#!/usr/bin/env python3
"""Validate per-scene capture outputs before render.

Walks the capture spec and checks every output:

    - tour MP4: file exists, ffprobe-readable, duration within ±20% of
      expected, no all-black run >2s at start or end
    - scene PNG: PNG header valid, file size ≥ 5 KB, dimensions ≥ 200x200
      (Pillow if available)

Borderline cases get `needs_visual_check: true` and Claude reads the asset
(PNG via Read, MP4 by sampling stills) to confirm it actually shows what the
scene's tour_action.steps / screenshot_action.steps was meant to capture.

Output:
    capture_validation_report.json with per-asset records and a top-level
    `gate_passed` boolean. Render does not run until gate_passed is true.

Usage:
    python validate_capture.py \\
        --spec capture_spec.json \\
        --output capture_validation_report.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DURATION_TOLERANCE = 0.20  # ±20%
MIN_PNG_BYTES = 5 * 1024
MIN_PNG_W = 200
MIN_PNG_H = 200
BLACK_LUMA_THRESHOLD = 12  # 0-255

try:
    from PIL import Image  # type: ignore
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ---------------------------------------------------------------------------
# tour MP4 checks
# ---------------------------------------------------------------------------
def ffprobe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def detect_black_runs(path: Path) -> dict:
    """Use ffmpeg blackdetect filter to find runs of dark frames.

    Returns {'has_long_black_run': bool, 'runs': [...]}.
    """
    if not shutil.which("ffmpeg"):
        return {"has_long_black_run": False, "runs": [], "skipped": True}
    cmd = [
        "ffmpeg", "-i", str(path),
        "-vf", f"blackdetect=d=2.0:pix_th={BLACK_LUMA_THRESHOLD/255:.3f}",
        "-an", "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return {"has_long_black_run": False, "runs": [], "skipped": True}
    runs = []
    for line in (result.stderr or "").split("\n"):
        if "blackdetect" in line and "black_start" in line:
            runs.append(line.strip())
    return {"has_long_black_run": len(runs) > 0, "runs": runs, "skipped": False}


def check_tour(entry: dict) -> dict:
    out_path = Path(entry["output_path"])
    record: dict = {
        "scene_id": entry["scene_id"],
        "type": "tour",
        "path": str(out_path),
        "exists": out_path.exists(),
        "size_bytes": 0,
        "duration_sec": None,
        "expected_duration_sec": entry.get("expected_duration_sec"),
        "duration_in_tolerance": False,
        "black_runs": [],
        "needs_visual_check": False,
        "severity": "pass",
        "issues": [],
    }
    if not record["exists"]:
        record["severity"] = "block"
        record["issues"].append("MP4 missing")
        return record
    record["size_bytes"] = out_path.stat().st_size
    if record["size_bytes"] < 50_000:
        record["severity"] = "block"
        record["issues"].append(f"file size {record['size_bytes']} bytes — likely empty/broken")
        return record

    dur = ffprobe_duration(out_path)
    record["duration_sec"] = dur
    if dur is None:
        record["severity"] = "review"
        record["needs_visual_check"] = True
        record["issues"].append("ffprobe could not read duration — Claude should sample stills")
    else:
        expected = float(record["expected_duration_sec"] or 8.0)
        low = expected * (1 - DURATION_TOLERANCE)
        high = expected * (1 + DURATION_TOLERANCE)
        if dur < low or dur > high:
            record["severity"] = "review"
            record["needs_visual_check"] = True
            record["issues"].append(
                f"duration {dur:.1f}s outside ±{int(DURATION_TOLERANCE*100)}% of expected {expected:.1f}s"
            )
        else:
            record["duration_in_tolerance"] = True

    black = detect_black_runs(out_path)
    if not black.get("skipped"):
        record["black_runs"] = black["runs"]
        if black["has_long_black_run"]:
            record["severity"] = "block"
            record["issues"].append(
                f">2s black-frame run detected — {len(black['runs'])} occurrence(s); likely a load failure or auth bounce"
            )
    return record


# ---------------------------------------------------------------------------
# scene PNG checks
# ---------------------------------------------------------------------------
def check_screenshot(entry: dict) -> dict:
    out_path = Path(entry["output_path"])
    record: dict = {
        "scene_id": entry["scene_id"],
        "type": "screenshot",
        "path": str(out_path),
        "exists": out_path.exists(),
        "size_bytes": 0,
        "png_signature_ok": False,
        "dimensions": None,
        "needs_visual_check": False,
        "severity": "pass",
        "issues": [],
    }
    if not record["exists"]:
        record["severity"] = "block"
        record["issues"].append("PNG missing")
        return record
    record["size_bytes"] = out_path.stat().st_size
    if record["size_bytes"] == 0:
        record["severity"] = "block"
        record["issues"].append("zero bytes")
        return record
    try:
        with out_path.open("rb") as fp:
            header = fp.read(8)
        if header == PNG_SIGNATURE:
            record["png_signature_ok"] = True
        else:
            record["severity"] = "block"
            record["issues"].append(f"not a valid PNG (header={header!r})")
            return record
    except OSError as e:
        record["severity"] = "block"
        record["issues"].append(f"cannot read: {e}")
        return record
    if record["size_bytes"] < MIN_PNG_BYTES:
        record["severity"] = "block"
        record["issues"].append(
            f"size {record['size_bytes']} bytes < min {MIN_PNG_BYTES} (likely placeholder or error page)"
        )
        return record
    if PILLOW_AVAILABLE:
        try:
            with Image.open(out_path) as img:
                w, h = img.size
                record["dimensions"] = {"width": w, "height": h}
                if w < MIN_PNG_W or h < MIN_PNG_H:
                    record["severity"] = "block"
                    record["issues"].append(f"dimensions {w}x{h} below {MIN_PNG_W}x{MIN_PNG_H}")
                    return record
                # Borderline aspect (very short page = often error)
                aspect = h / max(1, w)
                if aspect < 0.3:
                    record["severity"] = "review"
                    record["needs_visual_check"] = True
                    record["issues"].append(
                        f"unusually short page (aspect {aspect:.2f}) — may be a one-line error page"
                    )
        except Exception as e:
            record["severity"] = "block"
            record["issues"].append(f"PIL decode failed: {e}")
            return record
    else:
        record["severity"] = "review"
        record["needs_visual_check"] = True
        record["issues"].append(
            "Pillow not installed — Claude should read PNG and confirm it shows the intended UI state"
        )

    # Always flag captures with steps that include `highlight` or `hover` for
    # a visual sanity check — these are scenes where the intent is "show this
    # specific element" and only Claude can confirm the right element ended up
    # in frame.
    if record["severity"] == "pass":
        record["needs_visual_check"] = True
        record["severity"] = "review"
        record["issues"].append(
            "automated checks pass; Claude should still confirm the captured frame "
            "matches the scene's narration (correct UI state, right element highlighted)"
        )
    return record


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Validate per-scene capture outputs")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())
    entries = spec.get("entries", [])

    results: list[dict] = []
    for entry in entries:
        if entry["type"] == "tour":
            results.append(check_tour(entry))
        elif entry["type"] == "screenshot":
            results.append(check_screenshot(entry))

    blocks = [r for r in results if r["severity"] == "block"]
    reviews = [r for r in results if r["severity"] == "review"]
    passes = [r for r in results if r["severity"] == "pass"]

    report = {
        "summary": {
            "total": len(results),
            "passed": len(passes),
            "needs_visual_check": len(reviews),
            "blocked": len(blocks),
            "ffprobe_available": shutil.which("ffprobe") is not None,
            "ffmpeg_available": shutil.which("ffmpeg") is not None,
            "pillow_available": PILLOW_AVAILABLE,
        },
        "gate_passed": len(blocks) == 0,
        "_gate_passed_note": (
            "gate_passed reflects automated checks only. For every result with "
            "needs_visual_check=true, Claude must read the asset (PNG via Read, "
            "MP4 via ffmpeg-sampled stills) and confirm it shows what the scene's "
            "tour_action.steps / screenshot_action.steps was meant to capture. If "
            "any visual review fails, set gate_passed=false and re-run "
            "run_capture_pass.py --only <scene_id> to redo just the broken scenes."
        ),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    print(
        f"\nCapture validation: {len(passes)} pass · {len(reviews)} review · {len(blocks)} BLOCK",
        file=sys.stderr,
    )
    if blocks:
        print("\nBLOCKED:", file=sys.stderr)
        for b in blocks:
            print(f"  ✗ {b['scene_id']} ({b['type']}): {'; '.join(b['issues'])}", file=sys.stderr)
    if reviews:
        print("\nNeeds visual check (Claude reads via Read tool):", file=sys.stderr)
        for r in reviews:
            print(f"  ? {r['scene_id']} ({r['type']}): {'; '.join(r['issues'])}", file=sys.stderr)
    print(f"\nReport: {args.output}", file=sys.stderr)
    print(f"gate_passed: {report['gate_passed']}", file=sys.stderr)
    sys.exit(0 if report["gate_passed"] else 1)


if __name__ == "__main__":
    main()

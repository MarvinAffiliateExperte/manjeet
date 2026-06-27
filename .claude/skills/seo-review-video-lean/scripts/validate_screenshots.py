#!/usr/bin/env python3
"""Captured-screenshot validation — flag 404s and broken images before render.

Runs cheap automated checks on every PNG in the screenshot directories:

    - File exists and is non-empty
    - Valid PNG signature (89 50 4E 47 0D 0A 1A 0A)
    - File size >= --min-bytes (default 5 KB — anything smaller is almost
      certainly a 1x1 placeholder or an error page)
    - Image dimensions >= --min-width x --min-height (default 200x200)
      (only checked if Pillow is installed; otherwise skipped with a note)

Each PNG ends up tagged one of:

    pass    — all automated checks green, no visual review needed
    review  — automated checks passed but result is borderline (small but
              valid, unusual aspect, etc). Marked needs_visual_check: true so
              Claude can read the PNG via the Read tool and confirm it's not
              a 404, suspended-account, captcha, or "site unavailable" page.
    block   — automated checks failed; this screenshot CANNOT be used in the
              video. Either re-capture or drop the URL from the script.

Output:
    validation_report.json with per-screenshot results plus a top-level
    `gate_passed` boolean. The script-writing step in SKILL.md is gated on
    gate_passed: true.

Usage:
    python validate_screenshots.py \\
        --reddit-dir screenshots/reddit \\
        --product-dir screenshots/product \\
        --output screenshots/validation_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

try:
    from PIL import Image  # type: ignore
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def check_one(path: Path, min_bytes: int, min_w: int, min_h: int) -> dict:
    """Return a single-screenshot validation record."""
    record: dict = {
        "path": str(path),
        "filename": path.name,
        "exists": path.exists(),
        "size_bytes": 0,
        "png_signature_ok": False,
        "dimensions": None,
        "needs_visual_check": False,
        "severity": "pass",
        "issues": [],
    }

    if not record["exists"]:
        record["severity"] = "block"
        record["issues"].append("file missing")
        return record

    record["size_bytes"] = path.stat().st_size

    if record["size_bytes"] == 0:
        record["severity"] = "block"
        record["issues"].append("file is zero bytes")
        return record

    # PNG signature check (cheap, no decode)
    try:
        with path.open("rb") as fp:
            header = fp.read(8)
        if header == PNG_SIGNATURE:
            record["png_signature_ok"] = True
        else:
            record["severity"] = "block"
            record["issues"].append(f"not a valid PNG (header={header!r})")
            return record
    except OSError as e:
        record["severity"] = "block"
        record["issues"].append(f"cannot read file: {e}")
        return record

    # Size threshold
    if record["size_bytes"] < min_bytes:
        record["severity"] = "block"
        record["issues"].append(
            f"file size {record['size_bytes']} bytes < min {min_bytes} (likely "
            "a placeholder or error page)"
        )
        return record

    # Dimensions (Pillow only)
    if PILLOW_AVAILABLE:
        try:
            with Image.open(path) as img:
                w, h = img.size
                record["dimensions"] = {"width": w, "height": h}
                if w < min_w or h < min_h:
                    record["severity"] = "block"
                    record["issues"].append(
                        f"dimensions {w}x{h} below threshold {min_w}x{min_h}"
                    )
                    return record
                # Borderline cases — still pass automated, but ask Claude to look
                if w * h < (min_w * min_h * 4):
                    record["severity"] = "review"
                    record["needs_visual_check"] = True
                    record["issues"].append(
                        "image is small for a normal product/reddit screenshot — "
                        "Claude should visually confirm it isn't a 404 / error page"
                    )
                # Unusually tall/short pages can be 404s too
                aspect = h / max(1, w)
                if aspect < 0.3:
                    record["severity"] = "review"
                    record["needs_visual_check"] = True
                    record["issues"].append(
                        f"unusually short page (aspect {aspect:.2f}) — "
                        "may be a single-line error page"
                    )
        except Exception as e:  # pragma: no cover — Pillow can throw various
            record["severity"] = "block"
            record["issues"].append(f"PIL could not decode: {e}")
            return record
    else:
        # No Pillow — flag for visual check by default since we can't measure
        record["severity"] = "review"
        record["needs_visual_check"] = True
        record["issues"].append(
            "Pillow not installed — automated dimension check skipped. Claude "
            "should read the PNG via the Read tool and confirm it isn't a 404 "
            "/ broken page."
        )

    return record


def walk_dir(directory: Path, min_bytes: int, min_w: int, min_h: int) -> list[dict]:
    if not directory.exists():
        return []
    results = []
    for png in sorted(directory.glob("*.png")):
        results.append(check_one(png, min_bytes, min_w, min_h))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate captured screenshots")
    parser.add_argument("--reddit-dir", type=Path, required=True)
    parser.add_argument("--product-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=5 * 1024,
        help="Minimum acceptable PNG file size (default 5 KB)",
    )
    parser.add_argument("--min-width", type=int, default=200)
    parser.add_argument("--min-height", type=int, default=200)
    args = parser.parse_args()

    reddit_results = walk_dir(args.reddit_dir, args.min_bytes, args.min_width, args.min_height)
    product_results = walk_dir(args.product_dir, args.min_bytes, args.min_width, args.min_height)

    blocks = [r for r in reddit_results + product_results if r["severity"] == "block"]
    reviews = [r for r in reddit_results + product_results if r["severity"] == "review"]
    passes = [r for r in reddit_results + product_results if r["severity"] == "pass"]

    report = {
        "summary": {
            "reddit_total": len(reddit_results),
            "product_total": len(product_results),
            "passed": len(passes),
            "needs_visual_check": len(reviews),
            "blocked": len(blocks),
            "pillow_available": PILLOW_AVAILABLE,
        },
        "gate_passed": len(blocks) == 0,
        "_gate_passed_note": (
            "gate_passed only reflects automated checks. If the script reports "
            "needs_visual_check items, Claude must read each flagged PNG via "
            "the Read tool, visually confirm it is not a 404 / suspended / "
            "captcha / 'site unavailable' page, and re-set gate_passed to "
            "false on this report if any visual review fails."
        ),
        "reddit": reddit_results,
        "product": product_results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    # Stderr summary so humans (and Claude) can see at a glance
    print(
        f"\nScreenshot validation: "
        f"{len(passes)} pass · {len(reviews)} review · {len(blocks)} BLOCK",
        file=sys.stderr,
    )
    if blocks:
        print("\nBLOCKED screenshots:", file=sys.stderr)
        for b in blocks:
            print(f"  ✗ {b['filename']}: {'; '.join(b['issues'])}", file=sys.stderr)
    if reviews:
        print("\nNeeds visual check (Claude reads via Read tool):", file=sys.stderr)
        for r in reviews:
            print(f"  ? {r['filename']}: {'; '.join(r['issues'])}", file=sys.stderr)
    print(f"\nReport: {args.output}", file=sys.stderr)
    print(f"gate_passed: {report['gate_passed']}", file=sys.stderr)

    sys.exit(0 if report["gate_passed"] else 1)


if __name__ == "__main__":
    main()

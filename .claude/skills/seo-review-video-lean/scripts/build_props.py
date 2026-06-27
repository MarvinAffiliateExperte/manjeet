#!/usr/bin/env python3
"""Build props.json for the SEO review video pipeline.

Expected inputs in working dir:
  script.json          — scene definitions (with section metadata)
  tts/                 — generated WAV files (one per scene)
  remotion/public/tts/             — same WAVs staged for Remotion staticFile()
  remotion/public/reddit/          — reddit thread screenshots (Bucket Reddit)
  remotion/public/screenshots/     — Bucket A product screenshots (homepage etc.)
  remotion/public/screenshots-scene/ — per-scene UI-state PNGs (script-driven, named {scene_id}.png)
  remotion/public/broll/           — generic scroll recordings (public)
  remotion/public/tour/            — per-scene authenticated tour recordings (script-driven, named {scene_id}.mp4)

For each scene, reads WAV duration via ffprobe and computes durationInFrames.

In v3, capture is script-driven: every `tour-full` scene's MP4 lives at
remotion/public/tour/{scene_id}.mp4 (output of run_capture_pass.py), and every
scene whose script declared a `screenshot_action` has its PNG at
remotion/public/screenshots-scene/{scene_id}.png. This script auto-discovers
those per-scene assets without needing the older `tour` / `tour_start` /
`tour_end` fields. Older v1/v2 fields are still honored if present, for
backward compatibility.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

FPS = 30
TAIL_PADDING_SEC = 0.35

WORKDIR = Path.cwd()
SCRIPT = WORKDIR / "script.json"
TTS = WORKDIR / "tts"
OUT = WORKDIR / "remotion" / "props.json"
PUBLIC = WORKDIR / "remotion" / "public"

PUBLIC_TOUR_DIR = PUBLIC / "tour"
PUBLIC_SCENE_PNG_DIR = PUBLIC / "screenshots-scene"


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def main():
    raw = json.loads(SCRIPT.read_text())
    scenes_in = raw["scenes"] if isinstance(raw, dict) and "scenes" in raw else raw

    scenes_out = []
    total_frames = 0
    section_counts = {}
    auto_tour_count = 0
    auto_scene_png_count = 0
    missing_tour_warnings = []
    missing_scene_png_warnings = []

    for s in scenes_in:
        sid = s["id"]
        wav = TTS / f"{sid}.wav"
        if not wav.exists():
            print(f"WARN: missing {wav}", file=sys.stderr)
            continue
        dur = probe_duration(wav)
        frames = math.ceil((dur + TAIL_PADDING_SEC) * FPS)
        total_frames += frames

        scene = {
            "id": sid,
            "layout": s["layout"],
            "audio": f"tts/{sid}.wav",
            "durationInFrames": frames,
            "titleCard": s["title_card"],
        }

        # Track section for verification
        section = s.get("section", 0)
        section_counts[section] = section_counts.get(section, 0) + 1

        if s.get("subtitle"):
            scene["subtitle"] = s["subtitle"]
        if s.get("bullets"):
            scene["bullets"] = s["bullets"]
        if s.get("broll"):
            scene["broll"] = f"broll/{s['broll']}"

        # Testimonial pull (kept under `reddit` key for backward compat —
        # but `source` carries the origin: reddit | trustpilot | capterra | producthunt)
        if s.get("reddit"):
            r = s["reddit"]
            clean = {
                "image": f"reddit/{r['image']}",
                "quote": r.get("quote"),
                "author": r.get("author"),
                "upvotes": r.get("upvotes"),
                "subreddit": r.get("subreddit"),
                "source": r.get("source", "reddit"),
            }
            scene["reddit"] = {k: v for k, v in clean.items() if v is not None}

        # ---------- screenshot wiring (auto-discovery + backward compat) ----------
        # Script-driven (lean v2 / full v3+): if script declared screenshot_action,
        # look for the per-scene PNG at remotion/public/screenshots-scene/{scene_id}.png.
        # Multi-shot: if script declared screenshot_actions[] (plural — used by
        # screenshot-burst layouts), discover all matching files at
        # remotion/public/screenshots-scene/{scene_id}-*.png and wire them as a list.
        explicit_screenshot = s.get("screenshot")
        if s.get("screenshot_action"):
            scene_png = PUBLIC_SCENE_PNG_DIR / f"{sid}.png"
            if scene_png.exists():
                scene["screenshot"] = f"screenshots-scene/{sid}.png"
                auto_scene_png_count += 1
            elif explicit_screenshot:
                scene["screenshot"] = f"screenshots/{explicit_screenshot}"
            else:
                missing_scene_png_warnings.append(sid)
                if explicit_screenshot is not None:
                    scene["screenshot"] = f"screenshots/{explicit_screenshot}"
        elif explicit_screenshot:
            # Legacy: explicit screenshot field from older script schemas
            scene["screenshot"] = f"screenshots/{explicit_screenshot}"

        # Multi-shot wiring for screenshot-burst layouts (lean v2)
        multi_actions = s.get("screenshot_actions")
        if multi_actions:
            burst_files = sorted(PUBLIC_SCENE_PNG_DIR.glob(f"{sid}-*.png"))
            if burst_files:
                scene["screenshots"] = [f"screenshots-scene/{p.name}" for p in burst_files]
                auto_scene_png_count += len(burst_files)
                if len(burst_files) < len(multi_actions):
                    missing_scene_png_warnings.append(
                        f"{sid} (only {len(burst_files)}/{len(multi_actions)} burst shots)"
                    )
            else:
                missing_scene_png_warnings.append(sid + " (burst)")
        elif s.get("screenshots"):
            # Legacy: explicit screenshots[] field from older script schemas
            scene["screenshots"] = [f"screenshots/{x}" for x in s["screenshots"]]

        # ---------- tour wiring (auto-discovery + backward compat) ----------
        # Script-driven (v3): if scene declared tour_action, look for the
        # per-scene MP4 at remotion/public/tour/{scene_id}.mp4.
        if s.get("tour_action") or s.get("layout") == "tour-full":
            scene_mp4 = PUBLIC_TOUR_DIR / f"{sid}.mp4"
            if scene_mp4.exists():
                scene["tour"] = f"tour/{sid}.mp4"
                auto_tour_count += 1
            elif s.get("tour"):
                scene["tour"] = f"tour/{s['tour']}"
                if s.get("tour_start") is not None:
                    scene["tourStart"] = s["tour_start"]
                if s.get("tour_end") is not None:
                    scene["tourEnd"] = s["tour_end"]
            else:
                missing_tour_warnings.append(sid)
        elif s.get("tour"):
            # Legacy: explicit tour field from older script schemas
            scene["tour"] = f"tour/{s['tour']}"
            if s.get("tour_start") is not None:
                scene["tourStart"] = s["tour_start"]
            if s.get("tour_end") is not None:
                scene["tourEnd"] = s["tour_end"]

        scenes_out.append(scene)
        print(f"{sid}: {dur:5.2f}s → {frames:4d}f  [§{section} {s['layout']}]")

    props = {"scenes": scenes_out}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(props, indent=2))

    total_sec = total_frames / FPS
    print(f"\nTotal: {total_frames} frames = {total_sec:.1f}s ({total_sec / 60:.1f} min)")
    print(f"Sections covered: {sorted(section_counts.keys())}")
    for sec, count in sorted(section_counts.items()):
        print(f"  §{sec}: {count} scenes")

    print(f"\nAuto-wired per-scene assets:")
    print(f"  tour MP4s : {auto_tour_count}")
    print(f"  scene PNGs: {auto_scene_png_count}")

    if missing_tour_warnings:
        print(
            f"\nWARNING: {len(missing_tour_warnings)} scene(s) declared tour_action / "
            f"layout=tour-full but have no per-scene MP4 at {PUBLIC_TOUR_DIR}/<id>.mp4 — "
            f"render will fail unless you re-run run_capture_pass.py: {missing_tour_warnings}",
            file=sys.stderr,
        )
    if missing_scene_png_warnings:
        print(
            f"\nWARNING: {len(missing_scene_png_warnings)} scene(s) declared screenshot_action "
            f"but have no per-scene PNG at {PUBLIC_SCENE_PNG_DIR}/<id>.png — "
            f"re-run run_capture_pass.py: {missing_scene_png_warnings}",
            file=sys.stderr,
        )

    # Warn if any section has < 2 scenes
    for sec in range(1, 13):
        if section_counts.get(sec, 0) < 2:
            print(f"  WARNING: §{sec} has < 2 scenes!", file=sys.stderr)

    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

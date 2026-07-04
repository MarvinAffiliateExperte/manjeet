"""
Lean Product Review Video — Main Pipeline Orchestrator
Product: kurs-erfahrungen.com
Output:  output/review_kurs-erfahrungen.mp4  (~4–5 min, 1920×1080, H.264/AAC)

Steps:
  1. reddit_fetch  — collect Reddit testimonials → assets/reddit_quotes.json
  2. render_slides — render HTML templates → PNG  (requires Playwright)
  3. capture       — capture live screenshots + scroll videos (requires Playwright + site access)
  4. tts           — generate German VO via OpenRouter TTS  (requires OPENROUTER_API_KEY)
  5. assemble      — concat clips + audio → final MP4  (requires FFmpeg)

Usage:
    export OPENROUTER_API_KEY="sk-or-..."
    cd video/
    python pipeline.py [--skip-capture] [--skip-tts] [--skip-reddit]

Flags:
    --skip-capture   skip Playwright live-site capture (use existing assets/)
    --skip-tts       skip TTS generation (use existing assets/audio/)
    --skip-reddit    skip Reddit fetch (use existing assets/reddit_quotes.json)
    --only-assemble  jump straight to FFmpeg assembly
"""

import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
SKIP_CAPTURE = "--skip-capture" in sys.argv
SKIP_TTS = "--skip-tts" in sys.argv
SKIP_REDDIT = "--skip-reddit" in sys.argv
ONLY_ASSEMBLE = "--only-assemble" in sys.argv


def run_step(label: str, cmd: list[str]):
    print(f"\n{'='*60}")
    print(f"  STEP: {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n[error] Step '{label}' failed (exit {result.returncode}). Check output above.")
        sys.exit(result.returncode)


def main():
    # ensure we're in the video/ directory
    video_dir = Path(__file__).parent
    import os; os.chdir(video_dir)

    if ONLY_ASSEMBLE:
        run_step("Assemble final video", [PYTHON, "assemble.py"])
        return

    if not SKIP_REDDIT:
        run_step("Fetch Reddit testimonials", [PYTHON, "reddit_fetch.py"])

    if not SKIP_CAPTURE:
        run_step("Render slide PNGs", [PYTHON, "render_slides.py"])
        run_step("Capture live screenshots + scroll videos", [PYTHON, "capture.py"])

    if not SKIP_TTS:
        run_step("Generate TTS audio (OpenRouter)", [PYTHON, "tts.py"])

    run_step("Assemble final video", [PYTHON, "assemble.py"])

    print("\n" + "="*60)
    print("  DONE — output/review_kurs-erfahrungen.mp4")
    print("="*60)


if __name__ == "__main__":
    main()

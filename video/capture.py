"""
Screenshot + scroll-video capture using Playwright (Chromium pre-installed).
Reads scenes.json and produces every asset declared under type=screenshot|scroll_video.

Usage:
    python capture.py [--scenes scenes.json]

Env:
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers  (pre-set in CCR environment)
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCENES_FILE = sys.argv[1] if len(sys.argv) > 1 else "scenes.json"


async def capture_screenshot(page, scene: dict):
    out = Path(scene["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    await page.goto(scene["url"], wait_until="networkidle", timeout=30000)
    if scene.get("scroll_to_px"):
        await page.evaluate(f"window.scrollTo(0, {scene['scroll_to_px']})")
        await page.wait_for_timeout(800)
    if scene.get("highlight_selector"):
        await page.locator(scene["highlight_selector"]).scroll_into_view_if_needed()
        await page.wait_for_timeout(400)
    await page.screenshot(path=str(out), full_page=False)
    print(f"  [screenshot] {out}")


async def capture_scroll_video(page, scene: dict):
    out = Path(scene["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = scene.get("scroll_duration_s", 8)
    direction = scene.get("scroll_direction", "down")

    await page.goto(scene["url"], wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(1000)

    frame_dir = Path(tempfile.mkdtemp(prefix="frames_"))
    fps = 10  # low fps → smaller files; FFmpeg will re-encode at 30fps
    total_frames = duration * fps
    vp = scene.get("viewport", {"width": 1920, "height": 1080})
    page_height = await page.evaluate("document.body.scrollHeight")
    max_scroll = max(0, page_height - vp["height"])

    for i in range(total_frames):
        progress = i / (total_frames - 1) if total_frames > 1 else 0
        if direction == "up":
            progress = 1 - progress
        scroll_y = int(progress * max_scroll)
        await page.evaluate(f"window.scrollTo(0, {scroll_y})")
        frame_path = frame_dir / f"frame_{i:05d}.png"
        await page.screenshot(path=str(frame_path))

    # assemble frames → mp4 via FFmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frame_dir / "frame_%05d.png"),
        "-vf", f"scale={vp['width']}:{vp['height']},fps=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        str(out),
    ]
    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
    print(f"  [scroll_video] {out}")

    # cleanup frames
    for f in frame_dir.iterdir():
        f.unlink()
    frame_dir.rmdir()


async def main():
    from playwright.async_api import async_playwright

    config = json.loads(Path(SCENES_FILE).read_text())
    vp_default = {"width": 1920, "height": 1080}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=os.environ.get(
                "CHROMIUM_PATH",
                "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
            ),
            headless=True,
        )

        for scene in config["scenes"]:
            stype = scene.get("type")
            if stype not in ("screenshot", "scroll_video"):
                continue

            vp = scene.get("viewport", vp_default)
            ctx = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                device_scale_factor=1,
            )
            page = await ctx.new_page()

            try:
                print(f"[{scene['id']}] {scene['label']}")
                if stype == "screenshot":
                    await capture_screenshot(page, scene)
                elif stype == "scroll_video":
                    await capture_scroll_video(page, scene)
            except Exception as exc:
                print(f"  [error] {exc}")
            finally:
                await ctx.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

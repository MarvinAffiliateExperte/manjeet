#!/usr/bin/env python3
"""Playwright screenshot tool — captures Reddit threads and product pages.

Replaces the old firecrawl_screenshot.py. No third-party API needed; uses
locally-installed Playwright + Chromium.

Two modes:
  reddit   : screenshots each Reddit thread URL (full-page, dismisses overlays)
  product  : screenshots product pages at desktop viewport (homepage, features, pricing)

Both modes also support video capture by passing --video MP4 path. When --video is set
the script records a smooth top-to-bottom scroll of the page instead of (or in addition
to) capturing a static screenshot.

Install once:
    pip install playwright
    playwright install chromium

Usage:
    python playwright_screenshot.py reddit reddit_threads.json screenshots/reddit
    python playwright_screenshot.py product urls.json screenshots/product
    python playwright_screenshot.py product urls.json screenshots/product --video broll/

Idempotent: skips URLs whose output already exists.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # graceful failure — surface install instructions
    print(
        "ERROR: playwright is not installed.\n"
        "  pip install playwright && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(2)


VIEWPORT = {"width": 1920, "height": 1080}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------
def dismiss_overlays(page) -> None:
    """Best-effort dismissal of cookie/login banners — never throw."""
    selectors = [
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('I agree')",
        "button:has-text('Got it')",
        "button:has-text('Close')",
        "button[aria-label='Close']",
        "button[aria-label='close']",
        "[data-testid='reddit-cookie-consent-banner'] button",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=400):
                el.click(timeout=400)
                page.wait_for_timeout(150)
        except Exception:
            continue


def smooth_scroll(page, total_seconds: float = 12.0, fps: int = 30) -> None:
    """Smooth scroll top-to-bottom over total_seconds. Used during video capture."""
    height = page.evaluate("document.body.scrollHeight")
    viewport_h = page.evaluate("window.innerHeight")
    distance = max(0, height - viewport_h)
    if distance <= 0:
        page.wait_for_timeout(int(total_seconds * 1000))
        return
    steps = int(total_seconds * fps)
    step_px = distance / steps
    delay_ms = int(1000 / fps)
    for i in range(steps):
        page.evaluate(f"window.scrollBy(0, {step_px})")
        page.wait_for_timeout(delay_ms)


# -----------------------------------------------------------------------------
# screenshot core
# -----------------------------------------------------------------------------
def screenshot_url(
    page,
    url: str,
    out_path: Path,
    full_page: bool = True,
    wait_ms: int = 2500,
) -> bool:
    """Navigate, dismiss overlays, screenshot. Returns True on success."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"  goto failed: {e}", file=sys.stderr)
        return False
    page.wait_for_timeout(wait_ms)
    dismiss_overlays(page)
    page.wait_for_timeout(400)
    try:
        page.screenshot(path=str(out_path), full_page=full_page)
    except Exception as e:
        print(f"  screenshot failed: {e}", file=sys.stderr)
        return False
    return True


def record_scroll_mp4(
    browser,
    url: str,
    mp4_path: Path,
    duration_sec: float = 12.0,
) -> bool:
    """Record a smooth scroll of the page as MP4 via Playwright's video API + ffmpeg.

    Playwright records WebM; we ffmpeg to MP4 for downstream compatibility.
    """
    tmp_dir = mp4_path.parent / f".pwvideo-{mp4_path.stem}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        viewport=VIEWPORT,
        user_agent=USER_AGENT,
        record_video_dir=str(tmp_dir),
        record_video_size=VIEWPORT,
    )
    page = context.new_page()
    success = False
    try:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"  goto failed during video: {e}", file=sys.stderr)
            return False
        page.wait_for_timeout(2000)
        dismiss_overlays(page)
        page.wait_for_timeout(400)
        smooth_scroll(page, total_seconds=duration_sec)
        page.wait_for_timeout(500)
        success = True
    finally:
        page.close()
        context.close()
    if not success:
        return False
    webm_files = list(tmp_dir.glob("*.webm"))
    if not webm_files:
        print("  no webm produced", file=sys.stderr)
        return False
    src = webm_files[0]
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        str(mp4_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
    except Exception as e:
        print(f"  ffmpeg conversion failed: {e}", file=sys.stderr)
        return False
    # cleanup
    try:
        for f in tmp_dir.glob("*"):
            f.unlink()
        tmp_dir.rmdir()
    except Exception:
        pass
    return True


# -----------------------------------------------------------------------------
# modes
# -----------------------------------------------------------------------------
def mode_reddit(input_path: Path, out_dir: Path, video_dir: Path | None = None) -> None:
    threads = json.loads(input_path.read_text())["threads"]
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT)
        page = context.new_page()
        for i, t in enumerate(threads, 1):
            slug = f"reddit-{i:02d}-{t['id']}.png"
            dest = out_dir / slug
            if dest.exists():
                print(f"[{i}/{len(threads)}] cached: {slug}")
                saved.append({**t, "screenshot": str(dest)})
                continue
            print(f"[{i}/{len(threads)}] {t['url'][:80]}")
            url = t["url"].replace("www.reddit.com", "old.reddit.com")
            ok = screenshot_url(page, url, dest, full_page=True, wait_ms=3500)
            if not ok:
                print("  fallback to www.reddit.com")
                ok = screenshot_url(page, t["url"], dest, full_page=True, wait_ms=4000)
            if ok:
                print(f"  saved → {dest}")
                saved.append({**t, "screenshot": str(dest)})
            else:
                print("  FAILED")
            time.sleep(0.5)
        page.close()
        context.close()
        browser.close()
    manifest = out_dir.parent / "reddit_manifest.json"
    manifest.write_text(json.dumps({"threads": saved}, indent=2))
    print(f"\nManifest: {manifest}  ({len(saved)} succeeded)")


def mode_product(
    input_path: Path,
    out_dir: Path,
    video_dir: Path | None = None,
    video_duration_sec: float = 12.0,
) -> None:
    urls = json.loads(input_path.read_text())["urls"]
    out_dir.mkdir(parents=True, exist_ok=True)
    if video_dir:
        video_dir.mkdir(parents=True, exist_ok=True)
    saved: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT)
        page = context.new_page()
        for i, u in enumerate(urls, 1):
            slug = u.get("slug") or f"product-{i:02d}"
            dest = out_dir / f"{slug}.png"
            entry: dict = {**u}
            if not dest.exists():
                print(f"[{i}/{len(urls)}] screenshot: {u['url']}")
                ok = screenshot_url(page, u["url"], dest, full_page=False, wait_ms=3000)
                if ok:
                    print(f"  saved → {dest}")
                    entry["screenshot"] = str(dest)
                else:
                    print("  FAILED screenshot")
            else:
                print(f"[{i}/{len(urls)}] cached screenshot: {slug}")
                entry["screenshot"] = str(dest)
            saved.append(entry)
            time.sleep(0.4)
        page.close()
        context.close()
        # video pass
        if video_dir:
            for i, u in enumerate(urls, 1):
                slug = u.get("slug") or f"product-{i:02d}"
                mp4 = video_dir / f"{slug}.mp4"
                if mp4.exists():
                    print(f"[video {i}/{len(urls)}] cached: {mp4.name}")
                    saved[i - 1]["video"] = str(mp4)
                    continue
                print(f"[video {i}/{len(urls)}] recording: {u['url']}")
                ok = record_scroll_mp4(browser, u["url"], mp4, video_duration_sec)
                if ok:
                    print(f"  saved → {mp4}")
                    saved[i - 1]["video"] = str(mp4)
                else:
                    print("  FAILED video")
        browser.close()
    manifest = out_dir.parent / "product_manifest.json"
    manifest.write_text(json.dumps({"urls": saved}, indent=2))
    print(f"\nManifest: {manifest}  ({len(saved)} entries)")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Playwright screenshot + scroll-video tool")
    parser.add_argument("mode", choices=["reddit", "product"])
    parser.add_argument("input_json", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument(
        "--video",
        type=Path,
        default=None,
        help="If set, also record scroll-video MP4s to this directory (product mode only)",
    )
    parser.add_argument(
        "--video-duration",
        type=float,
        default=12.0,
        help="Seconds per scroll-video (default 12)",
    )
    args = parser.parse_args()

    if args.mode == "reddit":
        mode_reddit(args.input_json, args.out_dir)
    else:
        mode_product(args.input_json, args.out_dir, args.video, args.video_duration)


if __name__ == "__main__":
    main()

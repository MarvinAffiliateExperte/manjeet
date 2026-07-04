"""
Render HTML slide templates → PNG screenshots at 1920×1080 using Playwright.
Reads scenes.json, processes type=slide scenes only.

Usage:
    python render_slides.py [--scenes scenes.json]
"""

import asyncio
import json
import os
import sys
from pathlib import Path

SCENES_FILE = sys.argv[1] if len(sys.argv) > 1 else "scenes.json"


async def main():
    from playwright.async_api import async_playwright

    config = json.loads(Path(SCENES_FILE).read_text())

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
            headless=True,
        )
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await ctx.new_page()

        for scene in config["scenes"]:
            if scene.get("type") != "slide":
                continue

            template = Path(scene["template"])
            if not template.exists():
                print(f"  [skip] template not found: {template}")
                continue

            out = Path(scene["output"])
            out.parent.mkdir(parents=True, exist_ok=True)

            abs_path = template.resolve().as_uri()
            await page.goto(abs_path)
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
            print(f"  [slide] {scene['id']} → {out}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

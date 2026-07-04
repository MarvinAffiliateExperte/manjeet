"""
Assemble the final review MP4 from per-scene assets + audio via FFmpeg.
Uses imageio-ffmpeg's bundled FFmpeg binary (no system FFmpeg needed).

Pipeline per scene:
  • scroll_video  → already an MP4 → trim/loop to scene duration, mix VO audio
  • screenshot/slide PNG → freeze-frame video at scene duration, mix VO audio

Final output: output/review_kurs-erfahrungen.mp4
  • 1920×1080, VP8/WebM (imageio-ffmpeg supports libvpx), 30fps
  • Background music ducked under VO (optional; set MUSIC_FILE env var)

Usage:
    python assemble.py [--scenes scenes.json] [--audio-dir assets/audio]
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg

SCENES_FILE = "scenes.json"
AUDIO_DIR = Path("assets/audio")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "review_kurs-erfahrungen.mp4"
MUSIC_FILE = os.environ.get("MUSIC_FILE", "")
RESOLUTION = "1920x1080"
FPS = 30

# use bundled ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(str(c) for c in cmd[:7])}{'...' if len(cmd) > 7 else ''}")
    return subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def png_to_video(png: Path, duration: float, audio: Path | None, out: Path):
    """Convert a still PNG to an MP4 clip with optional audio overlay."""
    filter_v = f"scale={RESOLUTION},fps={FPS}"
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-framerate", "1", "-i", png,
    ]
    if audio and audio.exists():
        cmd += ["-i", audio]
        cmd += [
            "-vf", filter_v,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            "-map", "0:v", "-map", "1:a",
            "-shortest", out,
        ]
    else:
        cmd += [
            "-vf", filter_v,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", "-t", str(duration), out,
        ]
    run(cmd)


def generate_placeholder_video(duration: float, audio: Path | None, out: Path, label: str = ""):
    """Generate a dark-background placeholder clip using a PIL image."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    img = Image.new("RGB", (1920, 1080), color=(15, 15, 26))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    except Exception:
        font = ImageFont.load_default()

    text = label or "kurs-erfahrungen.com"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((1920 - w) // 2, (1080 - h) // 2), text, fill=(255, 255, 255), font=font)

    tmp_png = out.parent / f"_placeholder_{out.stem}.png"
    img.save(str(tmp_png))
    png_to_video(tmp_png, duration, audio, out)
    tmp_png.unlink(missing_ok=True)


def trim_video(src: Path, duration: float, audio: Path | None, out: Path):
    """Trim/loop a scroll MP4 to exact duration and mix in VO audio."""
    cmd = [FFMPEG, "-y", "-stream_loop", "-1", "-i", src]
    if audio and audio.exists():
        cmd += ["-i", audio]
        cmd += [
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            "-map", "0:v", "-map", "1:a",
            "-shortest", out,
        ]
    else:
        cmd += [
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an", "-t", str(duration), out,
        ]
    run(cmd)


def concat_clips(clip_paths: list[Path], out: Path):
    list_file = out.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
    run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        out,
    ])
    list_file.unlink(missing_ok=True)


def main():
    config = json.loads(Path(SCENES_FILE).read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="assembly_"))

    clip_paths: list[Path] = []

    for i, scene in enumerate(config["scenes"]):
        sid = scene["id"]
        stype = scene.get("type")
        duration = float(
            scene.get("duration_s")
            or (scene.get("vo_end_s", 0) - scene.get("vo_start_s", 0))
            or scene.get("scroll_duration_s", 8)
        )
        audio_path = AUDIO_DIR / f"{sid}.mp3"
        clip_out = tmp_dir / f"clip_{i:03d}_{sid}.mp4"

        print(f"\n[{sid}] type={stype} duration={duration}s")

        asset = Path(scene["output"])

        if not asset.exists():
            print(f"  [placeholder] asset missing: {asset}")
            generate_placeholder_video(
                duration,
                audio_path if audio_path.exists() else None,
                clip_out,
                label=scene.get("label", sid),
            )
        elif stype in ("screenshot", "slide"):
            png_to_video(asset, duration, audio_path if audio_path.exists() else None, clip_out)
        elif stype == "scroll_video":
            trim_video(asset, duration, audio_path if audio_path.exists() else None, clip_out)
        else:
            print(f"  [skip] unknown type: {stype}")
            continue

        clip_paths.append(clip_out)

    if not clip_paths:
        sys.exit("No clips to assemble.")

    print(f"\nConcatenating {len(clip_paths)} clips → {OUTPUT_FILE}")
    concat_clips(clip_paths, OUTPUT_FILE)

    # cleanup
    for p in clip_paths:
        p.unlink(missing_ok=True)
    remaining = list(tmp_dir.iterdir())
    if not remaining:
        tmp_dir.rmdir()

    size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"\n✓ Final video: {OUTPUT_FILE}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()

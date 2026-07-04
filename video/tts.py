"""
Generate German voiceover audio via OpenRouter (tts-1 compatible endpoint).
Reads video/script.md, splits by scene, sends each segment to TTS, saves WAV per scene.

Env vars required:
    OPENROUTER_API_KEY   — your OpenRouter API key

Usage:
    python tts.py [--script script.md] [--model <model-id>]

OpenRouter TTS model used: openai/tts-1  (cheapest, good German quality)
Alternative: openai/tts-1-hd  (higher quality, ~2× cost)
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

SCRIPT_FILE = "script.md"
MODEL = "openai/tts-1"
VOICE = "nova"          # best German-quality voice in tts-1; alternatives: alloy, echo, fable, onyx, shimmer
OUTPUT_DIR = Path("assets/audio")
OPENROUTER_URL = "https://openrouter.ai/api/v1/audio/speech"

SCENE_PATTERN = re.compile(r"##\s+\[SCENE:\s*(\w+)\].*?\n(.*?)(?=##|\Z)", re.DOTALL)


def parse_script(path: str) -> list[tuple[str, str]]:
    """Returns [(scene_id, voiceover_text), ...]."""
    text = Path(path).read_text(encoding="utf-8")
    scenes = []
    for m in SCENE_PATTERN.finditer(text):
        scene_id = m.group(1)
        raw = m.group(2).strip()
        # strip markdown bold markers, timing annotations, blank lines
        clean_lines = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or re.match(r"^[\d:·–\-]+", line):
                continue
            line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)   # bold → plain
            line = re.sub(r"\*(.+?)\*", r"\1", line)        # italic → plain
            clean_lines.append(line)
        vo_text = " ".join(clean_lines).strip()
        if vo_text:
            scenes.append((scene_id, vo_text))
    return scenes


def synthesize(text: str, scene_id: str, api_key: str) -> Path:
    out = OUTPUT_DIR / f"{scene_id}.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps({
        "model": MODEL,
        "input": text,
        "voice": VOICE,
        "response_format": "mp3",
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kurs-erfahrungen.com",
            "X-Title": "Lean Review Video Pipeline",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out.write_bytes(resp.read())

    print(f"  [tts] {scene_id} → {out} ({out.stat().st_size // 1024} KB)")
    return out


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        sys.exit("Error: OPENROUTER_API_KEY env var not set.")

    script_file = SCRIPT_FILE
    for arg in sys.argv[1:]:
        if arg.startswith("--script="):
            script_file = arg.split("=", 1)[1]
        elif arg.startswith("--model="):
            global MODEL
            MODEL = arg.split("=", 1)[1]

    scenes = parse_script(script_file)
    print(f"Found {len(scenes)} scenes with voiceover text.")

    manifest = []
    for scene_id, text in scenes:
        print(f"[{scene_id}] {text[:60]}…")
        audio_path = synthesize(text, scene_id, api_key)
        manifest.append({"scene_id": scene_id, "audio": str(audio_path)})

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nAudio manifest → {manifest_path}")


if __name__ == "__main__":
    main()

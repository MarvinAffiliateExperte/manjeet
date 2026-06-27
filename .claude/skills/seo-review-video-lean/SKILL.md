---
name: seo-review-video-lean
description: |
  **Lean Product Review Video**: Produce a 4-5 min voiceover review MP4 in a polished pitch-deck aesthetic. Script-first screenshot capture — every product screenshot is declared per scene, eliminating mismatched visuals. Bookend homepage scroll MP4, Reddit-first testimonials, OpenRouter TTS (no ElevenLabs). ~5x cheaper and ~6x faster than a full 8-12 min review pipeline.
  MANDATORY TRIGGERS: lean review video, product review video, deck review, pitch deck review, fast review video, quick review, lean SEO review, seo review video lean, deck-style review, short review video, lean pipeline, review mp4, make a review video
---

# Lean Product Review Video

Produces **4-5 minute voiceover-led review MP4s** in a polished editorial pitch-deck aesthetic. Cream background, charcoal text, coral accent — one cohesive theme, no configuration needed.

**The core architectural rule**: product screenshots are script-driven. The script declares exactly what each screenshot scene needs via `screenshot_action`, and the capture pass takes those exact shots after the script is written. This eliminates the classic failure mode where pre-captured screenshots (FAQ, About, Support pages) end up on slides they don't belong on.

## What you get

- 15-20 slides mapping the 12 standard SEO review sections
- Bookend homepage scroll MP4 (used as background on title + CTA slides)
- 4 Reddit-first testimonials (Trustpilot/Capterra/Product Hunt fallback)
- Script-driven screenshots — every body slide captures exactly what the narration describes
- OpenRouter TTS voiceover (gpt-audio-mini, 13 voice options)
- 1920×1080 MP4 at 30fps H.264, rendered via Remotion
- One API key required: OpenRouter

## MANDATORY INPUTS — ask before running

1. **Keyword** — exact target keyword (e.g. "best AI writing tool for SEO")
2. **Product name + URL** — what are we reviewing, where's the homepage
3. **Voice** — default **onyx**; alternatives: alloy, nova, sage, echo, shimmer, fable, ballad, coral, verse, marin, cedar, ash
4. **Slide count** — default **15**, range 15-20

Four questions. No engine choice. No auth-state check. No URL list to vet upfront.

## Defaults

- Slide count: **15** (~14.5s per slide → ~3:37 final)
- TTS: OpenRouter `gpt-audio-mini`, voice = user-chosen (default onyx)
- Theme: **editorial** (cream/charcoal/coral) — only one theme
- Testimonials target: **4** mined; 2-3 used in deck
- Body screenshots: **6-8 script-driven captures** (one per non-title/non-stat slide)
- Bookend scroll MP4: **1** (homepage) — pre-captured
- Capture: 100% unauthenticated Playwright (no login required)
- Output: 1920×1080 MP4, 30fps, H.264

## Pipeline (13 steps)

Working directory: `/tmp/lean-review-{slug}/` (or wherever the session sandbox writes).

### 1. Lock inputs

Ask the four questions. Write to `config.json`. Don't proceed without all four.

### 2. Lean research — single Perplexity query

```bash
OPENROUTER_API_KEY=... python scripts/research_lean.py \
  --product "{product}" --url "{url}" --output research.json
```

Returns one JSON object: one-liner, top 3 features, pricing tiers, headline stat, standout pro, standout con, best alternative, ideal user, skip-if profile, recent update, citations.

### 3. Mine 4 testimonials (Reddit-first with fallbacks)

```bash
python scripts/mine_testimonials.py "{product}" 4 --domain {domain}
```

Reddit-first; falls back to Trustpilot → Capterra → Product Hunt. Output `reddit_threads.json` with `source` field per entry.

### 4. Screenshot testimonial pages (Playwright)

```bash
python scripts/playwright_screenshot.py reddit reddit_threads.json screenshots/reddit
```

Pre-script because testimonials are data input, not scene-specific.

### 5. Capture bookend homepage scroll MP4 only

Build a one-URL `product_urls.json`:

```json
{"urls": [
  {"url": "https://{domain}", "slug": "homepage", "label": "Homepage"}
]}
```

Then:

```bash
python scripts/playwright_screenshot.py product product_urls.json screenshots/product --video broll/
```

Produces `broll/homepage.mp4` (~12s). Body slides do NOT use upfront product captures — they're declared by the script in step 7.

### 6. Validate testimonial + bookend captures — HARD GATE

```bash
python scripts/validate_screenshots.py \
  --reddit-dir screenshots/reddit \
  --product-dir screenshots/product \
  --output screenshots/validation_report.json
```

PNG header + size + dimensions audit. Borderline cases get `needs_visual_check: true` — Claude reads each via the `Read` tool. Step 7 doesn't run until `gate_passed: true`.

### 7. Write the deck script — every product-screenshot scene declares `screenshot_action`

Use `templates/deck_template.md`. **15-20 slides** mapping the 12 SEO sections plus title + CTA bookends.

Any slide whose narration ties to a specific UI element, page section, hover state, scroll position, or value **declares a `screenshot_action`**:

```json
{
  "id": "scene-04",
  "section": 2,
  "section_name": "Key Features",
  "layout": "screenshot-burst",
  "narration": "Three features carry the product. The one-click article generator, the Real-Time Data integration, and the bulk export to WordPress.",
  "title_card": "THREE FEATURES THAT MATTER",
  "screenshot_actions": [
    {
      "url": "https://app.example.com/features/one-click",
      "steps": [{"do": "wait", "ms": 1500}, {"do": "highlight", "selector": "[data-test='generate-button']", "ms": 800}],
      "viewport_focus": "[data-test='generate-button']",
      "output_name": "one-click"
    }
  ]
}
```

#### Capture primitives supported in `steps`

| `do` | Args | What it does |
|---|---|---|
| `wait` | `ms` | Pause |
| `goto` | `url` | Navigate mid-action |
| `click` | `selector` | Click an element |
| `type` | `selector`, `text` | Focus and type |
| `hover` | `selector` | Hover |
| `highlight` | `selector`, `ms` | Inject CSS outline + glow |
| `scroll` | `selector` OR `pixels` | Scroll into view or by pixels |
| `key` | `combo` | Playwright key combo |
| `dismiss_overlay` | — | Cookie/banner dismissal |

#### Layouts and their screenshot needs

| Layout | Needs screenshot? | What kind |
|---|---|---|
| `title-card` | No (uses bookend MP4) | — |
| `product-full` | Yes — single `screenshot_action` | Exact UI state narration describes |
| `screenshot-burst` | Yes — `screenshot_actions` array (typically 3) | Three distinct UI states |
| `vs-card` | Optional | Comparison or stat visual |
| `stat-card` | Optional | Page where the stat is visible |
| `reddit-card` | Uses pre-captured testimonial PNG | n/a |

**SCRIPT APPROVAL GATE**: stop after writing `script.json` and show the section-by-section outline (each scene's `screenshot_action` URLs as a one-line summary) before any capture or audio runs.

### 8. Compile capture spec from the script

```bash
python scripts/compile_capture_spec.py \
  --script script.json \
  --output capture_spec.json
```

Walks `script.json`, extracts every `screenshot_action`, emits a unified Playwright runbook.

### 9. Run the script-driven screenshot capture pass

```bash
python scripts/run_capture_pass.py \
  --spec capture_spec.json \
  --output-manifest capture_manifest.json
```

ONE Playwright session, **no auth**. Walks the runbook, navigates to each URL, runs the declared steps, takes the screenshot. PNGs land at `screenshots/scene/{scene_id}.png`.

### 10. Validate captured product screenshots — HARD GATE

```bash
python scripts/validate_capture.py \
  --spec capture_spec.json \
  --output capture_validation_report.json
```

File exists, PNG header valid, size ≥ 5 KB, dimensions ≥ 200×200. Borderline cases: Claude reads each PNG via `Read` and confirms it shows what the scene's narration calls for. `gate_passed: true` required to render.

To re-run a single failed scene: `run_capture_pass.py --only scene-XX`

### 11. Generate voiceover (OpenRouter only)

```bash
OPENROUTER_API_KEY=... python scripts/tts.py batch \
  --voice {voice from config.json} \
  --scenes script.json --output-dir tts/
```

15-20 sequential SSE streams; ~3-5 min total. WAV at 24kHz / 16-bit / mono PCM.

### 12. Build props + render

```bash
cp tts/*.wav remotion/public/tts/
cp screenshots/reddit/*.png remotion/public/reddit/
cp screenshots/scene/*.png remotion/public/screenshots-scene/
cp broll/*.mp4 remotion/public/broll/

python scripts/build_props.py

TMPDIR=/tmp/remotion-{slug} nohup npx remotion render \
  SlideDeck out/review.mp4 --props=props.json --concurrency=3 --jpeg-quality=85 \
  > render.log 2>&1 &
```

### 13. Verify + deliver

- `ffprobe` — duration 3:30-5:00, audio stream present, mean_volume ≥ -20dB
- Sample 8-10 frames — cream bg, coral accent, serif headline, no FAQ on pricing slide
- Audio sanity — first 10s plays the chosen voice
- All 12 SEO sections represented; every `screenshot_action`-tagged scene has its PNG
- Copy final MP4 to the user's chosen output folder and share via link

## Voice options

onyx (default) · alloy · nova · sage · echo · shimmer · fable · ballad · coral · verse · marin · cedar · ash

## When to use this vs a full review pipeline

| Signal | This skill | Full 8-12 min pipeline |
|---|---|---|
| Publish today / iterate fast | ✓ | |
| Product is mainstream + well-documented | ✓ | |
| API budget is tight | ✓ | |
| Brand-anchored cloned voice | | ✓ |
| Tutorial intent / dashboard deep-dive | | ✓ |
| Multi-product comparison | | ✓ |
| Affiliate URL needs maximum trust signals | | ✓ |
| Dashboard requires login + interesting B-roll | | ✓ |

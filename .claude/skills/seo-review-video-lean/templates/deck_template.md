# Lean Deck Script Template (4-5 min, 15-20 slides)

The lean skill compresses the full 12-section SEO review structure into a deck-style flow that reads like a SaaS founder's pitch deck — each slide is one beat, narration runs ~12-18 seconds, motion is minimal. The bookend public scroll MP4 is the only moving asset; everything else is static screenshots with subtle Ken Burns.

**Base: 15 slides (4:00). Expand toward 20 slides (5:00) for products with deep pricing or extra testimonials.**

---

## Slide flow

| # | Beat | Layout | Sec | Maps to full §  |
|---|------|--------|-----|-----------------|
| 1 | **Title** — product name + tagline + reviewer credit | `title-card` | 12-15 | §1 |
| 2 | **Problem / category pain** — what category gap this product fills | `title-card` | 13-16 | §1 |
| 3 | **Product intro** — one-line description + homepage screenshot | `product-full` | 14-17 | §2 |
| 4 | **Key features** — 3-card grid of standout features | `screenshot-burst` | 16-18 | §2/§3 |
| 5 | **How it works** — 3-step ordered flow | `vs-card` | 14-17 | §4 |
| 6 | **Headline stat** — one impressive number with context | `stat-card` | 12-15 | §4 |
| 7 | **UX** — labeled product screenshot of the dashboard or main flow | `product-full` | 14-17 | §5 |
| 8 | **Vs alternative** — head-to-head against the obvious competitor | `vs-card` | 16-18 | §6 |
| 9 | **Pros** — 3-4 best things | `vs-card` | 14-17 | §7 |
| 10 | **Cons** — 1-2 honest limitations | `vs-card` | 14-17 | §7 |
| 11 | **Pricing** — headline tier + price + key inclusion | `stat-card` | 13-16 | §10 |
| 12 | **Testimonial 1** — pull-quote from Reddit / Trustpilot / Capterra / Product Hunt | `reddit-card` | 14-17 | §12 |
| 13 | **Testimonial 2** — second pull-quote (different source preferred) | `reddit-card` | 14-17 | §12 |
| 14 | **Verdict** — rating + clear yes/no/it-depends recommendation | `title-card` | 14-17 | §11 |
| 15 | **CTA** — link in description / handle / product URL | `title-card` | 13-16 | §12 |

**15 slides × ~14.5s = 217s ≈ 3:37.** That's short enough to feel snappy, long enough to land.

---

## Expansion to 20 slides

If the product warrants more (deep pricing tiers, lots of testimonials, complex feature set), insert any of these:

| # | Beat | Layout | When to add |
|---|------|--------|-------------|
| 4b | **Best for** — single-sentence ideal-user profile | `title-card` | Always useful — make it slide 4b for products with mass appeal |
| 7b | **Skip if** — single-sentence non-ideal profile | `title-card` | Pairs with "best for" |
| 11b | **Pricing tiers detail** — second stat-card with second tier | `stat-card` | Multi-tier products only |
| 13b | **Testimonial 3** — third pull-quote | `reddit-card` | When you have 6+ testimonials available |
| 13c | **Testimonial 4** — fourth pull-quote | `reddit-card` | Rare — only if all four are distinct |

**20 slides × ~14.5s = 290s ≈ 4:50.**

---

## Bookend public scroll MP4

The intro/outro scroll is captured ONCE — homepage scroll, ~12 seconds, public-page only (no auth). It's used as the **background B-roll** behind the title (scene 1) and the CTA (scene 15). Both bookends get motion; everything in between is static screenshot + Ken Burns. This is the only moving asset in the entire video, and it makes the deck feel polished without ballooning capture cost.

```bash
python scripts/playwright_screenshot.py product product_urls.json screenshots/product --video broll/
```

The script auto-detects the homepage URL (the `homepage` slug in `product_urls.json`) and produces `broll/homepage.mp4`. Use this MP4 as the `broll` field on scenes 1 and 15.

---

## Layout playbook

The lean skill reuses 6 of the 8 layouts from the full skill. Here's how to wield them:

**`title-card`** — full-bleed bg + giant headline + subtitle. The deck's workhorse. Used for title, problem, verdict, CTA, and any "best for / skip if" expansion slides.

**`product-full`** — single product screenshot full-frame with subtle Ken Burns + small label top-center. Used for product intro and UX deep-dive slides.

**`screenshot-burst`** — 3 product screenshots in rapid succession (or 3 thumbnails in a static grid for the deck aesthetic — the renderer handles both modes). Used for the "key features" slide.

**`vs-card`** — left-side bullet list + right-side media. Used for "how it works" (3 steps), "vs alternative", "pros", "cons". Prefix winning bullets with `★ `.

**`stat-card`** — giant number/stat left + supporting media right. Used for headline-stat and pricing slides.

**`reddit-card`** — testimonial screenshot left + source pill + pull-quote right. Used for the 2-4 testimonial slides. Source pill renders as "REDDIT" by default; the screenshot itself shows the actual source's branding visually (Trustpilot logo, Capterra logo, etc.).

**Layouts NOT used in the lean skill:**
- `big-label` — too punchy for the deck aesthetic
- `tour-full` — no authenticated tours in lean

---

## Script-driven capture rules (lean v2)

**Architectural rule:** body-of-deck product screenshots are NOT pre-captured. Every screenshot scene declares a `screenshot_action` (single PNG) or `screenshot_actions[]` (array, used by `screenshot-burst` for the 3-up grid). The capture pass takes those exact shots after the script is written. This is the v2 architectural fix that eliminates the v1-lean failure mode where pre-captured FAQ / About / Support screenshots ended up on slides they didn't belong on.

### When to declare what

| Layout | Required field | Notes |
|---|---|---|
| `title-card` | none (uses `broll` for slide 1 + final, none otherwise) | Conceptual / verdict / CTA slides |
| `product-full` | `screenshot_action` (single) | The exact UI state the narration calls for |
| `screenshot-burst` | `screenshot_actions` (array of 3) | Three distinct UI states / pages / features for the 3-up grid |
| `vs-card` | `screenshot_action` (optional, single) | If a comparison or stat visual goes on the right side |
| `stat-card` | `screenshot_action` (optional, single) | If the supporting media is a UI element rather than abstract |
| `reddit-card` | uses pre-captured testimonial PNG (step 4) | Driven by `reddit_threads.json`, NOT `screenshot_action` |

### Step primitives

| `do` | Args | What it does |
|---|---|---|
| `wait` | `ms` | Pause |
| `goto` | `url` | Navigate mid-action |
| `click` | `selector` | Click an element |
| `type` | `selector`, `text` | Focus and type |
| `hover` | `selector` | Hover |
| `highlight` | `selector`, `ms` | Inject CSS outline + glow for `ms` ms (visible in capture) |
| `scroll` | `selector` OR `pixels` | Scroll element into view, or scroll by pixels |
| `key` | `combo` | Playwright key combo (`"Meta+K"`, `"ArrowDown"`) |
| `dismiss_overlay` | — | Best-effort cookie/banner dismissal |

### Selector preference

1. `[data-test=...]` / `[data-testid=...]` — most stable, prefer these
2. `[aria-label=...]` — semantic
3. Descriptive CSS like `button.generate-btn`
4. Text-based via Playwright like `text=Generate` — last resort

### Simple "go to URL and shoot" pattern

For scenes where the narration just describes a page generally (no specific UI state to hit), a minimal `screenshot_action` is fine:

```json
"screenshot_action": {
  "url": "https://example.com/pricing",
  "steps": [{"do": "wait", "ms": 1500}]
}
```

### Output paths (auto-discovered by `build_props.py`)

| Action type | Output path | Auto-wired field on scene |
|---|---|---|
| `screenshot_action` (single) | `screenshots/scene/{scene_id}.png` | `scene.screenshot` |
| `screenshot_actions[]` (multi) | `screenshots/scene/{scene_id}-{output_name}.png` | `scene.screenshots[]` |

You don't write `screenshot:` or `screenshots:` fields in the script — `build_props.py` discovers them from the disk after capture.

---

## Script writing rules (lean adaptations)

1. **Hook in under 5 seconds** on slide 1 — same as the full skill.
2. **Every slide is anchored by visible text** — title card, label, or callout. Never just B-roll.
3. **Quote testimonials verbatim** — at least 2 across the deck (target 4 mined; pick the 2 best).
4. **Show, then tell** — visual appears 0.3-0.5s before narration.
5. **Narration runs ~12-18 seconds per slide** — longer than the full skill's 8-12s because the deck pace is slower and more contemplative. Read every line aloud; if you stumble, rewrite.
6. **No filler**: each slide has a single point. If you find yourself padding, cut the slide.
7. **Bookend with motion** — slide 1 and the final slide use the homepage scroll MP4 as background. Everything else is static.
8. **Numbers > adjectives** — same as the full skill. "$49/month" not "affordable", "73 templates" not "lots of templates".

---

## Example scene objects

```json
{
  "id": "scene-01",
  "section": 1,
  "section_name": "Title",
  "layout": "title-card",
  "narration": "Koala Writer says you can generate a full SEO article in one click. I tested fifty articles across twelve niches. Here's what holds up — and what doesn't.",
  "title_card": "KOALA WRITER",
  "subtitle": "An honest 4-minute deck",
  "broll": "homepage.mp4"
}
```

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
      "url": "https://app.koala.sh/new",
      "steps": [
        {"do": "wait", "ms": 1500},
        {"do": "highlight", "selector": "[data-test='generate-article']", "ms": 800}
      ],
      "viewport_focus": "[data-test='generate-article']",
      "output_name": "one-click"
    },
    {
      "url": "https://app.koala.sh/real-time",
      "steps": [
        {"do": "wait", "ms": 1500},
        {"do": "scroll", "selector": "[data-test='live-results']"}
      ],
      "viewport_focus": "[data-test='live-results']",
      "output_name": "real-time"
    },
    {
      "url": "https://app.koala.sh/export",
      "steps": [
        {"do": "wait", "ms": 1200},
        {"do": "click", "selector": "[data-test='wp-tab']"}
      ],
      "output_name": "wp-export"
    }
  ]
}
```

```json
{
  "id": "scene-12",
  "section": 12,
  "section_name": "Testimonial",
  "layout": "reddit-card",
  "narration": "Here's a Reddit user who's been using Koala for six months: 'It's the only AI writer I haven't cancelled. The articles need a 10-minute edit, but they rank.'",
  "title_card": "SIX-MONTH USER",
  "reddit": {
    "image": "reddit-04-koala_review.png",
    "quote": "It's the only AI writer I haven't cancelled. The articles need a 10-minute edit, but they rank.",
    "author": "u/seo_practitioner",
    "subreddit": "r/SEO",
    "source": "reddit",
    "upvotes": 142
  }
}
```

```json
{
  "id": "scene-15",
  "section": 12,
  "section_name": "CTA",
  "layout": "title-card",
  "narration": "Free trial link's in the description if you want to test it yourself. No card needed.",
  "title_card": "TRY IT — LINK IN DESCRIPTION",
  "subtitle": "Free trial · No card",
  "broll": "homepage.mp4"
}
```

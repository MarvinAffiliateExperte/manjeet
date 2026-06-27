#!/usr/bin/env python3
"""Mine testimonials from Reddit, with fallbacks for thin Reddit niches.

Tries Reddit first via mine_reddit.py. If fewer than `target` threads come
back, falls back to:

    1. Trustpilot     — best for established consumer/SaaS brands
    2. Capterra       — best for B2B SaaS reviews
    3. Product Hunt   — best for newer tools

Each non-Reddit testimonial is normalized to the same shape mine_reddit.py
emits, so playwright_screenshot.py reddit mode and build_props.py work
unchanged. A `source` field is added per entry to make the origin explicit
(values: "reddit", "trustpilot", "capterra", "producthunt").

Output (writes to reddit_threads.json by default to stay drop-in compatible):

    {
      "product": "Koala Writer",
      "target": 7,
      "by_source": {"reddit": 3, "trustpilot": 4, "capterra": 0, "producthunt": 0},
      "threads": [
        {"id": "...", "url": "...", "source": "reddit"|"trustpilot"|..., ...},
        ...
      ]
    }

Usage:
    python mine_testimonials.py "Koala Writer" 7
    python mine_testimonials.py "Koala Writer" 7 --domain koala.sh
    python mine_testimonials.py "Surfer SEO" 7 --output reddit_threads.json --skip-reddit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(
        "ERROR: playwright not installed. pip install playwright && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(2)


VIEWPORT = {"width": 1366, "height": 900}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
QUOTE_MAX = 180


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def hash_id(text: str, prefix: str) -> str:
    return f"{prefix}-{hashlib.sha1(text.encode()).hexdigest()[:8]}"


def trim_quote(body: str) -> str:
    body = body.strip().replace("\n", " ").replace("\r", " ")
    while "  " in body:
        body = body.replace("  ", " ")
    if len(body) <= QUOTE_MAX:
        return body
    parts = body.split(". ")
    out = ""
    for p in parts:
        if len(out) + len(p) + 2 > QUOTE_MAX:
            break
        out += p + ". "
    return (out.strip() or body[:QUOTE_MAX]).rstrip(".") + "…"


def stars_to_score(stars: float | None, default: int = 50) -> int:
    if stars is None:
        return default
    return int(round(float(stars) * 20))  # 5-star → 100-point


def normalize(
    *,
    source: str,
    body: str,
    author: str,
    url: str,
    title: str | None = None,
    stars: float | None = None,
) -> dict:
    """Return a thread dict in the same shape mine_reddit.py emits."""
    score = stars_to_score(stars)
    quote = trim_quote(body)
    return {
        "title": title or f"Review by {author}",
        "url": url,
        "subreddit": source,  # legacy field (renderer uses this for the pill label)
        "source": source,
        "upvotes": score,
        "num_comments": 0,
        "author": author or f"{source}_user",
        "top_comment": {
            "body": body,
            "quote": quote,
            "score": score,
            "author": author or f"{source}_user",
        },
        "id": hash_id(url + body[:50], source),
    }


# ---------------------------------------------------------------------------
# Trustpilot
# ---------------------------------------------------------------------------
def fetch_trustpilot(page, product: str, domain: str | None, n_needed: int) -> list[dict]:
    """Try Trustpilot reviews. Returns up to n_needed normalized testimonials."""
    print(f"  [trustpilot] fetching for '{product}' (need {n_needed})", file=sys.stderr)
    base = "https://www.trustpilot.com"
    if domain:
        target = f"{base}/review/{domain}"
    else:
        # search first
        try:
            page.goto(f"{base}/search?query={quote(product)}", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            link = page.locator("a[href*='/review/']").first
            href = link.get_attribute("href", timeout=5000)
            if not href:
                return []
            target = href if href.startswith("http") else base + href
        except Exception as e:
            print(f"    search failed: {e}", file=sys.stderr)
            return []
    try:
        page.goto(target, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"    goto failed: {e}", file=sys.stderr)
        return []
    page.wait_for_timeout(2000)

    results: list[dict] = []
    # Card selector — Trustpilot's data attribute is reasonably stable
    card_selectors = ["[data-service-review-card-paper]", "[data-review-content]", "article"]
    cards = []
    for sel in card_selectors:
        cards = page.locator(sel).all()
        if cards:
            break
    if not cards:
        print(f"    no review cards found on {target}", file=sys.stderr)
        return []

    for card in cards[: n_needed * 2]:
        try:
            body_locs = ["p[data-service-review-text-typography]", "[data-review-text]", "p"]
            body = ""
            for s in body_locs:
                try:
                    body = card.locator(s).first.text_content(timeout=1000) or ""
                    if len(body.strip()) > 30:
                        break
                except Exception:
                    continue
            if not body or len(body.strip()) < 30:
                continue
            try:
                author = (card.locator("[data-consumer-name-typography]").first.text_content(timeout=1000) or "").strip()
            except Exception:
                author = ""
            stars: float | None = None
            try:
                attr = card.locator("[data-service-review-rating]").first.get_attribute(
                    "data-service-review-rating", timeout=1000
                )
                if attr:
                    stars = float(attr)
            except Exception:
                pass
            review_url = page.url + "#" + hash_id(body, "tp")[:6]
            results.append(normalize(
                source="trustpilot",
                body=body.strip(),
                author=author or "Trustpilot reviewer",
                url=review_url,
                stars=stars,
            ))
            if len(results) >= n_needed:
                break
        except Exception:
            continue
    print(f"    got {len(results)} from Trustpilot", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Capterra
# ---------------------------------------------------------------------------
def fetch_capterra(page, product: str, n_needed: int) -> list[dict]:
    print(f"  [capterra] fetching for '{product}' (need {n_needed})", file=sys.stderr)
    base = "https://www.capterra.com"
    try:
        page.goto(f"{base}/search/?search={quote(product)}", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1800)
        # First product link
        prod_link = page.locator("a[href*='/p/']").first
        href = prod_link.get_attribute("href", timeout=5000)
        if not href:
            print("    no product found on Capterra search", file=sys.stderr)
            return []
        product_url = href if href.startswith("http") else base + href
        # Reviews page is /reviews relative to /p/<slug>
        if not product_url.rstrip("/").endswith("/reviews"):
            product_url = product_url.rstrip("/") + "/reviews"
        page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"    Capterra navigation failed: {e}", file=sys.stderr)
        return []
    page.wait_for_timeout(2000)

    results: list[dict] = []
    card_selectors = [
        "[data-testid='review-card']",
        ".review-card",
        "[id^='review-']",
        "section[itemprop='review']",
    ]
    cards = []
    for sel in card_selectors:
        cards = page.locator(sel).all()
        if cards:
            break
    if not cards:
        print("    no review cards found on Capterra", file=sys.stderr)
        return []

    for card in cards[: n_needed * 2]:
        try:
            body = ""
            for s in ["[data-testid='review-text']", "[itemprop='reviewBody']", "p"]:
                try:
                    body = card.locator(s).first.text_content(timeout=1000) or ""
                    if len(body.strip()) > 30:
                        break
                except Exception:
                    continue
            if len(body.strip()) < 30:
                continue
            author = ""
            for s in ["[data-testid='reviewer-name']", "[itemprop='author']", ".reviewer-name"]:
                try:
                    author = (card.locator(s).first.text_content(timeout=1000) or "").strip()
                    if author:
                        break
                except Exception:
                    continue
            stars: float | None = None
            try:
                rating = card.locator("[itemprop='ratingValue']").first.get_attribute("content", timeout=1000)
                if rating:
                    stars = float(rating)
            except Exception:
                pass
            review_url = page.url + "#" + hash_id(body, "cap")[:6]
            results.append(normalize(
                source="capterra",
                body=body.strip(),
                author=author or "Capterra reviewer",
                url=review_url,
                stars=stars,
            ))
            if len(results) >= n_needed:
                break
        except Exception:
            continue
    print(f"    got {len(results)} from Capterra", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Product Hunt
# ---------------------------------------------------------------------------
def fetch_producthunt(page, product: str, n_needed: int) -> list[dict]:
    print(f"  [producthunt] fetching for '{product}' (need {n_needed})", file=sys.stderr)
    base = "https://www.producthunt.com"
    try:
        page.goto(f"{base}/search?q={quote(product)}", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1800)
        prod_link = page.locator("a[href^='/products/']").first
        href = prod_link.get_attribute("href", timeout=5000)
        if not href:
            print("    no product found on Product Hunt", file=sys.stderr)
            return []
        product_url = href if href.startswith("http") else base + href
        # Reviews page
        reviews_url = product_url.rstrip("/") + "/reviews"
        page.goto(reviews_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"    Product Hunt navigation failed: {e}", file=sys.stderr)
        return []
    page.wait_for_timeout(2000)

    results: list[dict] = []
    card_selectors = [
        "[data-test^='review-']",
        "article[data-test*='review']",
        "div[data-sentry-component='ReviewCard']",
        "section",
    ]
    cards = []
    for sel in card_selectors:
        cards = page.locator(sel).all()
        if len(cards) >= 2:  # need at least 2 to be confident
            break
    if not cards:
        print("    no review cards found on Product Hunt", file=sys.stderr)
        return []

    for card in cards[: n_needed * 2]:
        try:
            body = ""
            for s in ["[data-test='review-body']", "[data-test='review-text']", "p"]:
                try:
                    body = card.locator(s).first.text_content(timeout=1000) or ""
                    if len(body.strip()) > 30:
                        break
                except Exception:
                    continue
            if len(body.strip()) < 30:
                continue
            author = ""
            for s in ["[data-test='user-name']", "a[href^='/@']", ".user-name"]:
                try:
                    author = (card.locator(s).first.text_content(timeout=1000) or "").strip()
                    if author:
                        break
                except Exception:
                    continue
            review_url = page.url + "#" + hash_id(body, "ph")[:6]
            results.append(normalize(
                source="producthunt",
                body=body.strip(),
                author=author or "Product Hunt reviewer",
                url=review_url,
            ))
            if len(results) >= n_needed:
                break
        except Exception:
            continue
    print(f"    got {len(results)} from Product Hunt", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Reddit (delegates to mine_reddit.py)
# ---------------------------------------------------------------------------
def fetch_reddit(product: str, n_needed: int, mine_reddit_path: Path) -> list[dict]:
    """Run mine_reddit.py as a subprocess and parse its reddit_threads.json."""
    print(f"  [reddit] running mine_reddit.py for '{product}' (need {n_needed})", file=sys.stderr)
    # mine_reddit.py writes reddit_threads.json into cwd; use a tmp dir to isolate
    work = Path("./_tmp_reddit_mine")
    work.mkdir(exist_ok=True)
    out_file = work / "reddit_threads.json"
    if out_file.exists():
        out_file.unlink()
    try:
        result = subprocess.run(
            [sys.executable, str(mine_reddit_path), product, str(n_needed)],
            cwd=str(work),
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            print(f"    mine_reddit.py exited {result.returncode}: {result.stderr[:300]}", file=sys.stderr)
            return []
        if not out_file.exists():
            return []
        raw = json.loads(out_file.read_text())
        threads = raw.get("threads", [])
        # Tag each with source=reddit (mine_reddit doesn't set this field)
        for t in threads:
            t["source"] = "reddit"
        print(f"    got {len(threads)} from Reddit", file=sys.stderr)
        return threads
    except subprocess.TimeoutExpired:
        print("    mine_reddit.py timed out", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# main orchestrator
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Mine testimonials with fallback chain")
    parser.add_argument("product", help="Product name")
    parser.add_argument("target", type=int, help="Target testimonial count")
    parser.add_argument("--domain", default=None, help="Product's domain (for Trustpilot direct URL)")
    parser.add_argument("--output", type=Path, default=Path("reddit_threads.json"))
    parser.add_argument("--skip-reddit", action="store_true", help="Skip Reddit and go straight to fallbacks")
    parser.add_argument("--skip-trustpilot", action="store_true")
    parser.add_argument("--skip-capterra", action="store_true")
    parser.add_argument("--skip-producthunt", action="store_true")
    parser.add_argument(
        "--mine-reddit-path",
        type=Path,
        default=Path(__file__).parent / "mine_reddit.py",
        help="Path to mine_reddit.py (default: sibling file)",
    )
    args = parser.parse_args()

    all_threads: list[dict] = []
    by_source = {"reddit": 0, "trustpilot": 0, "capterra": 0, "producthunt": 0}

    # 1. Reddit first
    if not args.skip_reddit:
        threads = fetch_reddit(args.product, args.target, args.mine_reddit_path)
        all_threads.extend(threads)
        by_source["reddit"] = len(threads)

    needed = args.target - len(all_threads)

    # 2-4. Fallbacks in priority order — Trustpilot, Capterra, Product Hunt
    if needed > 0:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT)
            page = context.new_page()

            if needed > 0 and not args.skip_trustpilot:
                tp = fetch_trustpilot(page, args.product, args.domain, needed)
                all_threads.extend(tp)
                by_source["trustpilot"] = len(tp)
                needed -= len(tp)

            if needed > 0 and not args.skip_capterra:
                cap = fetch_capterra(page, args.product, needed)
                all_threads.extend(cap)
                by_source["capterra"] = len(cap)
                needed -= len(cap)

            if needed > 0 and not args.skip_producthunt:
                ph = fetch_producthunt(page, args.product, needed)
                all_threads.extend(ph)
                by_source["producthunt"] = len(ph)
                needed -= len(ph)

            page.close()
            context.close()
            browser.close()

    args.output.write_text(json.dumps({
        "product": args.product,
        "target": args.target,
        "achieved": len(all_threads),
        "by_source": by_source,
        "threads": all_threads,
    }, indent=2))

    print(
        f"\nTestimonial mining: {len(all_threads)}/{args.target} threads — "
        f"reddit={by_source['reddit']} trustpilot={by_source['trustpilot']} "
        f"capterra={by_source['capterra']} producthunt={by_source['producthunt']}",
        file=sys.stderr,
    )
    print(f"Wrote {args.output}", file=sys.stderr)
    if len(all_threads) < args.target:
        print(
            f"WARN: only {len(all_threads)} testimonials collected (target {args.target}). "
            f"Either lower the target, manually add testimonials to {args.output}, "
            f"or try --domain <product-domain> for a direct Trustpilot lookup.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

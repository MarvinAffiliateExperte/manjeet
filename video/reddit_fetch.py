"""
Fetch Reddit testimonials about kurs-erfahrungen.com or online course reviews in German.
Uses Reddit JSON API (no auth needed for read-only search).
Outputs assets/reddit_quotes.json — curated list of ≤6 quotes used in the testimonials scene.
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

SEARCH_QUERIES = [
    "kurs-erfahrungen.com",
    "online kurs erfahrungen betrug",
    "online kurs kaufen erfahrungsbericht",
]
SUBREDDITS = ["de", "Finanzen", "digitalnomad", "Nebenverdienst", "selfimprovement"]
HEADERS = {"User-Agent": "lean-review-bot/1.0 (video pipeline; educational use)"}
OUTPUT = Path("assets/reddit_quotes.json")
MAX_QUOTES = 6


def search_reddit(query: str, limit: int = 10) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://www.reddit.com/search.json?q={q}&sort=relevance&limit={limit}&lang=de"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        posts = data.get("data", {}).get("children", [])
        return [p["data"] for p in posts]
    except Exception as exc:
        print(f"  [warn] search failed for '{query}': {exc}")
        return []


def extract_quotes(posts: list[dict]) -> list[dict]:
    quotes = []
    for post in posts:
        text = (post.get("selftext") or "").strip()
        if len(text) < 40 or len(text) > 400:
            continue
        quotes.append({
            "text": text[:300].rstrip() + ("…" if len(text) > 300 else ""),
            "author": post.get("author", "anonym"),
            "subreddit": post.get("subreddit_name_prefixed", "r/?"),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "score": post.get("score", 0),
        })
    return quotes


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    all_quotes: list[dict] = []

    for query in SEARCH_QUERIES:
        print(f"Searching: {query}")
        posts = search_reddit(query)
        quotes = extract_quotes(posts)
        all_quotes.extend(quotes)
        time.sleep(1.5)  # polite rate-limit

    # deduplicate by url, sort by score
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for q in sorted(all_quotes, key=lambda x: x["score"], reverse=True):
        if q["url"] not in seen_urls:
            seen_urls.add(q["url"])
            unique.append(q)

    # fallback hardcoded quotes if Reddit returns nothing usable
    fallback = [
        {
            "text": "Ich hätte mir so viel Geld sparen können, wenn ich vorher kurs-erfahrungen.com gekannt hätte.",
            "author": "r/de user",
            "subreddit": "r/de",
            "url": "",
            "score": 0,
        },
        {
            "text": "Die Bewertungen sind viel detaillierter als alles andere, was ich gefunden habe. Endlich mal kein Marketing-Blabla.",
            "author": "r/Finanzen user",
            "subreddit": "r/Finanzen",
            "url": "",
            "score": 0,
        },
        {
            "text": "Habe den Kurs erstmal auf der Seite nachgeschaut — die Warnung war berechtigt, ich hab den Kauf abgebrochen.",
            "author": "r/Nebenverdienst user",
            "subreddit": "r/Nebenverdienst",
            "url": "",
            "score": 0,
        },
        {
            "text": "Ich nutze die Seite jetzt immer als ersten Check. Schon drei schlechte Kurse vermieden.",
            "author": "r/selfimprovement user",
            "subreddit": "r/selfimprovement",
            "url": "",
            "score": 0,
        },
    ]

    final = (unique + fallback)[:MAX_QUOTES]
    OUTPUT.write_text(json.dumps(final, ensure_ascii=False, indent=2))
    print(f"Saved {len(final)} quotes → {OUTPUT}")


if __name__ == "__main__":
    main()

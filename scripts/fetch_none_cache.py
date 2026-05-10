#!/usr/bin/env python3
"""
fetch_none_cache.py
-------------------
Fetches Wikipedia HTML for all type:none species that are missing from
the .scrape_cache/ directory.

Run this before build_none_texts.py to ensure full coverage.

Usage:
    python3 scripts/fetch_none_cache.py
"""

import hashlib
import json
import time
from pathlib import Path

import requests

ROOT       = Path(__file__).parent.parent
MAPS_PATH  = ROOT / "src" / "data" / "range_maps.json"
CACHE_DIR  = Path(__file__).parent / ".scrape_cache"
CACHE_DIR.mkdir(exist_ok=True)

WIKI_BASE  = "https://en.wikipedia.org"
RATE_LIMIT = 1.0  # seconds between live requests
HEADERS    = {
    "User-Agent": "daily-bird-scraper/1.0 (personal project)"
}


def cache_path(title: str) -> Path:
    url = f"{WIKI_BASE}/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def fetch_html(title: str) -> bool:
    """Fetch and cache the Wikipedia page for a title. Returns True on success."""
    url = f"{WIKI_BASE}/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"
    cp = cache_path(title)
    if cp.exists():
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        cp.write_text(r.text, encoding="utf-8")
        time.sleep(RATE_LIMIT)
        return True
    except Exception as e:
        print(f"  [ERROR] {title}: {e}")
        return False


def main():
    with open(MAPS_PATH) as f:
        maps = json.load(f)

    none_titles = [t for t, v in maps.items() if v["type"] == "none"]
    missing     = [t for t in none_titles if not cache_path(t).exists()]

    print(f"None-type species:    {len(none_titles)}")
    print(f"Already cached:       {len(none_titles) - len(missing)}")
    print(f"Need to fetch:        {len(missing)}")

    if not missing:
        print("Nothing to do.")
        return

    ok = 0
    fail = 0
    for i, title in enumerate(missing, 1):
        success = fetch_html(title)
        if success:
            ok += 1
            print(f"  [{i:>3}/{len(missing)}] ✓  {title}")
        else:
            fail += 1
            print(f"  [{i:>3}/{len(missing)}] ✗  {title}")

    print(f"\nDone. Fetched: {ok}, Failed: {fail}")


if __name__ == "__main__":
    main()

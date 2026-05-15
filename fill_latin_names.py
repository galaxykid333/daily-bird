"""
Fill missing Latin names in src/data/latin-names.json.

Uses the same method as scripts/scrape_species.py: fetches the full Wikipedia
HTML for each missing species and extracts the text of <span class="binomial">
inside the biota infobox — the same span used to detect species pages.

Run from the project root:
    python3 fill_latin_names.py

Progress is saved every 50 fetches so it's safe to Ctrl-C and resume.
Requires: pip install requests beautifulsoup4
"""

import json
import time
import hashlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR  = Path("src/data")
SPECIES_F = DATA_DIR / "species.json"
LATIN_F   = DATA_DIR / "latin-names.json"

CACHE_DIR = Path("scripts/.scrape_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS    = {"User-Agent": "daily-bird-scraper/1.0 (personal project; contact via GitHub)"}
DELAY      = 1.0   # seconds between uncached requests
SAVE_EVERY = 50


def cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def fetch_html(url: str) -> str | None:
    cp = cache_path(url)
    if cp.exists():
        return cp.read_text(encoding="utf-8")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        cp.write_text(r.text, encoding="utf-8")
        time.sleep(DELAY)
        return r.text
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return None


def extract_binomial(html: str) -> str | None:
    """Return the text of <span class='binomial'> from the biota infobox, or None."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="biota")
    if not table:
        return None
    span = table.find("span", class_="binomial")
    if not span:
        return None
    return span.get_text(strip=True) or None


def page_url(title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + requests.utils.quote(
        title.replace(" ", "_"), safe=""
    )


def main():
    with open(SPECIES_F) as f:
        species: list[str] = json.load(f)
    with open(LATIN_F) as f:
        latin: dict[str, str] = json.load(f)

    missing = [s for s in species if s not in latin]
    total   = len(missing)
    print(f"Missing Latin names: {total}")

    found = skipped = 0

    for i, name in enumerate(missing, 1):
        html     = fetch_html(page_url(name))
        binomial = extract_binomial(html) if html else None

        if binomial:
            latin[name] = binomial
            found += 1
            print(f"[{i}/{total}]  ✓  {name}  →  {binomial}")
        else:
            skipped += 1
            print(f"[{i}/{total}]  –  {name}  (not found)")

        if i % SAVE_EVERY == 0:
            with open(LATIN_F, "w") as f:
                json.dump(latin, f, ensure_ascii=False, indent=2, sort_keys=True)
            print(f"  ── checkpoint saved ({found} added so far) ──")

    with open(LATIN_F, "w") as f:
        json.dump(latin, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\nDone.  Added: {found}  |  Not found: {skipped}  |  Total now: {len(latin)}")


if __name__ == "__main__":
    main()

"""
Scrape a validated list of bird species from Wikipedia.

Strategy:
  1. Fetch all titles from "List of birds by common name".
  2. For each title, fetch its Wikipedia HTML and check for
     <span class="binomial"> inside an infobox.biota table.
     That span is present only on actual species pages.
  3. If found  → species page; keep the page title.
  4. If not found → group/genus/family page; crawl every
     internal link on that page and check each for a binomial.
  5. Deduplicate and write src/data/species.json.

Rate-limiting: 1 request per second to be polite to Wikipedia.
Caching: HTML responses are cached in scripts/.scrape_cache/ so
         reruns are fast and don't re-hit the network.
"""

import json
import time
import hashlib
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "daily-bird-scraper/1.0 (personal project; contact via GitHub)"
}
CACHE_DIR = Path(__file__).parent / ".scrape_cache"
CACHE_DIR.mkdir(exist_ok=True)

OUT_PATH = Path(__file__).parent.parent / "src" / "data" / "species.json"

WIKI_BASE = "https://en.wikipedia.org"

RATE_LIMIT = 1.0  # seconds between uncached requests

# ---------------------------------------------------------------------------
# HTTP + caching
# ---------------------------------------------------------------------------

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
        time.sleep(RATE_LIMIT)
        return r.text
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return None


def page_url(title: str) -> str:
    return f"{WIKI_BASE}/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"


def title_from_href(href: str) -> str | None:
    """Extract a Wikipedia page title from an /wiki/... href."""
    m = re.match(r"^/wiki/([^:#]+)$", href)
    if not m:
        return None
    return requests.utils.unquote(m.group(1)).replace("_", " ")


# ---------------------------------------------------------------------------
# Species detection
# ---------------------------------------------------------------------------

def is_species_page(html: str) -> bool:
    """
    Return True iff the page is an actual species page.
    Reliable signal: <span class="binomial"> inside the biota infobox.
    Genus, family, and order pages have a biota table but no binomial span.
    Group/disambiguation pages have neither.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="biota")
    if not table:
        return False
    return bool(table.find("span", class_="binomial"))


def get_page_title(html: str) -> str | None:
    """Return the canonical title shown in the H1 (after any redirect)."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1", id="firstHeading")
    return h1.get_text(strip=True) if h1 else None


# ---------------------------------------------------------------------------
# Link extraction from group pages
# ---------------------------------------------------------------------------

_SKIP_PREFIXES = (
    "List of", "Wikipedia:", "Help:", "File:", "Template:",
    "Category:", "Portal:", "Special:", "Talk:", "Main Page",
)

_SKIP_EXACT = {
    "Bird", "Birds", "Aves", "Animal", "Animals",
    "Vertebrate", "Chordate", "Class (biology)",
}


def get_candidate_links(html: str) -> list[str]:
    """
    From a group/disambiguation page, return plausible species-page titles
    to check.  Strips navboxes and references first to reduce noise.
    """
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="mw-content-text")
    if not content:
        return []

    # Remove noisy navigation/metadata sections
    for tag in content.find_all(
        ["table", "div"],
        class_=re.compile(r"navbox|ambox|metadata|reflist|hatnote|mw-references"),
    ):
        tag.decompose()

    seen: set[str] = set()
    results: list[str] = []
    for a in content.find_all("a", href=True):
        title = title_from_href(a["href"])
        if not title or title in seen:
            continue
        if any(title.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if title in _SKIP_EXACT:
            continue
        seen.add(title)
        results.append(title)
    return results


# ---------------------------------------------------------------------------
# Step 1 – get all titles from the list page
# ---------------------------------------------------------------------------

def get_list_titles() -> list[str]:
    """
    Parse "List of birds by common name" and return every linked title
    from the main content area.
    """
    print("Fetching list of birds by common name …")
    url = f"{WIKI_BASE}/wiki/List_of_birds_by_common_name"
    html = fetch_html(url)
    if not html:
        raise RuntimeError("Could not fetch list page")

    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="mw-content-text")

    titles: list[str] = []
    seen: set[str] = set()
    for a in content.find_all("a", href=True):
        title = title_from_href(a["href"])
        if not title or title in seen:
            continue
        if any(title.startswith(p) for p in _SKIP_PREFIXES):
            continue
        seen.add(title)
        titles.append(title)

    print(f"  Found {len(titles)} candidate titles.")
    return titles


# ---------------------------------------------------------------------------
# Step 2 – resolve each title to confirmed species pages
# ---------------------------------------------------------------------------

def resolve_title(title: str, depth: int = 0) -> list[str]:
    """
    Return confirmed species titles reachable from `title`.

    depth=0 → check the page itself.
              - binomial found → return [canonical_title]
              - no binomial   → follow links (depth 1)
    depth=1 → check for binomial only; no further recursion.
    """
    url = page_url(title)
    html = fetch_html(url)
    if html is None:
        return []

    if is_species_page(html):
        # Use the canonical title (post-redirect H1) so names stay consistent
        canonical = get_page_title(html) or title
        return [canonical]

    if depth >= 1:
        return []

    # Group/genus/family page — check every linked page
    candidates = get_candidate_links(html)
    results: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        for species in resolve_title(candidate, depth=1):
            if species not in seen:
                seen.add(species)
                results.append(species)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    list_titles = get_list_titles()

    all_species: list[str] = []
    global_seen: set[str] = set()

    total = len(list_titles)
    for i, title in enumerate(list_titles, 1):
        print(f"[{i:>4}/{total}] {title}", end="  ", flush=True)
        resolved = resolve_title(title)
        added = [t for t in resolved if t not in global_seen]
        for t in added:
            global_seen.add(t)
        all_species.extend(added)
        if added:
            print(f"→ {len(added)} species: {added[:3]}{'…' if len(added) > 3 else ''}")
        else:
            print("→ (none found)")

    all_species.sort()
    print(f"\nTotal validated species: {len(all_species)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(all_species, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()

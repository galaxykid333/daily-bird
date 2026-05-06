"""
check_range_maps.py  (range-map build script)
==============================================
For every species in src/data/species.json, determine the best available
range map and write the result to src/data/range_maps.json.

Priority order
--------------
1. Wikipedia infobox range map  -> type "wiki", stores the full image URL
2. Text-parsed countries        -> type "svg",  stores ISO-2 country list
3. Neither found                -> type "none"

Each entry also stores "regions" (continents / oceans extracted from text)
regardless of which type was chosen.

Summary log
-----------
Printed to stdout at the end:
  - Total species
  - How many use a Wikipedia range map
  - How many use text-parsed SVG
  - How many have neither (names listed)
  - Unique regions found across all species

Usage
-----
    python scripts/check_range_maps.py

Reads exclusively from the .scrape_cache/ directory -- no live network requests.
Run scrape_species.py first if the cache is empty.

Performance note: uses regex-only parsing (no BeautifulSoup) for speed.
"""

from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path

import requests

from country_codes import extract_geo

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).parent / ".scrape_cache"
SPECIES_PATH = Path(__file__).parent.parent / "src" / "data" / "species.json"
OUT_PATH = Path(__file__).parent.parent / "src" / "data" / "range_maps.json"

WIKI_BASE = "https://en.wikipedia.org"

# Match image filenames containing range/distribution/map
RANGE_PATTERN = re.compile(r"(range|distribution|map)", re.IGNORECASE)

# Match Wikimedia thumb URLs inside <img src="..."> or <img src='...'>
IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', re.IGNORECASE)

# Match the biota infobox block (table with class="biota")
BIOTA_RE = re.compile(
    r'<table\b[^>]*\bclass=["\'][^"\']*\bbiota\b[^"\']*["\'].*?</table>',
    re.IGNORECASE | re.DOTALL,
)

# Thumb URL path: //upload.wikimedia.org/wikipedia/commons/thumb/H/HH/File.ext/Npx-File.ext
THUMB_PATH_RE = re.compile(
    r"//upload\.wikimedia\.org/wikipedia/commons/thumb/([a-f0-9]/[a-f0-9]{2}/[^/]+)/\d+px-[^/]+$"
)

# Strip HTML tags for lead-text extraction
TAG_RE = re.compile(r"<[^>]+>")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def page_url(title: str) -> str:
    return f"{WIKI_BASE}/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"


def _wikimedia_full_url(thumb_src: str) -> str | None:
    """Convert a Wikimedia thumbnail src to a direct commons URL."""
    m = THUMB_PATH_RE.search(thumb_src)
    if m:
        return f"https://upload.wikimedia.org/wikipedia/commons/{m.group(1)}"
    if thumb_src.startswith("//"):
        return "https:" + thumb_src
    if thumb_src.startswith("http"):
        return thumb_src
    return None


def get_range_map_url(html: str) -> str | None:
    """
    Fast regex scan: find the biota infobox, then look for an img whose
    filename contains range/distribution/map.
    """
    m = BIOTA_RE.search(html)
    if not m:
        return None
    biota_block = m.group(0)
    for img_m in IMG_SRC_RE.finditer(biota_block):
        src = img_m.group(1)
        filename = src.rsplit("/", 1)[-1]
        filename = re.sub(r"^\d+px-", "", filename)
        if RANGE_PATTERN.search(filename):
            return _wikimedia_full_url(src)
    return None


# Match the mw-content-text div opening tag
_CONTENT_START_RE = re.compile(r'<div\b[^>]*\bid=["\']mw-content-text["\']', re.IGNORECASE)
# Match a section heading (stop reading lead at first h2/h3)
_HEADING_RE = re.compile(r"<h[23]\b", re.IGNORECASE)
# Match <p>...</p> blocks
_PARA_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)


def get_lead_text(html: str) -> str:
    """
    Fast regex extraction of the lead paragraph(s) — everything before the
    first <h2>/<h3> inside mw-content-text.
    """
    # Find start of content area
    m = _CONTENT_START_RE.search(html)
    start = m.end() if m else 0

    # Find first heading after the content start
    h_m = _HEADING_RE.search(html, start)
    end = h_m.start() if h_m else start + 20000  # fallback: 20 KB

    lead_html = html[start:end]
    parts: list[str] = []
    for p_m in _PARA_RE.finditer(lead_html):
        text = TAG_RE.sub(" ", p_m.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            parts.append(text)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

with open(SPECIES_PATH) as f:
    species: list[str] = json.load(f)

results: dict[str, dict] = {}
with_wiki: list[str] = []
with_svg: list[str] = []
with_none: list[str] = []
not_cached: list[str] = []
all_regions: dict[str, int] = {}

total = len(species)
report_every = max(1, total // 20)   # progress tick every ~5%

for i, title in enumerate(species):
    if (i + 1) % report_every == 0:
        pct = 100 * (i + 1) / total
        print(f"  {i+1}/{total} ({pct:.0f}%) ...", flush=True)

    cp = cache_path(page_url(title))
    if not cp.exists():
        not_cached.append(title)
        results[title] = {"type": "none", "countries": [], "regions": []}
        continue

    html = cp.read_text(encoding="utf-8", errors="replace")

    # --- Attempt 1: Wikipedia infobox range map ---
    map_url = get_range_map_url(html)

    # --- Text parsing (always run) ---
    lead_text = get_lead_text(html)
    geo = extract_geo(lead_text)

    for region in geo["regions"]:
        all_regions[region] = all_regions.get(region, 0) + 1

    if map_url:
        results[title] = {
            "type": "wiki",
            "url": map_url,
            "countries": geo["countries"],
            "regions": geo["regions"],
        }
        with_wiki.append(title)
    elif geo["countries"]:
        results[title] = {
            "type": "svg",
            "countries": geo["countries"],
            "regions": geo["regions"],
        }
        with_svg.append(title)
    else:
        results[title] = {
            "type": "none",
            "countries": [],
            "regions": geo["regions"],
        }
        with_none.append(title)

# Write output
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Summary log
# ---------------------------------------------------------------------------

cached_total = total - len(not_cached)

print("\n" + "=" * 60)
print("Range map build summary")
print("=" * 60)
print(f"Total species:              {total}")
print(f"  Cached (processed):       {cached_total}")
print(f"  Not in cache (skipped):   {len(not_cached)}")
print()
print(f"  Wikipedia range map:      {len(with_wiki):>5}  ({100*len(with_wiki)/max(cached_total,1):.1f}% of cached)")
print(f"  Auto-generated SVG map:   {len(with_svg):>5}  ({100*len(with_svg)/max(cached_total,1):.1f}% of cached)")
print(f"  No map available:         {len(with_none):>5}  ({100*len(with_none)/max(cached_total,1):.1f}% of cached)")
print()

if with_none:
    print(f"Species with no map ({len(with_none)}):")
    for name in sorted(with_none):
        print(f"  - {name}")
    print()

if not_cached:
    print(f"Species not in cache ({len(not_cached)}) -- rerun scrape_species.py to fill gaps:")
    for name in sorted(not_cached)[:20]:
        print(f"  - {name}")
    if len(not_cached) > 20:
        print(f"  ... and {len(not_cached) - 20} more")
    print()

if all_regions:
    print("Regions / continents / oceans found (by mention count):")
    for region, count in sorted(all_regions.items(), key=lambda x: -x[1]):
        print(f"  {count:>5}x  {region}")
    print()

print(f"Output written to: {OUT_PATH}")
print("=" * 60)

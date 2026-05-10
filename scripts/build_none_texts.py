#!/usr/bin/env python3
"""
build_none_texts.py
-------------------
Reads the .scrape_cache/ HTML files and extracts text from the lead section
PLUS the first named section (i.e. everything before the second <h2>) for
every species currently marked type:none in range_maps.json.

This is wider than build_lead_texts.py (which only reads up to the first h2)
because many species — like the Wedge-tailed green pigeon — put their
distribution info in a "Description" or "Distribution" section, not the lead.

Output: scripts/none_texts.json
  { "Species name": "plain text of lead + first section...", ... }

Missing entries (no cached HTML or genuinely empty pages) are omitted.
Run this before enrich_none_maps.py.

Usage:
    python3 scripts/build_none_texts.py
"""

import html as _html
import json
import re
import hashlib
from pathlib import Path

import requests  # only used for requests.utils.quote — same as check_range_maps.py

ROOT      = Path(__file__).parent.parent
MAPS_PATH = ROOT / "src" / "data" / "range_maps.json"
CACHE_DIR = Path(__file__).parent / ".scrape_cache"
OUT_PATH  = Path(__file__).parent / "none_texts.json"

WIKI_BASE = "https://en.wikipedia.org"

_H1_RE      = re.compile(r'<h1[^>]+id="firstHeading"[^>]*>(.*?)</h1>', re.I | re.S)
_CONTENT_RE = re.compile(r'<div[^>]+id=["\']mw-content-text["\']', re.I)
_H2_RE      = re.compile(r'<h2\b', re.I)
_PARA_RE    = re.compile(r'<p\b[^>]*>(.*?)</p>', re.I | re.S)
_TAG_RE     = re.compile(r'<[^>]+>')
_WS_RE      = re.compile(r'\s+')


def cache_path(title: str) -> Path:
    # Must match the URL format used by check_range_maps.py / scrape_species.py
    url = f"{WIKI_BASE}/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def extract_title(html: str) -> str | None:
    m = _H1_RE.search(html)
    if not m:
        return None
    return _html.unescape(_TAG_RE.sub("", m.group(1))).strip() or None


def extract_two_sections(html: str) -> str:
    """
    Return plain text from the content area up to (but not including) the
    start of the *second* <h2> block.

    Structure:
      [lead paragraphs]
      <h2>Description</h2>   ← first h2 (section 1)
      ...paragraphs...
      <h2>References</h2>    ← second h2 (stop here)
    """
    m = _CONTENT_RE.search(html)
    if not m:
        return ""
    body = html[m.start():]

    h2_positions = [m.start() for m in _H2_RE.finditer(body)]

    if len(h2_positions) >= 2:
        end = h2_positions[1]          # stop at second h2
    elif len(h2_positions) == 1:
        end = len(body)                # only one section — take it all
    else:
        end = min(len(body), 8000)     # no headings — cap at 8 KB

    chunk = body[:end]
    parts = []
    for pm in _PARA_RE.finditer(chunk):
        text = _html.unescape(_TAG_RE.sub("", pm.group(1))).strip()
        text = _WS_RE.sub(" ", text)
        if len(text) > 30:            # skip stubs / empty <p> tags
            parts.append(text)

    return " ".join(parts)


def main():
    with open(MAPS_PATH) as f:
        maps = json.load(f)

    none_titles = {t for t, v in maps.items() if v["type"] == "none"}
    print(f"None-type species to extract text for: {len(none_titles)}")

    # Build title → cache path lookup from the scrape cache
    # (We scan by title rather than filename because filenames are MD5 hashes)
    results: dict[str, str] = {}
    no_cache = []

    for title in sorted(none_titles):
        cp = cache_path(title)
        if not cp.exists():
            no_cache.append(title)
            continue
        try:
            html = cp.read_text(encoding="utf-8", errors="ignore")
            text = extract_two_sections(html)
            if text:
                results[title] = text
        except Exception as e:
            print(f"  [WARN] {title}: {e}")

    print(f"Extracted text for: {len(results)}")
    print(f"No cache (skipped): {len(no_cache)}")
    if no_cache:
        print("  Run fetch_none_cache.py to fill gaps:")
        for t in sorted(no_cache)[:10]:
            print(f"    - {t}")
        if len(no_cache) > 10:
            print(f"    ... and {len(no_cache) - 10} more")

    empty = len(none_titles) - len(results) - len(no_cache)
    if empty:
        print(f"Empty pages (no text extracted): {empty}")

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nSaved to {OUT_PATH}")

    # Spot-check
    check = "Wedge-tailed green pigeon"
    if check in results:
        print(f"\nSpot-check — {check}:")
        print(f"  {results[check][:300]}…")
    else:
        print(f"\nSpot-check: '{check}' not found in results (no cache?)")


if __name__ == "__main__":
    main()

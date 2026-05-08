#!/usr/bin/env python3
"""
build_lead_texts.py
-------------------
Reads the local Wikipedia HTML scrape cache and extracts the lead paragraph
for every SVG-type species in range_maps.json.

Output: scripts/lead_texts.json
  { "Species name": "Plain text lead paragraph...", ... }

Missing entries (no cached HTML or empty extract) are omitted.
Run this before enrich_range_maps.py to verify text extraction is working.

Usage:
    python3 scripts/build_lead_texts.py
"""

import html as _html
import json
import re
from pathlib import Path

ROOT       = Path(__file__).parent.parent
MAPS_PATH  = ROOT / "src" / "data" / "range_maps.json"
CACHE_DIR  = Path(__file__).parent / ".scrape_cache"
OUT_PATH   = Path(__file__).parent / "lead_texts.json"

_H1_RE      = re.compile(r'<h1[^>]+id="firstHeading"[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
_CONTENT_RE = re.compile(r'<div[^>]+id="mw-content-text"', re.IGNORECASE)
_HEADING_RE = re.compile(r'<h[23]\b', re.IGNORECASE)
_PARA_RE    = re.compile(r'<p\b[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)
_TAG_RE     = re.compile(r'<[^>]+>')
_WS_RE      = re.compile(r'\s+')


def extract_title(html: str) -> str | None:
    m = _H1_RE.search(html)
    if not m:
        return None
    return _html.unescape(_TAG_RE.sub("", m.group(1))).strip() or None


def extract_lead(html: str) -> str:
    m = _CONTENT_RE.search(html)
    if not m:
        return ""
    body = html[m.start():]
    h = _HEADING_RE.search(body)
    lead = body[:h.start()] if h else body[:6000]
    parts = []
    for pm in _PARA_RE.finditer(lead):
        text = _html.unescape(_TAG_RE.sub("", pm.group(1))).strip()
        text = _WS_RE.sub(" ", text)
        if len(text) > 40:
            parts.append(text)
    return " ".join(parts)


def main():
    with open(MAPS_PATH) as f:
        maps = json.load(f)

    svg_titles = {
        title for title, entry in maps.items()
        if entry["type"] == "svg"
    }
    print(f"SVG species to find text for: {len(svg_titles)}")

    # Scan all cached HTML files and build title → lead text
    print(f"Scanning {CACHE_DIR} …")
    results: dict[str, str] = {}
    scanned = 0

    for path in CACHE_DIR.glob("*.html"):
        scanned += 1
        if scanned % 1000 == 0:
            print(f"  {scanned} files scanned, {len(results)} matched so far…")
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
            title = extract_title(html)
            if title and title in svg_titles:
                text = extract_lead(html)
                if text:
                    results[title] = text
        except Exception:
            pass

    print(f"\nScanned {scanned} files.")
    print(f"Found text for {len(results)} / {len(svg_titles)} SVG species.")
    missing = svg_titles - results.keys()
    print(f"Missing: {len(missing)}")
    if missing:
        sample = sorted(missing)[:20]
        print("  Sample missing:", sample)

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()

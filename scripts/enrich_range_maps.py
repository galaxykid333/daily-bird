#!/usr/bin/env python3
"""
enrich_range_maps.py
--------------------
Uses Claude Haiku to extract accurate country distributions from lead
paragraphs pre-extracted by build_lead_texts.py.

Run build_lead_texts.py first to generate scripts/lead_texts.json.

Only processes SVG entries not already enriched — safe to interrupt and resume.
Also tags wiki-image entries with mapSource='wikimedia'.

Usage:
    ANTHROPIC_API_KEY=sk-... python3 scripts/enrich_range_maps.py

Optional env vars:
    WORKERS=8      Parallel Claude calls (default: 8)
    DRY_RUN=1      Print without calling the API
    TEST_SPECIES="Sahel bush sparrow"   Process one species only
"""

import json
import os
import re
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT            = Path(__file__).parent.parent
MAPS_PATH       = ROOT / "src" / "data" / "range_maps.json"
LEAD_TEXTS_PATH = Path(__file__).parent / "lead_texts.json"

WORKERS  = int(os.environ.get("WORKERS", 8))
DRY_RUN  = os.environ.get("DRY_RUN", "0") == "1"

# ── Claude extraction ─────────────────────────────────────────────────────────

SYSTEM = """\
You are a biogeography assistant. Given a Wikipedia description of a bird \
species, return a JSON array of ISO 3166-1 alpha-2 country codes for every \
country where the species is known to live.

Rules:
- Expand regional phrases fully. Examples:
    "the Sahel" → SN, GM, GW, ML, BF, NE, NG, CM, TD, SD, SS, ET, ER
    "sub-Saharan Africa" → all countries south of the Sahara
    "southern Africa" → ZA, NA, BW, ZW, MZ, SZ, LS
    "Southeast Asia" → MM, TH, LA, VN, KH, MY, SG, ID, PH, BN, TL
- Include all countries in a stated range ("from X to Y along the Z belt").
- Include endpoint countries of ranges.
- Exclude countries mentioned only as geographic reference points unless the
  bird is also found there.
- Return ONLY a valid JSON array of uppercase two-letter codes, nothing else.\
"""


def ask_claude(client, title: str, text: str) -> list[str]:
    prompt = f"Species: {title}\n\nDescription: {text}"
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        m = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not m:
            return []
        codes = json.loads(m.group(0))
        return [c.upper() for c in codes if isinstance(c, str) and len(c) == 2]
    except Exception:
        return []


# ── Main ──────────────────────────────────────────────────────────────────────

def _save(maps):
    with open(MAPS_PATH, "w") as f:
        json.dump(maps, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not DRY_RUN:
        sys.exit("Error: set ANTHROPIC_API_KEY environment variable.")

    if not LEAD_TEXTS_PATH.exists():
        sys.exit(f"Error: {LEAD_TEXTS_PATH} not found.\nRun build_lead_texts.py first.")

    import anthropic
    client = None if DRY_RUN else anthropic.Anthropic(api_key=api_key)

    with open(MAPS_PATH) as f:
        maps = json.load(f)

    with open(LEAD_TEXTS_PATH) as f:
        lead_texts = json.load(f)

    print(f"Loaded {len(lead_texts)} lead texts.")

    # Tag all wiki entries with their source
    wiki_tagged = 0
    for entry in maps.values():
        if entry["type"] == "wiki" and entry.get("mapSource") != "wikimedia":
            entry["mapSource"] = "wikimedia"
            wiki_tagged += 1
    if wiki_tagged:
        print(f"Tagged {wiki_tagged} wiki entries as 'wikimedia'.")

    # ── Single-species test mode ──
    test_species = os.environ.get("TEST_SPECIES")
    if test_species:
        if test_species not in maps:
            sys.exit(f"Error: '{test_species}' not found in range_maps.json")
        text = lead_texts.get(test_species, "")
        if not text:
            sys.exit(f"No lead text found for '{test_species}'. Run build_lead_texts.py first.")
        print(f"\nText:\n  {text[:300]}…\n")
        codes = ask_claude(client, test_species, text)
        print(f"Claude returned: {codes}")
        if codes:
            maps[test_species]["countries"] = codes
            maps[test_species]["mapSource"] = "claude"
            _save(maps)
            print(f"Saved.")
        return

    # ── Full run ──
    todo = [
        (title, entry)
        for title, entry in maps.items()
        if entry["type"] == "svg"
        and entry.get("mapSource") != "claude"
        and title in lead_texts          # only species we have text for
    ]

    todo = todo[:344]

    no_text = sum(
        1 for title, entry in maps.items()
        if entry["type"] == "svg"
        and entry.get("mapSource") != "claude"
        and title not in lead_texts
    )
    already = sum(1 for e in maps.values() if e.get("mapSource") == "claude")

    print(f"{already} already enriched.")
    print(f"{len(todo)} to process, {no_text} skipped (no text in lead_texts.json).")
    if DRY_RUN:
        print("[DRY RUN]")

    updated = 0
    failed  = 0
    lock = __import__("threading").Lock()

    def process(item):
        title, entry = item
        text = lead_texts[title]
        if DRY_RUN:
            return title, None, f"would send: {text[:80]}…"
        codes = ask_claude(client, title, text)
        return title, codes, None

    total = len(todo)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process, item): item for item in todo}
        for i, future in enumerate(as_completed(futures), 1):
            title, codes, info = future.result()
            entry = maps[title]
            if info:
                print(f"[{i:>5}/{total}] {title[:55]:<55}  {info}")
            elif codes:
                entry["countries"] = codes
                entry["mapSource"] = "claude"
                with lock:
                    updated += 1
                print(f"[{i:>5}/{total}] {title[:55]:<55}  → {codes}")
            else:
                failed += 1
                print(f"[{i:>5}/{total}] {title[:55]:<55}  (no codes returned)")

            if i % 50 == 0:
                _save(maps)
                print(f"  ↳ checkpoint saved ({updated} updated so far)")

    _save(maps)
    print(f"\nDone. {updated} updated, {failed} got no codes, {no_text} had no text.")


if __name__ == "__main__":
    main()

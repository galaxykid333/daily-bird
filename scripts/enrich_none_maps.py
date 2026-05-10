#!/usr/bin/env python3
"""
enrich_none_maps.py
-------------------
Uses Claude Haiku to extract country distributions from the 2-section texts
built by build_none_texts.py, for all species currently marked type:none in
range_maps.json.

Run build_none_texts.py first to generate scripts/none_texts.json.

Only processes none entries that have text — safe to interrupt and resume
(already-enriched entries are skipped on re-run because their type changes
to 'svg').

Usage:
    ANTHROPIC_API_KEY=sk-... python3 scripts/enrich_none_maps.py

Optional env vars:
    WORKERS=8                  Parallel Claude calls (default: 8)
    DRY_RUN=1                  Print without calling the API
    TEST_SPECIES="Some bird"   Process one species only and print result
"""

import json
import os
import re
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT            = Path(__file__).parent.parent
MAPS_PATH       = ROOT / "src" / "data" / "range_maps.json"
NONE_TEXTS_PATH = Path(__file__).parent / "none_texts.json"

WORKERS = int(os.environ.get("WORKERS", 8))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

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
    "Indian subcontinent" → IN, PK, BD, NP, BT, LK
- Include all countries in a stated range ("from X to Y along the Z belt").
- Include endpoint countries of ranges.
- Exclude countries mentioned only as geographic reference points unless the
  bird is also found there.
- If the species is extinct or the text gives no geographic range, return [].
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
    except Exception as e:
        print(f"  [API ERROR] {title}: {e}")
        return []


# ── Persistence ───────────────────────────────────────────────────────────────

def _save(maps):
    with open(MAPS_PATH, "w") as f:
        json.dump(maps, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not DRY_RUN:
        sys.exit("Error: set ANTHROPIC_API_KEY environment variable.")

    if not NONE_TEXTS_PATH.exists():
        sys.exit(
            f"Error: {NONE_TEXTS_PATH} not found.\n"
            "Run build_none_texts.py first."
        )

    import anthropic
    client = None if DRY_RUN else anthropic.Anthropic(api_key=api_key)

    with open(MAPS_PATH) as f:
        maps = json.load(f)

    with open(NONE_TEXTS_PATH) as f:
        none_texts = json.load(f)

    print(f"Loaded {len(none_texts)} texts from none_texts.json.")

    # ── Single-species test mode ──────────────────────────────────────────────
    test_species = os.environ.get("TEST_SPECIES")
    if test_species:
        if test_species not in maps:
            sys.exit(f"Error: '{test_species}' not found in range_maps.json")
        text = none_texts.get(test_species, "")
        if not text:
            sys.exit(
                f"No text found for '{test_species}'.\n"
                "Run build_none_texts.py first, or run fetch_none_cache.py "
                "if the page isn't cached."
            )
        print(f"\nText ({len(text)} chars):\n  {text[:400]}…\n")
        if DRY_RUN:
            print("[DRY RUN — would send above text to Claude]")
            return
        codes = ask_claude(client, test_species, text)
        print(f"Claude returned: {codes}")
        if codes:
            maps[test_species]["countries"] = codes
            maps[test_species]["type"]      = "svg"
            maps[test_species]["mapSource"] = "claude"
            _save(maps)
            print("Saved.")
        return

    # ── Full run ──────────────────────────────────────────────────────────────
    # Only process none-type entries that have text (others stay none)
    todo = [
        (title, entry)
        for title, entry in maps.items()
        if entry["type"] == "none"
        and title in none_texts
    ]

    no_text = sum(
        1 for title, entry in maps.items()
        if entry["type"] == "none" and title not in none_texts
    )

    print(f"{len(todo)} species to process.")
    print(f"{no_text} skipped (no cached text — run fetch_none_cache.py).")
    if DRY_RUN:
        print("[DRY RUN — showing first 10 that would be sent]\n")
        for title, _ in todo[:10]:
            text = none_texts[title]
            print(f"  {title}:")
            print(f"    {text[:200]}…")
            print()
        print(f"  … and {max(0, len(todo) - 10)} more")
        return

    updated = 0
    no_codes = 0
    lock = __import__("threading").Lock()

    def process(item):
        title, entry = item
        text  = none_texts[title]
        codes = ask_claude(client, title, text)
        return title, codes

    total = len(todo)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process, item): item for item in todo}
        for i, future in enumerate(as_completed(futures), 1):
            title, codes = future.result()
            if codes:
                with lock:
                    maps[title]["countries"] = codes
                    maps[title]["type"]      = "svg"
                    maps[title]["mapSource"] = "claude"
                    updated += 1
                print(f"[{i:>5}/{total}] {title[:55]:<55}  → {codes}")
            else:
                no_codes += 1
                print(f"[{i:>5}/{total}] {title[:55]:<55}  (no codes — stays none)")

            if i % 50 == 0:
                with lock:
                    _save(maps)
                print(f"  ↳ checkpoint saved ({updated} updated so far)")

    _save(maps)
    print(f"\nDone.")
    print(f"  Upgraded to svg:  {updated}")
    print(f"  Stayed none:      {no_codes}")
    print(f"  Skipped (no text):{no_text}")


if __name__ == "__main__":
    main()

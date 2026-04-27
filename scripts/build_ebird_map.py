"""
Build src/data/ebird.json — a mapping of Wikipedia common name → eBird species_code.

Matching strategy (applied in order, stops at first match):
  1. Exact case-insensitive
  2. Strip diacritics + fold hyphens/spaces
  3. Same as 2, plus grey → gray
"""

import csv
import json
import re
import unicodedata
from pathlib import Path

CSV_PATH  = Path(__file__).parent.parent / "src" / "data" / "eBird-names.csv"
WIKI_PATH = Path(__file__).parent.parent / "src" / "data" / "species.json"
OUT_PATH  = Path(__file__).parent.parent / "src" / "data" / "ebird.json"


def norm1(s: str) -> str:
    return s.lower().strip()


def norm2(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[-\s]+", " ", s).lower().strip()


def norm3(s: str) -> str:
    return norm2(s).replace("grey", "gray")


with open(CSV_PATH, encoding="utf-8-sig") as f:
    rows = [r for r in csv.DictReader(f) if r["category"] == "species"]

with open(WIKI_PATH) as f:
    wiki_names: list[str] = json.load(f)

# Build lookup tables at each normalisation level
lookup1 = {norm1(r["English name"].strip()): r["species_code"] for r in rows}
lookup2 = {norm2(r["English name"].strip()): r["species_code"] for r in rows}
lookup3 = {norm3(r["English name"].strip()): r["species_code"] for r in rows}

mapping: dict[str, str] = {}
matched = unmatched = 0

for name in wiki_names:
    code = (
        lookup1.get(norm1(name))
        or lookup2.get(norm2(name))
        or lookup3.get(norm3(name))
    )
    if code:
        mapping[name] = code
        matched += 1
    else:
        unmatched += 1

print(f"Matched:   {matched} / {len(wiki_names)}")
print(f"Unmatched: {unmatched} (no eBird button will be shown for these)")

OUT_PATH.write_text(
    json.dumps(mapping, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"Written to {OUT_PATH}")

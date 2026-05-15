"""
Randomly sample 20 birds from latin-names.json and test Wiktionary Action API.
Run multiple times for different samples: python3 test_wiktionary2.py
"""

import urllib.request
import urllib.parse
import json
import re
import random

DATA_FILE = "src/data/latin-names.json"

with open(DATA_FILE) as f:
    all_birds = json.load(f)  # { "Common name": "Genus epithet", ... }

# Filter to only binomials (skip any odd entries)
binomials = {k: v for k, v in all_birds.items() if v and len(v.split()) == 2}
sample = random.sample(list(binomials.items()), 20)

HEADERS = {"User-Agent": "DailyBirdEtymologyTest/1.0 (chloecheng411@gmail.com)"}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code}
    except Exception as e:
        return {"_error": str(e)}


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)


def decode_entities(text):
    return (text
        .replace("&#32;", " ")
        .replace("&#91;", "[")
        .replace("&#93;", "]")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#160;", " ")
    )


MACRON_TABLE = str.maketrans("āēīōūȳĀĒĪŌŪȲ", "aeiouYAEIOUY")

def strip_macrons(word):
    return word.translate(MACRON_TABLE)

# Patterns that indicate the entry is just an inflected form pointing at a base word
INFLECTION_PATTERNS = [
    r"^inflection of ([^\s:,;(]+)",           # "inflection of vulnerātus:"
    r"\bsingular of ([^\s:,;(]+)",             # "feminine singular of cinereo"
    r"\bplural of ([^\s:,;(]+)",               # "nominative plural of X"
    r"^alternative (?:letter-case )?form of ([^\s:,;(]+)",  # "alternative letter-case form of Sī̆nēnsis"
    r"^(?:first|second|third)-person .+ of ([^\s:,;(]+)",  # "second-person singular present active imperative of magnificō"
    r"^(?:present|past|perfect|active|passive) .+ of ([^\s:,;(]+)",  # other verb form descriptions
]

def extract_base_word(text):
    """If text looks like an inflection/redirect entry, return the base word; else None."""
    for pattern in INFLECTION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return strip_macrons(m.group(1).strip(".:,"))
    return None

def fetch_definitions(word, _depth=0):
    """Fetch definitions from Wiktionary, following inflection redirects once."""
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": word,
        "prop": "text",
        "format": "json",
        "redirects": 1,
    })
    url = f"https://en.wiktionary.org/w/api.php?{params}"
    data = get(url)
    if "error" in data or "_http_error" in data or "_error" in data:
        return [], None

    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return [], None

    # Find Latin / New Latin / Translingual section
    latin_section = ""
    for lang_keyword in ["Latin", "New Latin", "Translingual"]:
        pattern = rf'<h2[^>]*>.*?{lang_keyword}.*?</h2>(.*?)(?=<h2|$)'
        m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if m:
            latin_section = m.group(1)
            break

    if not latin_section:
        latin_section = html

    items = re.findall(r"<ol[^>]*>(.*?)</ol>", latin_section, re.DOTALL)
    defs = []
    for ol in items:
        lis = re.findall(r"<li[^>]*>(.*?)</li>", ol, re.DOTALL)
        for li in lis:
            text = decode_entities(strip_tags(li)).strip()
            if text and len(text) > 3 and not text.startswith("^"):
                defs.append(text)

    # If all definitions look like inflection forms, follow to base word (once)
    if defs and _depth == 0:
        base = extract_base_word(defs[0])
        if base and base.lower() != word.lower():
            base_defs, _ = fetch_definitions(base, _depth=1)
            if base_defs:
                return base_defs[:6], base

    return defs[:6], None


for common, latin in sample:
    genus, epithet = latin.split()
    defs, followed_to = fetch_definitions(epithet)

    print(f"\n{'='*65}")
    print(f"  {common}  ({latin})")
    print(f"  Epithet: {epithet!r}", end="")
    if followed_to:
        print(f"  →  base word: {followed_to!r}", end="")
    print()
    if defs:
        for i, d in enumerate(defs, 1):
            print(f"    {i}. {d}")
    else:
        print("    (no entry)")

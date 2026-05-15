"""
Test Wiktionary API responses for bird species epithets.
Run with: python3 test_wiktionary.py

Tests two endpoints per word:
  1. REST summary API  → clean extract, but may be too brief
  2. MediaWiki action API (parse) → full page as HTML, we look for the definition list
"""

import urllib.request
import urllib.parse
import json
import re

BIRDS = [
    ("White-collared Monarch",  "Symposiachrus vidua",    "vidua"),
    ("Little Grebe",            "Tachybaptus ruficollis", "ruficollis"),
    ("Peregrine Falcon",        "Falco peregrinus",       "peregrinus"),
    ("Blue Tit",                "Cyanistes caeruleus",    "caeruleus"),
    ("Crested Lark",            "Galerida cristata",      "cristata"),
    ("Goldcrest",               "Regulus regulus",        "regulus"),
    ("Golden Eagle",            "Aquila chrysaetos",      "chrysaetos"),
    ("Common Raven",            "Corvus corax",           "corax"),
    ("Common Swift",            "Apus apus",              "apus"),
    ("Plum-throated Cotinga",   "Cotinga maynana",        "maynana"),
]

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


# ── Approach 1: REST summary ──────────────────────────────────────────────────
def summary_api(word):
    url = f"https://en.wiktionary.org/api/rest_v1/page/summary/{urllib.parse.quote(word)}"
    data = get(url)
    if "_http_error" in data:
        return None, f"HTTP {data['_http_error']}"
    if "_error" in data:
        return None, data["_error"]
    return data.get("description"), data.get("extract", "")[:400]


# ── Approach 2: MediaWiki action API, parsed HTML ─────────────────────────────
def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)

def action_api_definitions(word):
    """
    Fetches parsed HTML for the word's Wiktionary page and extracts the
    first <ol><li> items that appear after a Latin/New Latin section heading.
    Returns a list of plain-text definition strings, or [] if not found.
    """
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
        return []

    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return []

    # Find the Latin section (or New Latin / Translingual)
    # Strategy: split on h2/h3 headings, take the Latin block, then grab <ol><li>s
    # Wiktionary wraps each language in an <h2> heading.
    latin_section = ""
    for lang_keyword in ["Latin", "New Latin", "Translingual"]:
        # Look for the heading span
        pattern = rf'<h2[^>]*>.*?{lang_keyword}.*?</h2>(.*?)(?=<h2|$)'
        m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if m:
            latin_section = m.group(1)
            break

    if not latin_section:
        latin_section = html  # fall back to full page

    # Extract all <li> items from <ol> lists (definitions, not nav links)
    items = re.findall(r"<ol[^>]*>(.*?)</ol>", latin_section, re.DOTALL)
    defs = []
    for ol in items:
        lis = re.findall(r"<li[^>]*>(.*?)</li>", ol, re.DOTALL)
        for li in lis:
            text = strip_tags(li).strip()
            # Skip citation noise and very short fragments
            if text and len(text) > 3 and not text.startswith("^"):
                defs.append(text)
    return defs[:5]  # top 5 definitions at most


# ── Main ──────────────────────────────────────────────────────────────────────
for common, latin, epithet in BIRDS:
    print(f"\n{'='*65}")
    print(f"  {common}  ({latin})")
    print(f"  Epithet tested: {epithet!r}")

    desc, extract = summary_api(epithet)
    print(f"\n  [REST summary]")
    print(f"    description : {desc}")
    print(f"    extract     : {extract}")

    defs = action_api_definitions(epithet)
    print(f"\n  [Action API – definitions from Latin section]")
    if defs:
        for i, d in enumerate(defs, 1):
            print(f"    {i}. {d}")
    else:
        print(f"    (none found)")

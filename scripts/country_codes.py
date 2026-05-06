"""
country_codes.py
================
Lookup tables and a text-extraction helper for parsing geographic range
information from Wikipedia lead paragraphs.

Exports
-------
COUNTRY_TO_ISO : dict[str, str]
    Maps English country names (+ common variants) → ISO 3166-1 alpha-2 code.

REGION_TO_LABEL : dict[str, str]
    Maps continent / ocean / sea names → a normalised label string.

extract_geo(text) -> dict
    Parses the distribution sentence(s) from a Wikipedia lead paragraph and
    returns {"countries": [iso2, ...], "regions": [label, ...]}.
"""

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# Country → ISO alpha-2
# ---------------------------------------------------------------------------

COUNTRY_TO_ISO: dict[str, str] = {
    # A
    "Afghanistan": "AF",
    "Albania": "AL",
    "Algeria": "DZ",
    "Andorra": "AD",
    "Angola": "AO",
    "Antigua and Barbuda": "AG",
    "Argentina": "AR",
    "Armenia": "AM",
    "Australia": "AU",
    "Austria": "AT",
    "Azerbaijan": "AZ",
    # B
    "Bahamas": "BS",
    "Bahrain": "BH",
    "Bangladesh": "BD",
    "Barbados": "BB",
    "Belarus": "BY",
    "Belgium": "BE",
    "Belize": "BZ",
    "Benin": "BJ",
    "Bhutan": "BT",
    "Bolivia": "BO",
    "Bosnia": "BA",
    "Bosnia and Herzegovina": "BA",
    "Botswana": "BW",
    "Brazil": "BR",
    "Brunei": "BN",
    "Brunei Darussalam": "BN",
    "Bulgaria": "BG",
    "Burkina Faso": "BF",
    "Burundi": "BI",
    # C
    "Cabo Verde": "CV",
    "Cape Verde": "CV",
    "Cambodia": "KH",
    "Cameroon": "CM",
    "Canada": "CA",
    "Central African Republic": "CF",
    "Chad": "TD",
    "Chile": "CL",
    "China": "CN",
    "Colombia": "CO",
    "Comoros": "KM",
    "Congo": "CG",
    "Democratic Republic of the Congo": "CD",
    "DR Congo": "CD",
    "DRC": "CD",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Cuba": "CU",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    # D
    "Denmark": "DK",
    "Djibouti": "DJ",
    "Dominica": "DM",
    "Dominican Republic": "DO",
    # E
    "Ecuador": "EC",
    "Egypt": "EG",
    "El Salvador": "SV",
    "Equatorial Guinea": "GQ",
    "Eritrea": "ER",
    "Estonia": "EE",
    "Eswatini": "SZ",
    "Swaziland": "SZ",
    "Ethiopia": "ET",
    # F
    "Fiji": "FJ",
    "Finland": "FI",
    "France": "FR",
    # G
    "Gabon": "GA",
    "Gambia": "GM",
    "Georgia": "GE",
    "Germany": "DE",
    "Ghana": "GH",
    "Greece": "GR",
    "Grenada": "GD",
    "Guatemala": "GT",
    "Guinea": "GN",
    "Guinea-Bissau": "GW",
    "Guyana": "GY",
    # H
    "Haiti": "HT",
    "Honduras": "HN",
    "Hungary": "HU",
    # I
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Iran": "IR",
    "Iraq": "IQ",
    "Ireland": "IE",
    "Israel": "IL",
    "Italy": "IT",
    # J
    "Jamaica": "JM",
    "Japan": "JP",
    "Jordan": "JO",
    # K
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kiribati": "KI",
    "Kuwait": "KW",
    "Kyrgyzstan": "KG",
    # L
    "Laos": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Lesotho": "LS",
    "Liberia": "LR",
    "Libya": "LY",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    # M
    "Madagascar": "MG",
    "Malawi": "MW",
    "Malaysia": "MY",
    "Maldives": "MV",
    "Mali": "ML",
    "Malta": "MT",
    "Marshall Islands": "MH",
    "Mauritania": "MR",
    "Mauritius": "MU",
    "Mexico": "MX",
    "Micronesia": "FM",
    "Moldova": "MD",
    "Monaco": "MC",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Myanmar": "MM",
    "Burma": "MM",
    # N
    "Namibia": "NA",
    "Nauru": "NR",
    "Nepal": "NP",
    "Netherlands": "NL",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Niger": "NE",
    "Nigeria": "NG",
    "North Korea": "KP",
    "North Macedonia": "MK",
    "Macedonia": "MK",
    "Norway": "NO",
    # O
    "Oman": "OM",
    # P
    "Pakistan": "PK",
    "Palau": "PW",
    "Palestine": "PS",
    "Panama": "PA",
    "Papua New Guinea": "PG",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines": "PH",
    "Poland": "PL",
    "Portugal": "PT",
    # Q
    "Qatar": "QA",
    # R
    "Romania": "RO",
    "Russia": "RU",
    "Russian Federation": "RU",
    "Rwanda": "RW",
    # S
    "Saint Kitts and Nevis": "KN",
    "Saint Lucia": "LC",
    "Saint Vincent and the Grenadines": "VC",
    "Samoa": "WS",
    "San Marino": "SM",
    "Sao Tome and Principe": "ST",
    "São Tomé and Príncipe": "ST",
    "Saudi Arabia": "SA",
    "Senegal": "SN",
    "Serbia": "RS",
    "Seychelles": "SC",
    "Sierra Leone": "SL",
    "Singapore": "SG",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Solomon Islands": "SB",
    "Somalia": "SO",
    "South Africa": "ZA",
    "South Korea": "KR",
    "South Sudan": "SS",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Sudan": "SD",
    "Suriname": "SR",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syria": "SY",
    # T
    "Taiwan": "TW",
    "Tajikistan": "TJ",
    "Tanzania": "TZ",
    "Thailand": "TH",
    "Timor-Leste": "TL",
    "East Timor": "TL",
    "Togo": "TG",
    "Tonga": "TO",
    "Trinidad and Tobago": "TT",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Türkiye": "TR",
    "Turkmenistan": "TM",
    "Tuvalu": "TV",
    # U
    "Uganda": "UG",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "UAE": "AE",
    "United Kingdom": "GB",
    "UK": "GB",
    "Britain": "GB",
    "Great Britain": "GB",
    "England": "GB",
    "Scotland": "GB",
    "Wales": "GB",
    "United States": "US",
    "United States of America": "US",
    "USA": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    # V
    "Vanuatu": "VU",
    "Vatican City": "VA",
    "Venezuela": "VE",
    "Vietnam": "VN",
    "Viet Nam": "VN",
    # Y
    "Yemen": "YE",
    # Z
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
    # Common territories / islands that appear often in bird articles
    "Greenland": "GL",
    "Puerto Rico": "PR",
    "Faroe Islands": "FO",
    "Falkland Islands": "FK",
    "Galápagos": "EC",
    "Galapagos": "EC",
    "Galapagos Islands": "EC",
    "Canary Islands": "ES",
    "Azores": "PT",
    "Madeira": "PT",
    "New Caledonia": "NC",
    "French Polynesia": "PF",
    "Hawaii": "US",
    "Hawaiian Islands": "US",
    "Alaska": "US",
    "Bermuda": "BM",
    "Cuba": "CU",
    "Hispaniola": "HT",  # shared — pick Haiti as dominant code
    "Borneo": "MY",      # shared island — Malaysia as representative
    "Sumatra": "ID",
    "Java": "ID",
    "Sulawesi": "ID",
    "Celebes": "ID",
    "New Guinea": "PG",
    "Sri Lanka": "LK",
    "Ceylon": "LK",
    "Réunion": "RE",
    "Reunion": "RE",
    "Mayotte": "YT",
    "Comoro Islands": "KM",
    "Madagascar": "MG",
    "Zanzibar": "TZ",
    "Bioko": "GQ",
    "São Tomé": "ST",
    "Sao Tome": "ST",
    "Príncipe": "ST",
    "Principe": "ST",
    "Socotra": "YE",
    "Maldive Islands": "MV",
    "Andaman Islands": "IN",
    "Nicobar Islands": "IN",
    "Lakshadweep": "IN",
    "Seychelles Islands": "SC",
    "Ascension Island": "SH",
    "Saint Helena": "SH",
    "Tristan da Cunha": "SH",
    "Svalbard": "SJ",
    "Jan Mayen": "SJ",
    "Franz Josef Land": "RU",
    "Novaya Zemlya": "RU",
    "Kamchatka": "RU",
    "Sakhalin": "RU",
    "Hokkaido": "JP",
    "Honshu": "JP",
    "Ryukyu Islands": "JP",
    "Kyushu": "JP",
    "Shikoku": "JP",
}

# ---------------------------------------------------------------------------
# Region → normalised label  (continents, subcontinents, oceans, seas)
# ---------------------------------------------------------------------------

REGION_TO_LABEL: dict[str, str] = {
    # Continents / subcontinents
    "Africa": "Africa",
    "Sub-Saharan Africa": "Sub-Saharan Africa",
    "sub-Saharan Africa": "Sub-Saharan Africa",
    "West Africa": "West Africa",
    "East Africa": "East Africa",
    "Central Africa": "Central Africa",
    "Southern Africa": "Southern Africa",
    "North Africa": "North Africa",
    "Northern Africa": "North Africa",
    "Horn of Africa": "Horn of Africa",
    "Asia": "Asia",
    "South Asia": "South Asia",
    "Southeast Asia": "Southeast Asia",
    "East Asia": "East Asia",
    "Central Asia": "Central Asia",
    "Southwest Asia": "Southwest Asia",
    "Western Asia": "Western Asia",
    "Middle East": "Middle East",
    "Europe": "Europe",
    "Western Europe": "Western Europe",
    "Eastern Europe": "Eastern Europe",
    "Northern Europe": "Northern Europe",
    "Southern Europe": "Southern Europe",
    "Scandinavia": "Scandinavia",
    "Iberian Peninsula": "Iberian Peninsula",
    "Balkans": "Balkans",
    "North America": "North America",
    "Central America": "Central America",
    "South America": "South America",
    "Latin America": "Latin America",
    "Caribbean": "Caribbean",
    "Australasia": "Australasia",
    "Australia": "Australia",   # also a country — handled in COUNTRY_TO_ISO
    "Oceania": "Oceania",
    "Melanesia": "Melanesia",
    "Polynesia": "Polynesia",
    "Micronesia": "Micronesia",
    "Antarctica": "Antarctica",
    "Arctic": "Arctic",
    "Tropics": "Tropics",
    "tropics": "Tropics",
    "the tropics": "Tropics",
    # Oceans
    "Atlantic Ocean": "Atlantic Ocean",
    "Atlantic": "Atlantic Ocean",
    "North Atlantic": "North Atlantic Ocean",
    "North Atlantic Ocean": "North Atlantic Ocean",
    "South Atlantic": "South Atlantic Ocean",
    "South Atlantic Ocean": "South Atlantic Ocean",
    "Pacific Ocean": "Pacific Ocean",
    "Pacific": "Pacific Ocean",
    "North Pacific": "North Pacific Ocean",
    "North Pacific Ocean": "North Pacific Ocean",
    "South Pacific": "South Pacific Ocean",
    "South Pacific Ocean": "South Pacific Ocean",
    "Indian Ocean": "Indian Ocean",
    "Arctic Ocean": "Arctic Ocean",
    "Southern Ocean": "Southern Ocean",
    "Antarctic Ocean": "Southern Ocean",
    # Seas / bays / gulfs
    "Mediterranean Sea": "Mediterranean Sea",
    "Mediterranean": "Mediterranean Sea",
    "Red Sea": "Red Sea",
    "Arabian Sea": "Arabian Sea",
    "Bay of Bengal": "Bay of Bengal",
    "South China Sea": "South China Sea",
    "Caribbean Sea": "Caribbean Sea",
    "Gulf of Mexico": "Gulf of Mexico",
    "Gulf of Guinea": "Gulf of Guinea",
    "Coral Sea": "Coral Sea",
    "Tasman Sea": "Tasman Sea",
    "Bering Sea": "Bering Sea",
    "Sea of Japan": "Sea of Japan",
    "North Sea": "North Sea",
    "Baltic Sea": "Baltic Sea",
    "Black Sea": "Black Sea",
    "Caspian Sea": "Caspian Sea",
}

# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

# Sentence openers that indicate range/distribution
_RANGE_OPENERS = re.compile(
    r"\b(?:"
    r"(?:is|are)\s+(?:found|known|recorded|distributed|widespread|native|resident|common|endemic)\b"
    r"|(?:occurs?|range[sd]?|breed[sd]?|winter[sd]?|migrates?|inhabits?|lives?)\b"
    r"|(?:is|are)\s+endemic\s+to\b"
    r"|(?:native\s+to|found\s+in|occurring\s+in|distributed\s+(?:across|throughout|in))\b"
    r")",
    re.IGNORECASE,
)

# Build a single big alternation from the two dicts, longest first to prefer
# multi-word names over sub-strings (e.g. "South Africa" before "Africa").
def _build_geo_pattern() -> re.Pattern:
    all_names = sorted(
        list(COUNTRY_TO_ISO.keys()) + list(REGION_TO_LABEL.keys()),
        key=len,
        reverse=True,
    )
    escaped = [re.escape(n) for n in all_names]
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b")


_GEO_PATTERN = _build_geo_pattern()


def extract_geo(text: str) -> dict:
    """
    Parse geographic names from a Wikipedia lead-paragraph string.

    Returns
    -------
    {
        "countries": ["US", "CA", ...],   # ISO alpha-2 codes, deduped, ordered
        "regions":   ["North America", ...],  # region labels, deduped, ordered
    }
    """
    # Split into sentences; try to find ones that describe range
    sentences = re.split(r"(?<=[.!?])\s+", text)
    range_sentences: list[str] = []
    for sent in sentences:
        if _RANGE_OPENERS.search(sent):
            range_sentences.append(sent)

    # If no sentence matched, fall back to scanning the whole text
    corpus = " ".join(range_sentences) if range_sentences else text

    countries: list[str] = []
    regions: list[str] = []
    seen: set[str] = set()

    for match in _GEO_PATTERN.finditer(corpus):
        name = match.group(0)
        if name in COUNTRY_TO_ISO:
            iso = COUNTRY_TO_ISO[name]
            if iso not in seen:
                seen.add(iso)
                countries.append(iso)
        if name in REGION_TO_LABEL:
            label = REGION_TO_LABEL[name]
            if label not in seen:
                seen.add(label)
                regions.append(label)

    return {"countries": countries, "regions": regions}

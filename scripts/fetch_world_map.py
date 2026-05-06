"""
fetch_world_map.py
==================
Downloads Natural Earth 110m country GeoJSON (public domain) and converts
it to a compact SVG where every country <path> has id="XX" matching its
ISO 3166-1 alpha-2 code.

Output: src/assets/world-map.svg

Usage
-----
    python scripts/fetch_world_map.py

Requires: requests  (already a project dependency via scrape_species.py)
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Natural Earth 110m countries GeoJSON — public domain, ~300 KB
GEOJSON_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
)

# Fallback mirror (Natural Earth direct)
GEOJSON_FALLBACK = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)

OUT_PATH = Path(__file__).parent.parent / "src" / "assets" / "world-map.svg"
HEADERS = {"User-Agent": "daily-bird-scraper/1.0 (personal project)"}

# SVG canvas
W = 1010
H = 506

# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def lonlat_to_xy(lon: float, lat: float) -> tuple[float, float]:
    """Equirectangular projection: lon/lat -> SVG x/y."""
    x = (lon + 180.0) * (W / 360.0)
    y = (90.0 - lat) * (H / 180.0)
    return x, y


def ring_to_d(ring: list[list[float]]) -> str:
    """Convert a GeoJSON coordinate ring to an SVG path 'd' segment."""
    parts: list[str] = []
    for i, (lon, lat) in enumerate(ring):
        x, y = lonlat_to_xy(lon, lat)
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd}{x:.2f},{y:.2f}")
    parts.append("Z")
    return "".join(parts)


def geometry_to_d(geometry: dict) -> str:
    """Convert a GeoJSON geometry (Polygon or MultiPolygon) to 'd' string."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]

    if gtype == "Polygon":
        rings = coords  # list of rings; first is outer, rest are holes
        return "".join(ring_to_d(r) for r in rings)

    elif gtype == "MultiPolygon":
        # coords is list of polygons, each a list of rings
        parts: list[str] = []
        for polygon in coords:
            for ring in polygon:
                parts.append(ring_to_d(ring))
        return "".join(parts)

    return ""


# ---------------------------------------------------------------------------
# ISO code extraction
# ---------------------------------------------------------------------------

def get_iso2(props: dict) -> str | None:
    """Extract ISO alpha-2 from a feature's properties dict."""
    # datasets/geo-countries uses ISO_A2
    # nvkelso/natural-earth-vector uses ISO_A2 too
    for key in ("ISO_A2", "iso_a2", "ISO2", "iso2", "ADM0_A3"):
        val = props.get(key, "")
        if val and len(val) == 2 and val != "-1":
            return val.upper()
    # Some features have ISO_A3 only — skip those (we need alpha-2)
    return None


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_geojson() -> dict:
    for url in (GEOJSON_URL, GEOJSON_FALLBACK):
        try:
            print(f"Downloading {url} ...")
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
            print(f"  OK — {len(data['features'])} features")
            return data
        except Exception as exc:
            print(f"  Failed: {exc}")
    print("ERROR: could not download GeoJSON from either source.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Build SVG
# ---------------------------------------------------------------------------

def build_svg(geojson: dict) -> str:
    paths: list[str] = []
    skipped = 0

    for feature in geojson["features"]:
        props = feature.get("properties", {})
        geom = feature.get("geometry")
        if not geom:
            skipped += 1
            continue

        iso2 = get_iso2(props)
        if not iso2:
            skipped += 1
            continue

        d = geometry_to_d(geom)
        if not d:
            skipped += 1
            continue

        # Sanitise the ID (should already be 2 uppercase letters)
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "", iso2)
        paths.append(f'  <path id="{safe_id}" d="{d}"/>')

    if skipped:
        print(f"  Skipped {skipped} features (missing ISO-2 or geometry)")
    print(f"  Generated {len(paths)} country paths")

    inner = "\n".join(paths)
    return f"""\
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {W} {H}"
     data-source="Natural Earth (public domain), equirectangular projection">
  <style>
    path {{
      fill: #d1d5db;
      stroke: #ffffff;
      stroke-width: 0.4;
      stroke-linejoin: round;
    }}
    path.highlighted {{
      fill: #6b9e78;
    }}
  </style>
{inner}
</svg>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

geojson = download_geojson()
svg = build_svg(geojson)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(svg, encoding="utf-8")
print(f"Written to: {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB)")

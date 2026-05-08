import { useMemo } from 'react'
import worldMapRaw from '../assets/world-map.svg?raw'
import countryBboxes from '../data/country-bboxes.json'

// SVG canvas dimensions — must match generate_world_map.js
const SVG_W = 1010
const SVG_H = 506

function projX(lon) { return (lon + 180) * SVG_W / 360 }
function projY(lat) { return (90 - lat) * SVG_H / 180 }

/**
 * Given a list of ISO alpha-2 country codes, compute a zoomed SVG viewBox
 * string that tightly crops to the union of their bounding boxes, with padding.
 *
 * Returns null if no valid bboxes are found (falls back to full-world view).
 */
function computeViewBox(countries) {
  let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity
  let found = false

  for (const iso of countries) {
    const b = countryBboxes[iso]
    if (!b) continue               // null = antimeridian-straddling, skip
    found = true
    if (b[0] < minLon) minLon = b[0]
    if (b[1] < minLat) minLat = b[1]
    if (b[2] > maxLon) maxLon = b[2]
    if (b[3] > maxLat) maxLat = b[3]
  }

  if (!found) return null

  // Project to SVG space
  const x0 = projX(minLon)
  const x1 = projX(maxLon)
  const y0 = projY(maxLat)   // maxLat → smaller y (top)
  const y1 = projY(minLat)   // minLat → larger  y (bottom)

  const w = x1 - x0
  const h = y1 - y0

  // Padding: 25% of each dimension, minimum 20 SVG units (~7° lon/lat)
  const padX = Math.max(w * 0.25, 20)
  const padY = Math.max(h * 0.25, 20)

  // Enforce a minimum crop size so tiny islands aren't over-zoomed
  const minSize = 40
  const cropW = Math.max(w + 2 * padX, minSize)
  const cropH = Math.max(h + 2 * padY, minSize)

  // Centre the crop on the range centroid
  const cx = (x0 + x1) / 2
  const cy = (y0 + y1) / 2

  const vbX = Math.max(0,     cx - cropW / 2)
  const vbY = Math.max(0,     cy - cropH / 2)
  const vbW = Math.min(SVG_W - vbX, cropW)
  const vbH = Math.min(SVG_H - vbY, cropH)

  return `${vbX.toFixed(1)} ${vbY.toFixed(1)} ${vbW.toFixed(1)} ${vbH.toFixed(1)}`
}

/**
 * Inject highlight styles and a zoomed viewBox into the raw SVG string.
 */
function buildSvg(countries) {
  const selector = countries.map(iso => `#${iso}`).join(', ')
  const styleTag = countries.length
    ? `<style>${selector} { fill: #6b9e78; }</style>`
    : ''

  const viewBox = computeViewBox(countries)

  let svg = worldMapRaw
  if (styleTag) svg = svg.replace('</svg>', `${styleTag}</svg>`)
  if (viewBox)  svg = svg.replace(/viewBox="[^"]*"/, `viewBox="${viewBox}"`)
  // Make the SVG element itself fill its container
  svg = svg.replace('<svg ', '<svg width="100%" height="100%" ')

  return svg
}

// ---------------------------------------------------------------------------

/** Small watermark label shown in the bottom-right corner of each map. */
function Watermark({ label }) {
  return (
    <span className="absolute bottom-1.5 right-1.5 text-[9px] leading-none
                     bg-black/25 text-white/90 px-1.5 py-0.5 rounded
                     pointer-events-none select-none">
      {label}
    </span>
  )
}

export function RangeMapImage({ rangeMap, title }) {
  const { type, url, countries = [], mapSource } = rangeMap

  const builtSvg = useMemo(
    () => (type === 'svg' ? buildSvg(countries) : null),
    [type, countries],
  )

  // The parent cell is flex-1 so this div must fill it completely in both axes
  const base = 'relative w-full h-full overflow-hidden flex items-center justify-center bg-stone-100'

  // --- Wikipedia range map ---
  if (type === 'wiki' && url) {
    return (
      <div className={base}>
        <img
          src={url}
          alt={`Range map for ${title}`}
          className="w-full h-full object-contain"
          loading="lazy"
        />
        <Watermark label="from Wikimedia" />
      </div>
    )
  }

  // --- Auto-generated SVG with zoomed crop ---
  if (type === 'svg') {
    return (
      <div className="relative w-full h-full">
        <div
          className={base}
          aria-label={`Range map for ${title}`}
          dangerouslySetInnerHTML={{ __html: builtSvg }}
        />
        {mapSource === 'claude' && <Watermark label="drawn with Claude" />}
      </div>
    )
  }

  // --- No map available ---
  return (
    <div className={`${base} flex-col gap-1`}>
      <span className="text-2xl select-none opacity-30">🗺️</span>
      <span className="text-xs text-stone-400 text-center px-2 leading-tight">No range map</span>
    </div>
  )
}

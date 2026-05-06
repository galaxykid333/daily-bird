import { useMemo } from 'react'
import worldMapRaw from '../assets/world-map.svg?raw'

/**
 * RangeMapImage
 * -------------
 * Renders a range map thumbnail based on the entry from range_maps.json.
 *
 * Props:
 *   rangeMap  – object from useRangeMap(): { type, url?, countries[], regions[] }
 *   title     – species title, used for alt text
 *   className – extra classes applied to the outer wrapper
 */
export function RangeMapImage({ rangeMap, title, className = '' }) {
  const { type, url, countries = [] } = rangeMap

  // For SVG maps: inject a <style> block that highlights the relevant countries.
  // We do this by modifying the raw SVG string before setting innerHTML —
  // cheaper than cloning the DOM and far simpler than a ref + querySelectorAll.
  const highlightedSvg = useMemo(() => {
    if (type !== 'svg' || countries.length === 0) return worldMapRaw

    // Build a CSS rule that targets each country path by id
    const selector = countries.map((iso) => `#${iso}`).join(', ')
    const styleTag = `<style>${selector} { fill: #6b9e78; }</style>`

    // Insert just before </svg>
    return worldMapRaw.replace('</svg>', `${styleTag}</svg>`)
  }, [type, countries])

  const wrapperClass = `w-full h-full overflow-hidden flex items-center justify-center bg-stone-100 ${className}`

  // --- Wikipedia range map image ---
  if (type === 'wiki' && url) {
    return (
      <div className={wrapperClass}>
        <img
          src={url}
          alt={`Range map for ${title}`}
          className="w-full h-full object-contain"
          loading="lazy"
        />
      </div>
    )
  }

  // --- Auto-generated SVG world map with highlighted countries ---
  if (type === 'svg') {
    return (
      <div
        className={wrapperClass}
        aria-label={`Range map for ${title} (${countries.length} countr${countries.length === 1 ? 'y' : 'ies'} highlighted)`}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: highlightedSvg }}
      />
    )
  }

  // --- No map available: subtle placeholder ---
  return (
    <div className={`${wrapperClass} flex-col gap-1`}>
      <span className="text-2xl select-none opacity-40">🗺️</span>
      <span className="text-xs text-stone-400 text-center px-2">No range map</span>
    </div>
  )
}

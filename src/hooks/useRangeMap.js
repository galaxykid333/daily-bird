import rangeData from '../data/range_maps.json'

/**
 * Returns the pre-built range map entry for a species title.
 *
 * Return shape:
 *   { type: 'wiki',  url: '...', countries: [...], regions: [...] }
 *   { type: 'svg',   countries: [...], regions: [...] }
 *   { type: 'none',  countries: [],    regions: [...] }
 *
 * Topics and unknown titles always return { type: 'none', countries: [], regions: [] }.
 */
export function useRangeMap(title, cardType) {
  if (cardType !== 'species' || !title) {
    return { type: 'none', countries: [], regions: [] }
  }
  return rangeData[title] ?? { type: 'none', countries: [], regions: [] }
}

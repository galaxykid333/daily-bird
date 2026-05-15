import { useState, useEffect } from 'react'

const cache = new Map()

/** Fetch the species page HTML and extract the genus Wikipedia title from
 *  the biota infobox Genus row — avoids disambiguation pages entirely. */
async function fetchGenusTitle(speciesName) {
  const params = new URLSearchParams({
    action: 'parse',
    page: speciesName.replace(/ /g, '_'),
    prop: 'text',
    format: 'json',
    redirects: '1',
    origin: '*',
  })
  const res = await fetch(`https://en.wikipedia.org/w/api.php?${params}`)
  const data = await res.json()
  if (data.error) return null

  const html = data?.parse?.text?.['*'] ?? ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const biota = doc.querySelector('table.biota')
  if (!biota) return null

  for (const row of biota.querySelectorAll('tr')) {
    const tds = row.querySelectorAll('td')
    if (tds.length >= 2 && tds[0].textContent.trim() === 'Genus:') {
      const link = tds[1].querySelector('a')
      const href = link?.getAttribute('href') ?? ''
      const m = href.match(/^\/wiki\/(.+)$/)
      if (m) return decodeURIComponent(m[1]).replace(/_/g, ' ')
    }
  }
  return null
}

async function fetchSummary(title) {
  const encoded = encodeURIComponent(title.replace(/ /g, '_'))
  const res = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encoded}`)
  if (!res.ok) return null
  return res.json()
}

/**
 * Given a species common name, finds the correct genus Wikipedia page
 * (via the species page's infobox), then fetches its summary.
 *
 * Returns { genusWikiTitle, extract, loading }
 */
export function useGenusSummary(speciesName, fallbackGenus) {
  const [state, setState] = useState({ genusWikiTitle: null, extract: null, loading: true })

  useEffect(() => {
    if (!speciesName) return
    if (cache.has(speciesName)) {
      setState({ ...cache.get(speciesName), loading: false })
      return
    }

    let cancelled = false
    setState((s) => ({ ...s, loading: true }))

    ;(async () => {
      const genusTitle = (await fetchGenusTitle(speciesName)) ?? fallbackGenus
      const summary = genusTitle ? await fetchSummary(genusTitle) : null
      if (cancelled) return
      const result = {
        genusWikiTitle: genusTitle,
        extract: summary?.extract ?? null,
      }
      cache.set(speciesName, result)
      setState({ ...result, loading: false })
    })()

    return () => { cancelled = true }
  }, [speciesName, fallbackGenus])

  return state
}

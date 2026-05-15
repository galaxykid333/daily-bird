import { useState, useEffect, useRef, useCallback } from 'react'
import { useGenusSummary } from '../hooks/useGenusSummary'

// ── Wiktionary helpers ────────────────────────────────────────────────────────

const MACRON_MAP = { ā:'a',ē:'e',ī:'i',ō:'o',ū:'u',ȳ:'y',Ā:'A',Ē:'E',Ī:'I',Ō:'O',Ū:'U',Ȳ:'Y' }
const stripMacrons = (w) => w.split('').map((c) => MACRON_MAP[c] ?? c).join('')

const INFLECTION_RES = [
  /^inflection of ([^\s:,;(]+)/i,
  /\bsingular of ([^\s:,;(]+)/i,
  /\bplural of ([^\s:,;(]+)/i,
  /^alternative (?:letter-case )?form of ([^\s:,;(]+)/i,
  /^(?:first|second|third)-person .+ of ([^\s:,;(]+)/i,
  /^(?:present|past|perfect|active|passive) .+ of ([^\s:,;(]+)/i,
]

function extractBaseWord(text) {
  for (const re of INFLECTION_RES) {
    const m = text.match(re)
    if (m) return stripMacrons(m[1].replace(/[.:,]$/, ''))
  }
  return null
}

const stripTags     = (html) => html.replace(/<[^>]+>/g, '')
const decodeEntities = (t) =>
  t.replace(/&#32;/g,' ').replace(/&#91;/g,'[').replace(/&#93;/g,']')
   .replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#160;/g,' ')

const wiktionaryCache = new Map()

async function fetchWiktionaryDef(word, depth = 0) {
  const cacheKey = word.toLowerCase()
  if (depth === 0 && wiktionaryCache.has(cacheKey)) return wiktionaryCache.get(cacheKey)

  const params = new URLSearchParams({
    action: 'parse', page: word, prop: 'text',
    format: 'json', redirects: '1', origin: '*',
  })
  let data
  try {
    const res = await fetch(`https://en.wiktionary.org/w/api.php?${params}`)
    data = await res.json()
  } catch {
    return { def: null, base: null }
  }
  if (data.error) return { def: null, base: null }

  const html = data?.parse?.text?.['*'] ?? ''
  let section = ''
  for (const lang of ['Latin', 'New Latin', 'Translingual']) {
    const m = html.match(new RegExp(`<h2[^>]*>.*?${lang}.*?<\\/h2>(.*?)(?=<h2|$)`, 's'))
    if (m) { section = m[1]; break }
  }
  if (!section) section = html

  const defs = []
  for (const ol of (section.match(/<ol[^>]*>.*?<\/ol>/gs) ?? [])) {
    for (const li of (ol.match(/<li[^>]*>.*?<\/li>/gs) ?? [])) {
      const text = decodeEntities(stripTags(li)).trim()
      if (text && text.length > 3 && !text.startsWith('^')) defs.push(text)
    }
  }

  if (defs.length > 0 && depth === 0) {
    const base = extractBaseWord(defs[0])
    if (base && base.toLowerCase() !== word.toLowerCase()) {
      const result = await fetchWiktionaryDef(base, 1)
      if (result.def) {
        const out = { def: result.def, base }
        wiktionaryCache.set(cacheKey, out)
        return out
      }
    }
  }

  const firstDef = (defs[0] ?? '').split('\n')[0].trim() || null
  const out = { def: firstDef, base: null }
  if (depth === 0) wiktionaryCache.set(cacheKey, out)
  return out
}

// ── FloatingPanel ─────────────────────────────────────────────────────────────

function FloatingPanel({ anchorEl, onMouseEnter, onMouseLeave, children }) {
  const [style, setStyle] = useState({ position: 'fixed', visibility: 'hidden' })

  useEffect(() => {
    if (!anchorEl) return
    const rect = anchorEl.getBoundingClientRect()
    const above = rect.top > 120
    setStyle({
      position: 'fixed',
      visibility: 'visible',
      left: Math.min(rect.left + rect.width / 2, window.innerWidth - 220),
      top: above ? rect.top - 8 : rect.bottom + 8,
      transform: above ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
      zIndex: 9999,
    })
  }, [anchorEl])

  if (!anchorEl) return null

  return (
    <div
      style={style}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="w-52 bg-white border border-stone-200 rounded-xl shadow-lg p-3 text-xs text-stone-700 leading-relaxed"
    >
      {children}
    </div>
  )
}

// ── GenusToken ────────────────────────────────────────────────────────────────

function GenusToken({ genus, genusSummary, genusWikiTitle }) {
  const [anchor, setAnchor] = useState(null)
  const ref = useRef(null)
  const leaveTimer = useRef(null)

  const show = () => { clearTimeout(leaveTimer.current); setAnchor(ref.current) }
  const hide = () => { leaveTimer.current = setTimeout(() => setAnchor(null), 150) }

  const wikiUrl = `https://en.wikipedia.org/wiki/${encodeURIComponent((genusWikiTitle ?? genus).replace(/ /g, '_'))}`

  return (
    <>
      <span
        ref={ref}
        onMouseEnter={show}
        onMouseLeave={hide}
        className="cursor-help underline decoration-dotted decoration-stone-300 underline-offset-2"
      >
        {genus}
      </span>
      <FloatingPanel anchorEl={anchor} onMouseEnter={show} onMouseLeave={hide}>
        {genusSummary
          ? <p className="mb-2">{genusSummary}</p>
          : <p className="mb-2 text-stone-400 italic">Loading…</p>}
        <a href={wikiUrl} target="_blank" rel="noopener noreferrer"
          className="text-emerald-700 hover:underline font-medium">
          Wikipedia →
        </a>
      </FloatingPanel>
    </>
  )
}

// ── EpithetToken ──────────────────────────────────────────────────────────────

function EpithetToken({ epithet }) {
  const [anchor, setAnchor] = useState(null)
  const [result, setResult] = useState(null)
  const ref = useRef(null)
  const leaveTimer = useRef(null)

  const show = useCallback(async () => {
    clearTimeout(leaveTimer.current)
    setAnchor(ref.current)
    if (result === null) {
      setResult('loading')
      const out = await fetchWiktionaryDef(epithet)
      setResult(out)
    }
  }, [epithet, result])

  const hide = () => { leaveTimer.current = setTimeout(() => setAnchor(null), 150) }

  const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(epithet + ' latin')}`

  return (
    <>
      <span
        ref={ref}
        onMouseEnter={show}
        onMouseLeave={hide}
        className="cursor-help underline decoration-dotted decoration-stone-300 underline-offset-2"
      >
        {epithet}
      </span>
      <FloatingPanel anchorEl={anchor} onMouseEnter={show} onMouseLeave={hide}>
        {result === 'loading' && (
          <p className="mb-2 text-stone-400 italic">Looking up…</p>
        )}
        {result && result !== 'loading' && result.def && (
          <p className="mb-2">
            {result.base && (
              <span className="text-stone-400 text-[10px] block mb-0.5">from <em>{result.base}</em></span>
            )}
            {result.def}
          </p>
        )}
        {result && result !== 'loading' && !result.def && (
          <p className="mb-2 text-stone-400 italic">No Latin entry found.</p>
        )}
        <a href={googleUrl} target="_blank" rel="noopener noreferrer"
          className="text-emerald-700 hover:underline font-medium">
          Search '<em>{epithet}</em>' in Latin →
        </a>
      </FloatingPanel>
    </>
  )
}

// ── LatinName (exported) ──────────────────────────────────────────────────────

/**
 * Renders the scientific name with hover tooltips for genus and epithet.
 * @param {string} title      - Wikipedia page title of the species (for genus lookup)
 * @param {string} latinName  - Full binomial e.g. "Himantopus mexicanus"
 */
export function LatinName({ title, latinName }) {
  const [genus, epithet] = latinName.split(' ')
  const { genusWikiTitle, extract: genusExtract } = useGenusSummary(title, genus)

  const firstSentence = (text) => {
    if (!text) return null
    const end = text.indexOf('. ')
    return end === -1 ? text : text.slice(0, end + 1)
  }

  const genusSummary = genusExtract ? firstSentence(genusExtract) : null
  const genusLine = genusSummary
    ? (genusWikiTitle && genusWikiTitle !== genus ? `${genus} — ${genusSummary}` : genusSummary)
    : null

  return (
    <span className="text-sm text-stone-400 italic leading-snug">
      <GenusToken genus={genus} genusSummary={genusLine} genusWikiTitle={genusWikiTitle} />
      {' '}
      <EpithetToken epithet={epithet} />
    </span>
  )
}

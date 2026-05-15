import { useState, useEffect, useRef, useCallback } from 'react'
import { useWikiSummary } from './hooks/useWikiSummary'
import { useGenusSummary } from './hooks/useGenusSummary'
import speciesData from './data/species.json'
import latinNames from './data/latin-names.json'
import ebirdMap from './data/ebird.json'

// ── Data helpers ──────────────────────────────────────────────────────────────

const SPECIES_WITH_LATIN = speciesData.filter((s) => latinNames[s])

function randomBird() {
  const i = Math.floor(Math.random() * SPECIES_WITH_LATIN.length)
  const name = SPECIES_WITH_LATIN[i]
  return { name, latin: latinNames[name] }
}

function firstSentence(text) {
  if (!text) return ''
  const end = text.indexOf('. ')
  return end === -1 ? text : text.slice(0, end + 1)
}

function trimExtract(extract, maxChars = 480) {
  if (!extract) return ''
  const parts = extract.split('. ')
  let text = parts.slice(0, 5).join('. ')
  if (!text.endsWith('.')) text += '.'
  return text.length > maxChars ? text.slice(0, maxChars).replace(/\s\S+$/, '') + '…' : text
}

// ── Wiktionary ────────────────────────────────────────────────────────────────

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

const stripTags = (html) => html.replace(/<[^>]+>/g, '')
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

  // Find Latin / New Latin / Translingual section
  let section = ''
  for (const lang of ['Latin', 'New Latin', 'Translingual']) {
    const m = html.match(new RegExp(`<h2[^>]*>.*?${lang}.*?<\\/h2>(.*?)(?=<h2|$)`, 's'))
    if (m) { section = m[1]; break }
  }
  if (!section) section = html

  // Pull definitions from <ol><li>
  const defs = []
  for (const ol of (section.match(/<ol[^>]*>.*?<\/ol>/gs) ?? [])) {
    for (const li of (ol.match(/<li[^>]*>.*?<\/li>/gs) ?? [])) {
      const text = decodeEntities(stripTags(li)).trim()
      if (text && text.length > 3 && !text.startsWith('^')) defs.push(text)
    }
  }

  // Inflection fallback — follow to base word once
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
    // Place above the word; flip below if too close to top
    const spaceAbove = rect.top
    const above = spaceAbove > 120
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
        className="italic text-stone-400 cursor-help underline decoration-dotted decoration-stone-300 underline-offset-2"
      >
        {genus}
      </span>
      <FloatingPanel anchorEl={anchor} onMouseEnter={show} onMouseLeave={hide}>
        {genusSummary
          ? <p className="mb-2">{firstSentence(genusSummary)}</p>
          : <p className="mb-2 text-stone-400 italic">Loading…</p>}
        <a
          href={wikiUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-emerald-700 hover:underline font-medium"
        >
          Wikipedia →
        </a>
      </FloatingPanel>
    </>
  )
}

// ── EpithetToken ──────────────────────────────────────────────────────────────

function EpithetToken({ epithet }) {
  const [anchor, setAnchor] = useState(null)
  const [result, setResult] = useState(null)   // { def, base } | 'loading' | 'done'
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
        className="italic text-stone-400 cursor-help underline decoration-dotted decoration-stone-300 underline-offset-2"
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
              <span className="text-stone-400 text-[10px] block mb-0.5">
                from <em>{result.base}</em>
              </span>
            )}
            {result.def}
          </p>
        )}
        {result && result !== 'loading' && !result.def && (
          <p className="mb-2 text-stone-400 italic">No Latin entry found.</p>
        )}
        <a
          href={googleUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-emerald-700 hover:underline font-medium"
        >
          Search '<em>{epithet}</em>' in Latin →
        </a>
      </FloatingPanel>
    </>
  )
}

// ── TestBirdCard ──────────────────────────────────────────────────────────────

function TestBirdCard({ name, latin }) {
  const [genus, epithet] = latin.split(' ')

  const { data: speciesData } = useWikiSummary(name)
  const { genusWikiTitle, extract: genusExtract } = useGenusSummary(name, genus)

  const extract   = trimExtract(speciesData?.extract)
  const genusSummary = genusExtract ? firstSentence(genusExtract) : null
  // If the genus wiki page title differs from the genus name (e.g. "Icterus (bird)" vs "Icterus"),
  // prefix with the genus name so it reads: "Icterus — the genus of the New World orioles"
  const genusLine = genusSummary
    ? (genusWikiTitle && genusWikiTitle !== genus ? `${genus} — ${genusSummary}` : genusSummary)
    : null

  const wikiUrl = speciesData?.content_urls?.desktop?.page
    ?? `https://en.wikipedia.org/wiki/${encodeURIComponent(name.replace(/ /g, '_'))}`
  const ebirdCode = ebirdMap[name]

  return (
    <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden p-6 max-w-lg">

      {/* Common name */}
      <h2 className="font-serif text-xl font-semibold text-stone-800 leading-snug">
        {name}
      </h2>

      {/* Latin name — genus + epithet each hoverable */}
      <div className="mt-0.5 text-sm">
        <GenusToken genus={genus} genusSummary={genusLine} genusWikiTitle={genusWikiTitle} />
        {' '}
        <EpithetToken epithet={epithet} />
      </div>

      {/* Species extract */}
      <p className="mt-3 text-sm text-stone-500 leading-relaxed">
        {extract || <span className="text-stone-300 italic">Loading…</span>}
      </p>

      {/* Footer links */}
      <div className="mt-4 pt-3 border-t border-stone-100 flex gap-3">
        <a href={wikiUrl} target="_blank" rel="noopener noreferrer"
          className="text-xs font-medium text-emerald-700 hover:underline">
          Wikipedia →
        </a>
        {ebirdCode && (
          <a href={`https://ebird.org/species/${ebirdCode}`} target="_blank" rel="noopener noreferrer"
            className="text-xs font-medium text-sky-600 hover:underline">
            eBird →
          </a>
        )}
      </div>
    </article>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function TestCardPage() {
  const [bird, setBird] = useState(() => randomBird())

  return (
    <div className="min-h-screen bg-stone-50 font-sans flex flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <p className="text-xs font-medium text-stone-400 uppercase tracking-widest mb-1">
          Latin name test
        </p>
        <p className="text-xs text-stone-300">
          Hover over the genus and epithet to test the tooltips
        </p>
      </div>

      <TestBirdCard key={bird.name} name={bird.name} latin={bird.latin} />

      <button
        onClick={() => setBird(randomBird())}
        className="bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-medium px-5 py-2.5 rounded-full shadow-sm transition-colors"
      >
        New bird →
      </button>
    </div>
  )
}

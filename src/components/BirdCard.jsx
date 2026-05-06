import { useWikiSummary } from '../hooks/useWikiSummary'
import { useRangeMap } from '../hooks/useRangeMap'
import { RangeMapImage } from './RangeMapImage'
import ebirdMap from '../data/ebird.json'

/**
 * Try to pull the binomial/Latin name from the opening sentence.
 * Wikipedia leads look like: "The Barn owl (Tyto alba) is a species of..."
 * We match the first "(CapWord lowerword)" near the start of the text.
 */
function extractLatinName(extract) {
  if (!extract) return null
  const m = extract.slice(0, 300).match(/\(([A-Z][a-z]+(?: [a-z]+)+)\)/)
  return m ? m[1] : null
}

/**
 * Trim the extract to a target line-count by sentence.
 * Returns the first `n` sentences joined, hard-capped at `maxChars`.
 */
function trimExtract(extract, sentences = 5, maxChars = 480) {
  if (!extract) return ''
  const parts = extract.split('. ')
  let text = parts.slice(0, sentences).join('. ')
  if (!text.endsWith('.')) text += '.'
  return text.length > maxChars ? text.slice(0, maxChars).replace(/\s\S+$/, '') + '…' : text
}

// ─────────────────────────────────────────────────────────────────────────────

export function BirdCard({ title, type, isSaved, onToggleSave }) {
  const { data, loading, error } = useWikiSummary(title)
  const rangeMap = useRangeMap(title, type)

  const latinName = extractLatinName(data?.extract)
  const extract   = trimExtract(data?.extract)

  const wikiUrl =
    data?.content_urls?.desktop?.page ??
    `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`

  // ── Topic card — text only, no images ─────────────────────────────────────
  if (type === 'topic') {
    return (
      <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden transition-shadow hover:shadow-md">
        <div className="flex flex-col p-5 gap-2">
          <span className="self-start text-xs font-medium px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
            Topic
          </span>

          <h2 className="font-serif text-lg font-semibold text-stone-800 leading-snug">
            {loading
              ? <span className="block h-6 bg-stone-100 rounded animate-pulse w-2/3" />
              : data?.title ?? title}
          </h2>

          <p className="text-sm text-stone-500 leading-relaxed line-clamp-5">
            {loading ? (
              <>
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2 w-5/6" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse w-4/6" />
              </>
            ) : error ? (
              <span className="text-red-400">Could not load summary.</span>
            ) : extract}
          </p>

          <div className="flex items-center justify-between pt-2 border-t border-stone-50 mt-1">
            <a
              href={wikiUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline transition-colors"
            >
              Wikipedia →
            </a>
            <button
              onClick={() => onToggleSave(title)}
              aria-label={isSaved ? 'Remove from saved' : 'Save'}
              className={`text-xl transition-transform hover:scale-125 active:scale-110 ${
                isSaved ? 'text-rose-500' : 'text-stone-300 hover:text-rose-400'
              }`}
            >
              {isSaved ? '♥' : '♡'}
            </button>
          </div>
        </div>
      </article>
    )
  }

  // ── Species card — horizontal strip with image + range map gallery ─────────
  return (
    <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden transition-shadow hover:shadow-md">
      <div className="flex flex-col sm:flex-row">

        {/* Text column */}
        <div className="flex flex-col flex-1 p-5 gap-2 min-w-0">

          <div className="flex items-baseline gap-2 flex-wrap">
            <h2 className="font-serif text-lg font-semibold text-stone-800 leading-snug">
              {loading
                ? <span className="block h-6 bg-stone-100 rounded animate-pulse w-2/3" />
                : data?.title ?? title}
            </h2>
            {!loading && latinName && (
              <span className="text-sm text-stone-400 italic leading-snug shrink-0">
                {latinName}
              </span>
            )}
          </div>

          <p className="text-sm text-stone-500 leading-relaxed line-clamp-5 flex-1">
            {loading ? (
              <>
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2 w-5/6" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2 w-4/6" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse w-3/5" />
              </>
            ) : error ? (
              <span className="text-red-400">Could not load summary.</span>
            ) : extract}
          </p>

          <div className="flex items-center justify-between pt-2 border-t border-stone-50 mt-auto">
            <div className="flex items-center gap-2">
              <a
                href={wikiUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline transition-colors"
              >
                Wikipedia →
              </a>
              {ebirdMap[title] && (
                <a
                  href={`https://ebird.org/species/${ebirdMap[title]}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-sky-600 hover:text-sky-800 hover:underline transition-colors"
                >
                  eBird →
                </a>
              )}
            </div>
            <button
              onClick={() => onToggleSave(title)}
              aria-label={isSaved ? 'Remove from saved' : 'Save'}
              title={isSaved ? 'Remove from saved' : 'Save'}
              className={`text-xl transition-transform hover:scale-125 active:scale-110 ${
                isSaved ? 'text-rose-500' : 'text-stone-300 hover:text-rose-400'
              }`}
            >
              {isSaved ? '♥' : '♡'}
            </button>
          </div>
        </div>

        {/* Image gallery: bird photo + range map, always side by side, fills card height */}
        <div className="flex flex-row self-stretch w-full sm:w-52 shrink-0 border-t sm:border-t-0 sm:border-l border-stone-100">

          {/* Bird photo */}
          <div className="flex-1 min-h-[120px] sm:min-h-0 overflow-hidden bg-stone-100 flex items-center justify-center border-r border-stone-100">
            {loading ? (
              <div className="w-full h-full animate-pulse bg-stone-100" />
            ) : data?.thumbnail?.source ? (
              <img
                src={data.thumbnail.source}
                alt={title}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-4xl select-none opacity-30">🐦</span>
            )}
          </div>

          {/* Range map */}
          <div className="flex-1 min-h-[120px] sm:min-h-0">
            <RangeMapImage rangeMap={rangeMap} title={title} />
          </div>

        </div>
      </div>
    </article>
  )
}

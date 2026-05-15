import { useWikiSummary } from '../hooks/useWikiSummary'
import { useRangeMap } from '../hooks/useRangeMap'
import { RangeMapImage } from './RangeMapImage'
import ebirdMap from '../data/ebird.json'
import latinNames from '../data/latin-names.json'

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

  const latinName = latinNames[title] ?? null
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

  // ── Species card — stacked on mobile, horizontal strip on desktop ────────────
  return (
    <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden transition-shadow hover:shadow-md sm:h-[350px]">
      <div className="flex flex-col sm:flex-row h-full">

        {/* Text column — full width on mobile, 40% on desktop */}
        <div className="flex flex-col w-full sm:w-[40%] p-5 gap-2 min-w-0 border-b sm:border-b-0 sm:border-r border-stone-100">

          <div className="flex flex-col gap-0.5">
            <h2 className="font-serif text-lg font-semibold text-stone-800 leading-snug">
              {loading
                ? <span className="block h-6 bg-stone-100 rounded animate-pulse w-2/3" />
                : data?.title ?? title}
            </h2>
            {!loading && latinName && (
              <span className="text-sm text-stone-400 italic leading-snug">
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

        {/* Image panel — full width / 200px tall on mobile, 60% width / full height on desktop */}
        <div className="flex w-full h-[200px] sm:w-[60%] sm:h-full">

          {/* Bird photo — fills cell, cropped to fit (object-cover) */}
          <div className="w-1/2 h-full overflow-hidden bg-stone-100 border-r border-stone-100">
            {loading ? (
              <div className="w-full h-full animate-pulse bg-stone-200" />
            ) : data?.thumbnail?.source ? (
              <img
                src={data.thumbnail.source}
                alt={title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-4xl select-none opacity-30">🐦</span>
              </div>
            )}
          </div>

          {/* Range map — fills remaining half */}
          <div className="w-1/2 h-full">
            <RangeMapImage rangeMap={rangeMap} title={title} />
          </div>

        </div>
      </div>
    </article>
  )
}

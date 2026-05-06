import { useWikiSummary } from '../hooks/useWikiSummary'
import { useRangeMap } from '../hooks/useRangeMap'
import { RangeMapImage } from './RangeMapImage'
import ebirdMap from '../data/ebird.json'

export function BirdCard({ title, type, isSaved, onToggleSave }) {
  const { data, loading, error } = useWikiSummary(title)
  const rangeMap = useRangeMap(title, type)

  const extract = data?.extract?.split('. ').slice(0, 3).join('. ') + (data?.extract ? '.' : '')

  return (
    <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden transition-shadow hover:shadow-md">
      {/*
        Layout:
          desktop → [text left | bird photo + range map right]  (flex-row)
          mobile  → [text top  | images below as 2-col row]     (flex-col)
      */}
      <div className="flex flex-col sm:flex-row">

        {/* ── Left / top: text column ─────────────────────────────── */}
        <div className="flex flex-col flex-1 p-5 gap-3 min-w-0">

          {/* Type badge */}
          <span
            className={`self-start text-xs font-medium px-2 py-0.5 rounded-full ${
              type === 'species'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-amber-50 text-amber-700'
            }`}
          >
            {type === 'species' ? 'Species' : 'Topic'}
          </span>

          {/* Title */}
          <h2 className="font-serif text-lg font-semibold text-stone-800 leading-snug">
            {loading ? (
              <span className="block h-6 bg-stone-100 rounded animate-pulse w-3/4" />
            ) : (
              data?.title ?? title
            )}
          </h2>

          {/* Extract */}
          <p className="text-sm text-stone-500 leading-relaxed flex-1">
            {loading ? (
              <>
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse mb-2 w-5/6" />
                <span className="block h-4 bg-stone-100 rounded animate-pulse w-4/6" />
              </>
            ) : error ? (
              <span className="text-red-400">Could not load summary.</span>
            ) : (
              extract
            )}
          </p>

          {/* Actions: links + save button */}
          <div className="flex items-center justify-between pt-2 border-t border-stone-50 mt-auto">
            <div className="flex items-center gap-2">
              <a
                href={
                  data?.content_urls?.desktop?.page ??
                  `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`
                }
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

        {/* ── Right / bottom: two image thumbnails ────────────────── */}
        <div className="flex flex-row sm:flex-col w-full sm:w-44 shrink-0 border-t sm:border-t-0 sm:border-l border-stone-100">

          {/* Bird photo — left on mobile, top on desktop */}
          <div className="w-1/2 sm:w-full h-32 sm:h-36 overflow-hidden bg-stone-100 flex items-center justify-center border-r sm:border-r-0 sm:border-b border-stone-100">
            {loading ? (
              <div className="w-full h-full bg-stone-100 animate-pulse" />
            ) : data?.thumbnail?.source ? (
              <img
                src={data.thumbnail.source}
                alt={title}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-4xl select-none opacity-40">🐦</span>
            )}
          </div>

          {/* Range map — right on mobile, bottom on desktop */}
          <div className="w-1/2 sm:w-full h-32 sm:h-36">
            <RangeMapImage rangeMap={rangeMap} title={title} />
          </div>

        </div>
      </div>
    </article>
  )
}

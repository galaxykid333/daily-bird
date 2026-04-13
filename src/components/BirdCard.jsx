import { useWikiSummary } from '../hooks/useWikiSummary'

const PLACEHOLDER = (
  <div className="w-full h-48 bg-stone-100 flex items-center justify-center rounded-t-2xl">
    <span className="text-5xl select-none">🐦</span>
  </div>
)

export function BirdCard({ title, type, isSaved, onToggleSave }) {
  const { data, loading, error } = useWikiSummary(title)

  return (
    <article className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden flex flex-col transition-shadow hover:shadow-md">
      {/* Image */}
      {loading ? (
        <div className="w-full h-48 bg-stone-100 animate-pulse rounded-t-2xl" />
      ) : data?.thumbnail?.source ? (
        <img
          src={data.thumbnail.source}
          alt={title}
          className="w-full h-48 object-cover"
        />
      ) : (
        PLACEHOLDER
      )}

      {/* Body */}
      <div className="flex flex-col flex-1 p-5 gap-3">
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
            data?.extract?.split('. ').slice(0, 3).join('. ') + (data?.extract ? '.' : '')
          )}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-stone-50">
          <a
            href={data?.content_urls?.desktop?.page ?? `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline transition-colors"
          >
            Read on Wikipedia →
          </a>
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
    </article>
  )
}

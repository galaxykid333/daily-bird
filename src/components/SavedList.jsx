import { useWikiSummary } from '../hooks/useWikiSummary'

function SavedItem({ title, onRemove }) {
  const { data, loading } = useWikiSummary(title)

  return (
    <li className="flex items-center gap-3 py-3 border-b border-stone-100 last:border-0">
      {loading ? (
        <div className="w-12 h-12 rounded-lg bg-stone-100 animate-pulse flex-shrink-0" />
      ) : data?.thumbnail?.source ? (
        <img
          src={data.thumbnail.source}
          alt={title}
          className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-12 h-12 rounded-lg bg-stone-100 flex items-center justify-center flex-shrink-0 text-xl">
          🐦
        </div>
      )}

      <div className="flex-1 min-w-0">
        <p className="font-medium text-stone-800 text-sm truncate">{data?.title ?? title}</p>
        <a
          href={data?.content_urls?.desktop?.page ?? `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-emerald-700 hover:underline"
        >
          Wikipedia →
        </a>
      </div>

      <button
        onClick={() => onRemove(title)}
        aria-label="Remove"
        className="text-stone-300 hover:text-rose-400 transition-colors text-lg flex-shrink-0"
        title="Remove"
      >
        ×
      </button>
    </li>
  )
}

export function SavedList({ saved, onRemove, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <aside className="relative z-10 w-full max-w-sm h-full bg-white shadow-2xl flex flex-col">
        <header className="flex items-center justify-between px-5 py-4 border-b border-stone-100">
          <h2 className="font-serif text-lg font-semibold text-stone-800">
            Saved birds
          </h2>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-stone-700 text-2xl leading-none transition-colors"
            aria-label="Close"
          >
            ×
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5">
          {saved.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-stone-400 text-sm gap-2">
              <span className="text-4xl">🪺</span>
              <p>No saved birds yet.</p>
              <p className="text-xs">Tap ♡ on a card to save it.</p>
            </div>
          ) : (
            <ul>
              {saved.map((title) => (
                <SavedItem key={title} title={title} onRemove={onRemove} />
              ))}
            </ul>
          )}
        </div>
      </aside>
    </div>
  )
}

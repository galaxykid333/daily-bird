import { useState } from 'react'
import { BirdCard } from './components/BirdCard'
import { SavedList } from './components/SavedList'
import { useSaved } from './hooks/useSaved'
import { seededPick, todayString } from './utils/seed'
import speciesData from './data/species.json'
import topicsData from './data/topics.json'

const TODAY = todayString()

function pickCards(extraCounter) {
  const seedStr = `${TODAY}-${extraCounter}`
  const species = seededPick(speciesData, 3, seedStr + '-s')
  const topic = seededPick(topicsData, 1, seedStr + '-t')
  return [
    { title: species[0], type: 'species' },
    { title: species[1], type: 'species' },
    { title: species[2], type: 'species' },
    { title: topic[0], type: 'topic' },
  ]
}

export default function App() {
  // daily cards are always counter 0, "show me more" increments from 1
  const [dailyCards] = useState(() => pickCards(0))
  const [extras, setExtras] = useState([])
  const [extraCounter, setExtraCounter] = useState(1)
  const [showSaved, setShowSaved] = useState(false)
  const { saved, toggle, isSaved } = useSaved()

  function handleShowMore() {
    const newCards = pickCards(extraCounter)
    setExtras((prev) => [...prev, ...newCards])
    setExtraCounter((c) => c + 1)
  }

  return (
    <div className="min-h-screen bg-stone-50 font-sans">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-stone-100">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl select-none">🐦</span>
            <span className="font-serif text-xl font-semibold text-stone-800 tracking-tight">
              Daily Bird
            </span>
          </div>
          <button
            onClick={() => setShowSaved(true)}
            className="flex items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-stone-900 transition-colors"
          >
            <span className="text-rose-400">♥</span>
            Saved
            {saved.length > 0 && (
              <span className="ml-0.5 bg-rose-100 text-rose-600 text-xs rounded-full px-1.5 py-0.5 leading-none">
                {saved.length}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Date banner */}
        <p className="text-xs font-medium text-stone-400 uppercase tracking-widest mb-6">
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>

        {/* Daily picks */}
        <section>
          <h1 className="font-serif text-2xl font-semibold text-stone-800 mb-5">
            Today's picks
          </h1>
          <CardGrid cards={dailyCards} isSaved={isSaved} onToggleSave={toggle} />
        </section>

        {/* Extras from "show me more" */}
        {extras.length > 0 && (
          <section className="mt-10">
            {Array.from({ length: Math.ceil(extras.length / 4) }, (_, i) => {
              const batch = extras.slice(i * 4, i * 4 + 4)
              return (
                <div key={i} className="mb-10">
                  <h2 className="font-serif text-lg font-medium text-stone-500 mb-5">
                    More birds
                  </h2>
                  <CardGrid cards={batch} isSaved={isSaved} onToggleSave={toggle} />
                </div>
              )
            })}
          </section>
        )}

        {/* Show me more button */}
        <div className="flex justify-center mt-10">
          <button
            onClick={handleShowMore}
            className="bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 text-white font-medium text-sm px-6 py-3 rounded-full shadow-sm transition-colors"
          >
            Show me more
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-5xl mx-auto px-4 py-8 text-center text-xs text-stone-400">
        Content sourced from{' '}
        <a
          href="https://en.wikipedia.org"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-stone-600"
        >
          Wikipedia
        </a>{' '}
        under CC BY-SA 4.0.
      </footer>

      {/* Saved list overlay */}
      {showSaved && (
        <SavedList
          saved={saved}
          onRemove={toggle}
          onClose={() => setShowSaved(false)}
        />
      )}
    </div>
  )
}

function CardGrid({ cards, isSaved, onToggleSave }) {
  return (
    <div className="flex flex-col gap-4">
      {cards.map(({ title, type }) => (
        <BirdCard
          key={title}
          title={title}
          type={type}
          isSaved={isSaved(title)}
          onToggleSave={onToggleSave}
        />
      ))}
    </div>
  )
}

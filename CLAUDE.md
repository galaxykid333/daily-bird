# Daily Bird

A personal website that surfaces random bird-related Wikipedia articles daily for discovery and learning.

## Concept

Every day, the site shows four cards: three random **bird species** and one random **bird topic** (anatomy, behaviour, evolution, etc.). A "Show me more" button draws a fresh pair on demand. Users can save interesting finds to a persistent list.

## Tech Stack

- **Framework**: Vite + React
- **Styling**: Tailwind CSS
- **Data**: Static JSON arrays of Wikipedia page titles, fetched at runtime via the Wikipedia REST API
- **Storage**: Browser localStorage for saved items
- **Deployment**: Vercel or GitHub Pages (static site, no backend)

## Data Sources

Two static JSON arrays baked into the app:

1. **Species list** — page titles from https://en.wikipedia.org/wiki/List_of_birds_by_common_name (~10,000 entries)
2. **Topics list** — page titles from the Wikipedia "Birds (class: Aves)" navigation template (~60-80 entries covering anatomy, behaviour, evolution, fossil birds, human interaction, and lists)

These are compiled once via a Python scraping script and saved as static `.json` files in `src/data/`.

## Features

### Daily Picks
- On load, display 4 cards: three species, one topic
- Selection is deterministic per day: hash the date string (e.g. "2026-04-12") to seed the random pick
- Same day = same cards, every time you open it

### Show Me More
- Button below the cards
- Increments a counter on top of the date hash for a fresh pair
- Does not affect the daily picks if you reload

### Card Component
Each card fetches from `https://en.wikipedia.org/api/rest_v1/page/summary/{title}` and displays:
- Thumbnail image (or placeholder if none)
- Species/topic name
- 2-3 sentence extract
- "Read on Wikipedia" link (opens in new tab)
- "Save" button (heart or bookmark icon)

### Saved List
- Stored in localStorage as a JSON array of page titles
- Accessible via a tab/button in the header
- Shows saved items as a list with titles, thumbnails, and Wikipedia links
- Items can be removed from the list

## UI/Layout

- **Header**: Site name + saved list toggle
- **Main**: Two cards — side by side on desktop, stacked on mobile
- **"Show me more" button**: Below the cards
- **Saved list**: Sidebar or overlay, toggled from header
- **Footer**: Minimal — link to Wikipedia sources

## Style Direction

Clean, minimal, nature-inspired. Muted greens and warm neutrals. Readable typography. Generous whitespace. Cards with soft shadows and rounded corners. Fully responsive.

## Build Order

1. Initialise Vite + React + Tailwind project
2. Create the card component with Wikipedia API integration
3. Implement daily seed logic (date-based deterministic selection)
4. Add "Show me more" refresh button
5. Build save functionality (heart button + localStorage + saved list view)
6. Responsive polish, loading states, error handling
7. Compile full bird data (Python scrape of Wikipedia sources)
8. Deploy to Vercel

## Commands

- `npm run dev` — Start dev server
- `npm run build` — Production build
- `npm run preview` — Preview production build locally

## Notes

- Start with a small hardcoded sample of ~30 species and ~10 topics for prototyping. Replace with full scraped data later.
- The Wikipedia REST API requires no authentication and returns JSON with title, extract, and thumbnail.
- Keep the app entirely client-side — no backend, no database, no API keys.

import { useState, useCallback } from 'react'

const STORAGE_KEY = 'daily-bird-saved'

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function persist(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

export function useSaved() {
  const [saved, setSaved] = useState(load)

  const toggle = useCallback((title) => {
    setSaved((prev) => {
      const next = prev.includes(title)
        ? prev.filter((t) => t !== title)
        : [...prev, title]
      persist(next)
      return next
    })
  }, [])

  const isSaved = useCallback((title) => saved.includes(title), [saved])

  return { saved, toggle, isSaved }
}

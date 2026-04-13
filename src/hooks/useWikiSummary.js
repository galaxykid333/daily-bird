import { useState, useEffect } from 'react'

const cache = new Map()

export function useWikiSummary(title) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!title) return
    let cancelled = false

    if (cache.has(title)) {
      setData(cache.get(title))
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    const encoded = encodeURIComponent(title.replace(/ /g, '_'))
    fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encoded}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (cancelled) return
        cache.set(title, json)
        setData(json)
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message)
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [title])

  return { data, loading, error }
}

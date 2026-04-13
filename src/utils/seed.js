/**
 * Deterministic seeded pseudo-random number generator (mulberry32).
 * Returns a function that yields floats in [0, 1).
 */
function mulberry32(seed) {
  return function () {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Hash a string to a 32-bit integer. */
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = Math.imul(31, hash) + str.charCodeAt(i)
    hash |= 0
  }
  return hash
}

/**
 * Pick `n` distinct items from `array` deterministically using the given seed string.
 */
export function seededPick(array, n, seedStr) {
  const rng = mulberry32(hashString(seedStr))
  const pool = [...array]
  const result = []
  for (let i = 0; i < n && pool.length > 0; i++) {
    const idx = Math.floor(rng() * pool.length)
    result.push(pool.splice(idx, 1)[0])
  }
  return result
}

/**
 * Returns today's date string as "YYYY-MM-DD".
 */
export function todayString() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

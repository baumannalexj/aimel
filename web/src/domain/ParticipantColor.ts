// Every participant gets a pill colour, the human included, derived from their email address so it
// is stable across sessions and needs no storage. One function for everyone: if the human's colour
// came from somewhere else it would drift from the agents' the first time either changed.

// Paul Tol's qualitative "light" scheme, ported from src/common/session_color.py — colourblind-safe
// and pale by construction. Hashing straight to 24 bits gives near-white and muddy-brown pills, so we
// hash to an index into this palette instead.
const TOL_LIGHT = [
  '#77AADD',
  '#99DDFF',
  '#44BB99',
  '#BBCC33',
  '#AAAA00',
  '#EEDD88',
  '#EE8866',
  '#FFAABB',
  '#DDDDDD',
]

function fnv1a(seed: string): number {
  let hash = 0x811c9dc5
  for (let i = 0; i < seed.length; i++) {
    hash ^= seed.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193)
  }
  return hash >>> 0
}

/** Deterministic hex for any seed. Same seed, same colour, forever. */
export function hashToHex(seed: string): string {
  return TOL_LIGHT[fnv1a(seed) % TOL_LIGHT.length]
}

export function participantColor(emailAddress: string): string {
  return hashToHex(emailAddress.trim().toLowerCase())
}

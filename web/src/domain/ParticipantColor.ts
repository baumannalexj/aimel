// SEAM — signature is settled, body is not.
//
// Every participant gets a pill colour, the human included, derived from their email address so it
// is stable across sessions and needs no storage. One function for everyone: if the human's colour
// came from somewhere else it would drift from the agents' the first time either changed.

/** Deterministic hex for any seed. Same seed, same colour, forever. */
export function hashToHex(_seed: string): string {
  throw new Error('hashToHex is not implemented yet')
}

export function participantColor(emailAddress: string): string {
  return hashToHex(emailAddress.trim().toLowerCase())
}

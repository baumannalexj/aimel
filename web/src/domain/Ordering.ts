// Ordering and filtering are objects the caller passes in, not behaviour baked into a component.
//
// The view currently renders whatever order the api happened to send, which means the wire and the
// screen are silently coupled: change the server's sort and the UI changes with no code touching it.
// Making the ordering explicit at the call site means the component cannot care, and swapping to
// "by project" or "oldest first" is a different argument rather than a different component.

export interface Comparator<T> {
  compare(left: T, right: T): number
}

export interface Predicate<T> {
  matches(candidate: T): boolean
}

/** Everything passes. The honest name for "no filter", so callers never pass null. */
export class Anything<T> implements Predicate<T> {
  matches(): boolean {
    return true
  }
}

export function sorted<T>(items: readonly T[], comparator: Comparator<T>): T[] {
  // Copied first: sort mutates, and these arrays come from state.
  return [...items].sort((left, right) => comparator.compare(left, right))
}

export function filtered<T>(items: readonly T[], predicate: Predicate<T>): T[] {
  return items.filter((item) => predicate.matches(item))
}

// Mirrors the api's json contract. Kept hand-written and small; generate it later if it grows.

export interface ThreadListItem {
  threadUuid: string
  subject: string
  emailCount: number
  latestEmailUuid: string
  session: string
  sessionShort: string
  updatedAt: string
}

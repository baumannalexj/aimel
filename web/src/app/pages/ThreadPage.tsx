export interface ThreadPageProps {
  readonly threadUuid: string
}

// Placeholder root page for `/threads/:threadUuid`. The real thread view lands here once the data layer settles.
export function ThreadPage({ threadUuid }: ThreadPageProps) {
  return (
    <div className="notice">
      <p>ThreadPage</p>
      <p>threadUuid: {threadUuid}</p>
    </div>
  )
}

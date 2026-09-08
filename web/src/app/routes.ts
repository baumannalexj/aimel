// The route table: which paths exist and which root page serves each.
// No dependency — this is a small hand-rolled matcher, not a routing library.

export interface InboxRoute {
  readonly name: 'inbox'
}

export interface ThreadRoute {
  readonly name: 'thread'
  readonly threadUuid: string
}

export interface NotFoundRoute {
  readonly name: 'not-found'
  readonly path: string
}

export type RouteMatch = InboxRoute | ThreadRoute | NotFoundRoute

interface RouteDefinition<TMatch extends RouteMatch> {
  readonly segments: readonly string[]
  build(params: ReadonlyMap<string, string>): TMatch
}

function route<TMatch extends RouteMatch>(
  pattern: string,
  build: (params: ReadonlyMap<string, string>) => TMatch,
): RouteDefinition<TMatch> {
  return { segments: pattern.split('/').filter(Boolean), build }
}

const routeTable: readonly RouteDefinition<RouteMatch>[] = [
  route('/', () => ({ name: 'inbox' })),
  route('/threads/:threadUuid', (params) => ({
    name: 'thread',
    threadUuid: params.get('threadUuid')!,
  })),
]

export function matchRoute(pathname: string): RouteMatch {
  const pathSegments = pathname.split('/').filter(Boolean)
  for (const candidate of routeTable) {
    const params = matchSegments(candidate.segments, pathSegments)
    if (params) return candidate.build(params)
  }
  return { name: 'not-found', path: pathname }
}

function matchSegments(
  routeSegments: readonly string[],
  pathSegments: readonly string[],
): ReadonlyMap<string, string> | null {
  if (routeSegments.length !== pathSegments.length) return null

  const params = new Map<string, string>()
  for (let i = 0; i < routeSegments.length; i++) {
    const routeSegment = routeSegments[i]
    const pathSegment = pathSegments[i]
    if (routeSegment.startsWith(':')) {
      params.set(routeSegment.slice(1), decodeURIComponent(pathSegment))
    } else if (routeSegment !== pathSegment) {
      return null
    }
  }
  return params
}

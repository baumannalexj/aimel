import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { matchRoute, type RouteMatch } from './routes'

// A default landing place must replace, not push. Pushing means back returns to the path that
// redirected, which redirects forward again -- a history you cannot escape.
export enum HistoryMode {
  Push = 'push',
  Replace = 'replace',
}

export type Navigate = (path: string, mode?: HistoryMode) => void

const NavigateContext = createContext<Navigate>(() => {
  throw new Error('navigate() called outside <Router>')
})

const RouteContext = createContext<RouteMatch | null>(null)

// The session filter lives in `?session=`, orthogonal to which named route matched -- it has to
// survive opening a thread, which only the pathname encodes. Kept as its own context rather than
// a field on RouteMatch so routes.ts stays untouched by a concern that isn't routing.
export type SetSessionFilter = (sessionUuid: string | null) => void
const SessionFilterContext = createContext<[string | null, SetSessionFilter]>([
  null,
  () => {
    throw new Error('setSessionFilter() called outside <Router>')
  },
])

function readSessionFilter(search: string): string | null {
  return new URLSearchParams(search).get('session')
}

// Lets components navigate without reaching for window.history directly.
export function useNavigate(): Navigate {
  return useContext(NavigateContext)
}

export function useRoute(): RouteMatch {
  const route = useContext(RouteContext)
  if (!route) throw new Error('useRoute() called outside <Router>')
  return route
}

export function useSessionFilter(): [string | null, SetSessionFilter] {
  return useContext(SessionFilterContext)
}

export interface RouterProps {
  children: ReactNode
}

// Owns window.history: navigate() pushes a new entry, popstate re-matches from the URL. Neither
// path ever calls the other, so back/forward can't get stuck re-pushing the entry it just left.
export function Router({ children }: RouterProps) {
  const [route, setRoute] = useState<RouteMatch>(() => matchRoute(window.location.pathname))
  const [sessionFilter, setSessionFilterState] = useState<string | null>(() =>
    readSessionFilter(window.location.search),
  )

  useEffect(() => {
    function onPopState() {
      setRoute(matchRoute(window.location.pathname))
      setSessionFilterState(readSessionFilter(window.location.search))
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function navigate(path: string, mode: HistoryMode = HistoryMode.Push) {
    const [pathname, search = ''] = path.split('?')
    if (path === window.location.pathname + window.location.search) return
    if (mode === HistoryMode.Replace) {
      window.history.replaceState(null, '', path)
    } else {
      window.history.pushState(null, '', path)
    }
    setRoute(matchRoute(pathname))
    setSessionFilterState(readSessionFilter(search))
  }

  function setSessionFilter(sessionUuid: string | null) {
    const params = new URLSearchParams(window.location.search)
    if (sessionUuid) {
      params.set('session', sessionUuid)
    } else {
      params.delete('session')
    }
    const query = params.toString()
    // Replace, not push: choosing a filter narrows the current view, it doesn't visit a new one --
    // back should undo the thread you opened, not toggle the dropdown you set two clicks ago.
    navigate(`${window.location.pathname}${query ? `?${query}` : ''}`, HistoryMode.Replace)
  }

  return (
    <NavigateContext.Provider value={navigate}>
      <RouteContext.Provider value={route}>
        <SessionFilterContext.Provider value={[sessionFilter, setSessionFilter]}>
          {children}
        </SessionFilterContext.Provider>
      </RouteContext.Provider>
    </NavigateContext.Provider>
  )
}

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

// Lets components navigate without reaching for window.history directly.
export function useNavigate(): Navigate {
  return useContext(NavigateContext)
}

export function useRoute(): RouteMatch {
  const route = useContext(RouteContext)
  if (!route) throw new Error('useRoute() called outside <Router>')
  return route
}

export interface RouterProps {
  children: ReactNode
}

// Owns window.history: navigate() pushes a new entry, popstate re-matches from the URL. Neither
// path ever calls the other, so back/forward can't get stuck re-pushing the entry it just left.
export function Router({ children }: RouterProps) {
  const [route, setRoute] = useState<RouteMatch>(() => matchRoute(window.location.pathname))

  useEffect(() => {
    function onPopState() {
      setRoute(matchRoute(window.location.pathname))
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function navigate(path: string, mode: HistoryMode = HistoryMode.Push) {
    if (path === window.location.pathname) return
    if (mode === HistoryMode.Replace) {
      window.history.replaceState(null, '', path)
    } else {
      window.history.pushState(null, '', path)
    }
    setRoute(matchRoute(path))
  }

  return (
    <NavigateContext.Provider value={navigate}>
      <RouteContext.Provider value={route}>{children}</RouteContext.Provider>
    </NavigateContext.Provider>
  )
}

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { matchRoute, type RouteMatch } from './routes'
import { InboxPage } from './pages/InboxPage'
import { ThreadPage } from './pages/ThreadPage'

export type Navigate = (path: string) => void

const NavigateContext = createContext<Navigate>(() => {
  throw new Error('navigate() called outside <Router>')
})

// Lets pages navigate without reaching for window.history directly.
export function useNavigate(): Navigate {
  return useContext(NavigateContext)
}

export function Router() {
  const [route, setRoute] = useState<RouteMatch>(() => matchRoute(window.location.pathname))

  useEffect(() => {
    function onPopState() {
      setRoute(matchRoute(window.location.pathname))
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function navigate(path: string) {
    window.history.pushState(null, '', path)
    setRoute(matchRoute(path))
  }

  return <NavigateContext.Provider value={navigate}>{renderRoute(route)}</NavigateContext.Provider>
}

function renderRoute(route: RouteMatch): ReactNode {
  switch (route.name) {
    case 'inbox':
      return <InboxPage />
    case 'thread':
      return <ThreadPage threadUuid={route.threadUuid} />
    case 'not-found':
      return <p className="notice">No page at "{route.path}".</p>
  }
}

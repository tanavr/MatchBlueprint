import { lazy, Suspense, useEffect, useState } from 'react'
import Analyze from './pages/Analyze'
import About from './pages/About'
const Compare = lazy(() => import('./pages/Compare'))

const pages = { analyze: 'Analyze', compare: 'Compare', simulate: 'Simulate', about: 'About Model' }
const currentPage = () => Object.hasOwn(pages, location.hash.slice(1)) ? location.hash.slice(1) : 'analyze'
export default function App() {
  const [page, setPage] = useState(currentPage)
  useEffect(() => {
    const change = () => {
      if (location.hash === '#main-content') return
      setPage(currentPage())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', change)
    return () => window.removeEventListener('hashchange', change)
  }, [])
  useEffect(() => { document.title = `${pages[page]} · MatchBlueprint` }, [page])
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#analyze"><span className="brand-mark" aria-hidden="true">MB<span>.</span></span><span>MatchBlueprint</span></a><p className="nav-caption">Workspace</p>
      <nav aria-label="Main navigation">{Object.entries(pages).map(([id, label], i) => <a key={id} href={`#${id}`} aria-current={page === id ? 'page' : undefined}><span className="nav-index">0{i + 1}</span>{label}<span className="nav-arrow" aria-hidden="true">↗</span></a>)}</nav>
      <div className="sidebar-note"><span className="status-dot" />Transparent by design<p>Football analysis with the assumptions in view.</p><span className="version">RESEARCH WORKSPACE / V1</span></div>
    </aside>
    <div className="workspace"><header className="topbar"><span>Workspace <span className="breadcrumb">/</span> <strong>{pages[page]}</strong></span><span className="topbar-note">MatchBlueprint</span></header>
      <main id="main-content" tabIndex="-1">{page === 'analyze' ? <Analyze /> : page === 'compare' ? <Suspense fallback={<p role="status">Loading comparison workspace…</p>}><Compare /></Suspense> : page === 'about' ? <About /> : <><div className="page-heading"><p className="eyebrow">{pages[page]}</p><h1>{page === 'compare' ? 'Two teams. Different approaches.' : 'Explore the hypothetical.'}</h1><p>{page === 'compare' ? 'Compare tactical profiles across clubs, leagues, and seasons.' : 'Explainable goal estimates and match outcome probabilities.'}</p></div><section className="panel coming-soon"><span className="badge">Interface planned</span><h2>{pages[page]} workspace</h2><p>The backend supports this feature. Its dedicated dashboard is a future step; team analysis is ready to explore now.</p><a className="primary-button" href="#analyze">Analyze a team →</a></section></>}</main>
      <footer><span>MatchBlueprint</span><span>Relative style. Transparent context.</span></footer>
    </div>
  </div>
}

import { useEffect } from 'react'
import { Link, Outlet, useLocation } from 'react-router'
import Header from './Header.jsx'
export default function Layout() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (hash) { const timer = window.setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView(), 0); return () => window.clearTimeout(timer) }
    window.scrollTo(0, 0)
  }, [pathname, hash])
  return <><a href="#main" className="skip-link">Skip to content</a><Header /><main id="main"><Outlet /></main>
    <footer className="site-footer"><div className="container footer-grid"><div><Link className="brand" to="/">Campusly <span>↗</span></Link><p>A little less scrolling.<br />A little more showing up.</p></div><div><strong>Find your people</strong><Link to="/#events">Explore events</Link><Link to="/registrations">My registrations</Link></div><div><strong>Your campus</strong><Link to="/profile">My profile</Link><Link to="/organizer">Organizer workspace</Link></div><div className="footer-note"><span>GOOD THINGS HAPPEN<br />WHEN WE GET TOGETHER.</span><p>Event times use Tashkent time, UTC+5.</p></div></div><div className="container footer-bottom"><span>Campusly · University Event Manager</span><span>Made for campus life.</span></div></footer></>
}

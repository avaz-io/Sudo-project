import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import './Header.css'

export default function Header() {
  const { user, status, logout, retry } = useAuth()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  async function handleLogout() {
    setBusy(true); setError('')
    try { await logout(); setOpen(false); navigate('/') }
    catch (error) { setError(error.message) }
    finally { setBusy(false) }
  }
  return <header className="site-header"><div className="container header-content">
    <Link className="brand" to="/" onClick={() => setOpen(false)}>Campusly <span>↗</span></Link>
    <button className="menu-toggle" aria-expanded={open} aria-controls="site-navigation" onClick={() => setOpen(!open)}>{open ? 'Close ✕' : 'Menu ☰'}</button>
    <nav id="site-navigation" className={open ? 'header-nav is-open' : 'header-nav'} aria-label="Main navigation">
      <NavLink to="/" end onClick={() => setOpen(false)}>Discover</NavLink>
      {user && <NavLink to="/registrations" onClick={() => setOpen(false)}>My registrations</NavLink>}
      {user?.role === 'organizer' && <NavLink to="/organizer" onClick={() => setOpen(false)}>Organize</NavLink>}
      <div className="header-account">
        {status === 'checking' && <span className="header-status" role="status">Checking account…</span>}
        {status === 'unavailable' && <button className="button outline-light small" onClick={retry}>Retry account</button>}
        {status === 'anonymous' && <><Link to="/login" onClick={() => setOpen(false)}>Log in</Link><Link className="button small" to="/signup" onClick={() => setOpen(false)}>Create account ↗</Link></>}
        {status === 'authenticated' && <><Link className="account-link" to="/profile" onClick={() => setOpen(false)}><span className="avatar" aria-hidden="true">{user.display_name.slice(0, 1).toUpperCase()}</span><span>{user.display_name}</span></Link><button className="logout-button" onClick={handleLogout} disabled={busy}>{busy ? 'Logging out…' : 'Log out'}</button></>}
      </div>
    </nav>
  </div>{error && <p className="container header-error" role="alert">{error}</p>}</header>
}

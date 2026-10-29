import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import './Header.css'

function clearSession() {
  sessionStorage.removeItem('campusly_token')
  sessionStorage.removeItem('campusly_user')
}

export default function Header() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(() =>
    sessionStorage.getItem('campusly_token') ? 'checking' : 'anonymous'
  )
  const [error, setError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const token = sessionStorage.getItem('campusly_token')
    if (!token) return
    const controller = new AbortController()

    async function checkAccount() {
      try {
        const response = await fetch('/api/users/me', {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        })
        if (controller.signal.aborted) return
        if (response.status === 401) {
          clearSession()
          setUser(null)
          setStatus('anonymous')
          setError('Your session has expired. Please log in again.')
          return
        }
        if (!response.ok) throw new Error('Account unavailable')
        const account = await response.json()
        if (controller.signal.aborted) return
        if (typeof account.display_name !== 'string') throw new Error('Invalid account')
        sessionStorage.setItem('campusly_user', JSON.stringify(account))
        setUser(account)
        setStatus('authenticated')
      } catch {
        if (controller.signal.aborted) return
        setError('We could not load your account. Please try again.')
        setStatus('unavailable')
      }
    }

    checkAccount()
    return () => controller.abort()
  }, [retry])

  function retryAccount() {
    setError('')
    setStatus('checking')
    setRetry((value) => value + 1)
  }

  async function handleLogout() {
    setError('')
    setLoggingOut(true)
    try {
      const token = sessionStorage.getItem('campusly_token')
      if (token) {
        const response = await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!response.ok && response.status !== 401) throw new Error('Logout failed')
      }
      clearSession()
      setUser(null)
      setStatus('anonymous')
      navigate('/', { replace: true })
    } catch {
      setError('We could not log you out. Please try again.')
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <header className="site-header account-header" id="home">
      <div className="container header-content">
        <Link className="brand" to="/" aria-label="Campusly home">
          <svg className="header-logo" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M5 6h22v6a4 4 0 0 0 0 8v6H5v-6a4 4 0 0 0 0-8V6Z" />
            <path d="M20 9v14" strokeDasharray="2 3" />
          </svg>
          Campusly
        </Link>
        <nav className="header-nav" aria-label="Main navigation">
          <a href="#home">Home</a>
          <a href="#categories">Categories</a>
          <a href="#events">Explore events →</a>
        </nav>
        <div className="header-account" aria-live="polite">
          {status === 'checking' && <span className="header-status">Checking account…</span>}
          {status === 'anonymous' && <>
            <Link className="header-login" to="/login">Log in</Link>
            <Link className="header-signup" to="/signup">Create account</Link>
          </>}
          {status === 'authenticated' && <>
            <span className="header-name" title={user.display_name}>{user.display_name}</span>
            <button className="header-logout" type="button" onClick={handleLogout} disabled={loggingOut}>
              {loggingOut ? 'Logging out…' : 'Log out'}
            </button>
          </>}
          {status === 'unavailable' && <button className="header-logout" type="button" onClick={retryAccount}>Retry account</button>}
        </div>
      </div>
      {error && <p className="container header-error" role="alert">{error}</p>}
    </header>
  )
}

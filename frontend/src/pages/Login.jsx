import { useState } from 'react'
import { Link, useLocation } from 'react-router'
import './Login.css'

export default function Login({ onLogin }) {
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try { await onLogin({ email: email.trim(), password }) }
    catch (error) { setError(error.message || 'Unable to log in. Please try again.') }
    finally { setLoading(false) }
  }
  return (
    <main className="auth-page">
      <aside className="auth-story">
        <Link className="brand" to="/">Campusly ↗</Link>
        <div><p className="eyebrow">YOUR CAMPUS. YOUR COMMUNITY.</p><h2>Your next experience starts here.</h2><p>Discover events, meet people, and make campus life yours.</p></div>
      </aside>
      <section className="auth-panel" aria-labelledby="login-title">
        <Link className="auth-back" to="/">← Back to home</Link>
        <div className="auth-form-container">
          <h1 id="login-title">Welcome back</h1>
          <p className="auth-description">Log in to discover what’s happening on campus.</p>
          <form className="auth-form" onSubmit={handleSubmit} aria-busy={loading}>
            <label htmlFor="login-email">Email address</label>
            <input id="login-email" name="email" type="email" autoComplete="username" placeholder="you@university.edu" value={email} onChange={(event) => setEmail(event.target.value)} disabled={loading} required />
            <label htmlFor="login-password">Password</label>
            <input id="login-password" name="password" type="password" autoComplete="current-password" placeholder="Enter your password" maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} disabled={loading} required />
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Logging in…' : 'Log in'}</button>
          </form>
          <p className="auth-switch">New to Campusly? <Link to="/signup" state={location.state}>Create an account</Link></p>
        </div>
      </section>
    </main>
  )
}

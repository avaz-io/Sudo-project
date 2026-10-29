import { useState } from 'react'
import { Link, useLocation } from 'react-router'
import './Login.css'
import './Signup.css'

export default function Signup({ onSignup }) {
  const location = useLocation()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (!displayName.trim()) {
      setError('Please enter your name.')
      return
    }
    if (password !== confirmPassword) {
      setError('Your passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await onSignup({
        display_name: displayName.trim(),
        email: email.trim(),
        password,
      })
    } catch (error) {
      setError(error.message || 'Unable to create your account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page signup-page">
      <aside className="auth-story">
        <Link className="brand" to="/">Campusly ↗</Link>
        <div>
          <p className="eyebrow">YOUR CAMPUS. YOUR COMMUNITY.</p>
          <h2>Make your campus experience yours.</h2>
          <p>Join your community and discover events worth showing up for.</p>
        </div>
      </aside>

      <section className="auth-panel" aria-labelledby="signup-title">
        <Link className="auth-back" to="/">← Back to home</Link>
        <div className="auth-form-container">
          <h1 id="signup-title">Create an account</h1>
          <p className="auth-description">Discover more. Connect with your campus.</p>

          <form className="auth-form" onSubmit={handleSubmit} aria-busy={loading}>
            <label htmlFor="signup-name">Full name</label>
            <input
              id="signup-name"
              name="display_name"
              type="text"
              autoComplete="name"
              placeholder="Enter your full name"
              maxLength={100}
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              disabled={loading}
              required
            />

            <label htmlFor="signup-email">Email address</label>
            <input
              id="signup-email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@university.edu"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={loading}
              required
            />

            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="Create a password"
              minLength={8}
              maxLength={128}
              aria-describedby="signup-password-help"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={loading}
              required
            />
            <p className="auth-password-help" id="signup-password-help">
              Use at least 8 characters.
            </p>

            <label htmlFor="signup-confirm">Confirm password</label>
            <input
              id="signup-confirm"
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              placeholder="Enter your password again"
              minLength={8}
              maxLength={128}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              disabled={loading}
              required
            />

            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? 'Creating your account…' : 'Create account'}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login" state={location.state}>Log in</Link>
          </p>
        </div>
      </section>
    </main>
  )
}

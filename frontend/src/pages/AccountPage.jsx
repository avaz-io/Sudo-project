import { useNavigate } from 'react-router'
import Login from './Login.jsx'
import Signup from './Signup.jsx'

export default function AccountPage({ signup = false }) {
  const navigate = useNavigate()

  async function handleSubmit(credentials) {
    let response
    try {
      response = await fetch(`/api/auth/${signup ? 'register' : 'login'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      })
    } catch {
      throw new Error('Cannot connect to the account service. Please try again.')
    }

    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const detail = typeof data?.detail === 'string'
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((item) => item.msg).join(' ')
          : 'Unable to complete your request. Please try again.'
      throw new Error(detail)
    }
    if (!data?.access_token || !data?.user) {
      throw new Error('The account service is currently unavailable.')
    }

    sessionStorage.setItem('campusly_token', data.access_token)
    sessionStorage.setItem('campusly_user', JSON.stringify(data.user))
    navigate('/', { replace: true })
  }

  return signup
    ? <Signup onSignup={handleSubmit} />
    : <Login onLogin={handleSubmit} />
}

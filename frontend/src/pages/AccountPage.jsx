import { useLocation, useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import Login from './Login.jsx'
import Signup from './Signup.jsx'
export default function AccountPage({ signup = false }) {
  const { authenticate } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  async function handleSubmit(credentials) {
    await authenticate(credentials, signup)
    const destination = location.state?.returnTo
    navigate(typeof destination === 'string' && /^\/(events\/\d+|registrations|profile|organizer(?:\/(?:new|\d+(?:\/(?:edit|participants))?))?)(?:\?[^#]*)?$/.test(destination) ? destination : '/', { replace: true })
  }
  return signup ? <Signup onSignup={handleSubmit} /> : <Login onLogin={handleSubmit} />
}

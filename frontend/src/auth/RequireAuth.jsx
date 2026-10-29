import { Navigate, useLocation } from 'react-router'
import { useAuth } from './AuthContext.js'
import Feedback from '../components/Feedback.jsx'
export default function RequireAuth({ organizer = false, children }) {
  const { status, user, retry } = useAuth()
  const location = useLocation()
  if (status === 'checking') return <Feedback loading />
  if (status === 'unavailable') return <Feedback error={new Error('We could not verify your account.')} retry={retry} />
  if (status !== 'authenticated') return <Navigate to="/login" replace state={{ returnTo: location.pathname + location.search }} />
  if (organizer && user.role !== 'organizer') return <Feedback title="Organizer access required"><p>Your account can discover and register for events. Organizer access is granted by the project team.</p></Feedback>
  return children
}

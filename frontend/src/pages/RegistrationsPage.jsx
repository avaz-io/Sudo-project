import { useRef, useState } from 'react'
import { Link } from 'react-router'
import useResource from '../hooks/useResource.js'
import useNow from '../hooks/useNow.js'
import { request } from '../api/client.js'
import Feedback from '../components/Feedback.jsx'
import EventCard from '../components/EventCard.jsx'
export default function RegistrationsPage() {
  const { data, loading, error, reload } = useResource('/users/me/registrations', true)
  const [busy, setBusy] = useState(null)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const [confirmId, setConfirmId] = useState(null)
  const acting = useRef(false)
  const now = useNow()
  async function cancel(id) {
    if (acting.current) return
    acting.current = true; setBusy(id); setActionError(''); setNotice('')
    try { await request(`/events/${id}/registration`, { method: 'DELETE', auth: true }); setNotice('Your registration was cancelled.'); setConfirmId(null); reload() }
    catch (error) { setActionError(error.message) }
    finally { acting.current = false; setBusy(null) }
  }
  return <div className="container page-space"><div className="page-heading heading-row"><div><p className="eyebrow muted">YOUR NEXT GOOD STORY</p><h1>My registrations.</h1><p>Everything you have signed up for, in one place.</p></div><Link className="button secondary" to="/#events">Find more events ↗</Link></div>
    {notice && <p className="alert success" role="status">{notice}</p>}{actionError && <p className="alert error" role="alert">{actionError}</p>}
    {loading || error ? <Feedback loading={loading} error={error} retry={reload} /> : !data.length ? <Feedback title="Your calendar has room for more."><p>Discover an event and make your first campus connection.</p><Link className="button" to="/#events">Explore events ↗</Link></Feedback> : <><div className="list-toolbar"><span>{data.length} active {data.length === 1 ? 'registration' : 'registrations'}</span><button className="text-link" onClick={reload}>Refresh ↻</button></div><div className="event-grid">{data.map(({ id, event }) => <EventCard key={id} event={event}><span className={`badge status-${event.status}`}>{event.status === 'cancelled' ? 'Event cancelled by organizer' : event.status === 'completed' ? 'Event completed' : 'You are registered'}</span><Link className="text-link" to={`/events/${event.id}`}>View event ↗</Link>{Date.parse(event.starts_at) > now && (confirmId === event.id ? <div className="inline-confirm"><p>Cancel your place at this event?</p><button className="button danger small" disabled={busy !== null} onClick={() => cancel(event.id)}>{busy === event.id ? 'Cancelling…' : 'Yes, cancel'}</button><button className="button secondary small" disabled={busy !== null} onClick={() => setConfirmId(null)}>Keep my place</button></div> : <button className="text-link danger-text" disabled={busy !== null} onClick={() => setConfirmId(event.id)}>Cancel registration</button>)}</EventCard>)}</div></>}
  </div>
}

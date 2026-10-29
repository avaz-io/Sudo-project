import { useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import { request } from '../api/client.js'
import useResource from '../hooks/useResource.js'
import useNow from '../hooks/useNow.js'
import { categoryInfo, formatTime } from '../data/events.js'
import Feedback from '../components/Feedback.jsx'
import './EventPage.css'

export default function EventPage() {
  const { eventId } = useParams()
  return <EventDetail key={eventId} id={eventId} />
}
function EventDetail({ id }) {
  const { user, status, retry } = useAuth()
  const authenticated = status === 'authenticated'
  const { data: event, loading, error, reload } = useResource(`/events/${id}`, authenticated)
  const [busy, setBusy] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const [notice, setNotice] = useState('')
  const [actionError, setActionError] = useState('')
  const acting = useRef(false)
  const navigate = useNavigate()
  const now = useNow()
  const returnTo = `/events/${id}`
  async function register(cancel = false) {
    if (acting.current) return
    if (!authenticated) { navigate('/login', { state: { returnTo } }); return }
    acting.current = true; setBusy(true); setActionError(''); setNotice('')
    try {
      await request(`/events/${id}/registration`, { method: cancel ? 'DELETE' : 'POST', auth: true })
      setNotice(cancel ? 'Your registration has been cancelled.' : 'You are registered. See you there!')
      setConfirm(false); reload()
    } catch (error) { setActionError(error.message) }
    finally { acting.current = false; setBusy(false) }
  }
  if (loading || error || status === 'checking') return <Feedback loading={loading || status === 'checking'} error={error} retry={reload} />
  const category = categoryInfo(event.category)
  const registered = event.my_registration_status === 'active'
  const upcoming = Date.parse(event.starts_at) > now
  const canRegister = event.status === 'published' && upcoming && event.available_places !== 0
  const owner = user?.role === 'organizer' && user.id === event.organizer.id
  return <><section className="detail-hero"><div className="container"><Link className="back-link" to="/#events">← All events</Link><div className="detail-hero-grid"><div><span className="badge light">{category.label}</span><h1>{event.title}</h1><p>Organized by <strong>{event.organizer.display_name}</strong></p><span className={`badge status-${event.status}`}>{event.status}</span></div><img className="detail-photo" src={category.image} alt={`${category.label} category illustration`} /><span className="detail-photo-label">Category image</span></div></div></section>
    <div className="container detail-layout"><section className="detail-about"><p className="eyebrow muted">BE PART OF IT</p><h2>About this event</h2><p className="description">{event.description}</p>{owner && <div className="button-row"><Link className="button secondary" to={`/organizer/${id}/edit`}>Manage event</Link><Link className="text-link" to={`/organizer/${id}/participants`}>View participants ↗</Link></div>}</section>
    <section className="panel booking-panel" aria-labelledby="booking-title" aria-busy={busy}><span className="eyebrow muted">SAVE YOUR PLACE</span><h2 id="booking-title">See you there?</h2><dl><dt>When</dt><dd><time dateTime={event.starts_at}>{formatTime(event.starts_at)}</time><span>Tashkent time (UTC+5)</span></dd><dt>Where</dt><dd>{event.location}</dd><dt>Availability</dt><dd>{event.available_places === null ? 'No capacity limit' : event.available_places === 0 ? 'Fully booked' : `${event.available_places} places available`}</dd></dl>
    {notice && <p className="alert success" role="status">{notice}</p>}{registered && !notice && <p className="alert success">You are registered for this event.</p>}{actionError && <div className="alert error"><p role="alert">{actionError}</p><button className="text-link" onClick={reload} disabled={busy}>Refresh event</button></div>}
    {status === 'unavailable' ? <><p className="field-help">Check your account before registering.</p><button className="button secondary" onClick={retry}>Retry account</button></> : registered && upcoming ? confirm ? <div className="inline-confirm"><p>Cancel your place?</p><button className="button danger" disabled={busy} onClick={() => register(true)}>{busy ? 'Cancelling…' : 'Yes, cancel registration'}</button><button className="button secondary" disabled={busy} onClick={() => setConfirm(false)}>Keep my place</button></div> : <button className="button secondary full-width" onClick={() => setConfirm(true)}>Cancel registration</button> : !registered && canRegister ? authenticated ? <button className="button full-width" disabled={busy} onClick={() => register()}>{busy ? 'Registering…' : 'Register for event ↗'}</button> : <Link className="button full-width" to="/login" state={{ returnTo }}>Log in to register ↗</Link> : <p className="closed-message">{event.status === 'cancelled' ? 'This event has been cancelled.' : !upcoming || event.status === 'completed' ? 'Registration is closed.' : event.available_places === 0 ? 'This event is full.' : 'Registration is not open yet.'}</p>}
    <Link className="text-link booking-more" to="/registrations">My registrations ↗</Link>
    </section></div></>
}

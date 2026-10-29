import { useRef, useState } from 'react'
import { Link } from 'react-router'
import useResource from '../hooks/useResource.js'
import useNow from '../hooks/useNow.js'
import { request } from '../api/client.js'
import { formatTime } from '../data/events.js'
import Feedback from '../components/Feedback.jsx'
export default function OrganizerPage() {
  const { data, loading, error, reload } = useResource('/users/me/events', true)
  const [filter, setFilter] = useState('all')
  const [pending, setPending] = useState(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const acting = useRef(false)
  const now = useNow()
  const events = data || []
  async function transition() {
    if (acting.current || !pending) return
    acting.current = true; setBusy(true); setActionError(''); setNotice('')
    try { await request(`/events/${pending.event.id}/${pending.action}`, { method: 'POST', auth: true }); setNotice(`“${pending.event.title}” was ${pending.action === 'publish' ? 'published' : pending.action === 'cancel' ? 'cancelled' : 'completed'}.`); setPending(null); reload() }
    catch (error) { setActionError(error.message) }
    finally { acting.current = false; setBusy(false) }
  }
  const results = events.filter((event) => filter === 'all' || event.status === filter)
  return <div className="container page-space"><div className="page-heading heading-row"><div><p className="eyebrow muted">BRING PEOPLE TOGETHER</p><h1>Your organizer workspace.</h1><p>Plan it. Publish it. Make it happen.</p></div><Link className="button" to="/organizer/new">Create event ↗</Link></div>
    <div className="stats-grid"><div><strong>{events.length}</strong><span>Total events</span></div><div><strong>{events.filter((event) => event.status === 'published').length}</strong><span>Published</span></div><div><strong>{events.filter((event) => event.status === 'draft').length}</strong><span>Drafts</span></div><div><strong>{events.reduce((count, event) => count + event.active_registrations, 0)}</strong><span>Active registrations</span></div></div>
    {notice && <p className="alert success" role="status">{notice}</p>}{actionError && <p className="alert error" role="alert">{actionError}</p>}
    {pending && <section className="confirmation panel" aria-labelledby="confirm-action"><h2 id="confirm-action">{pending.action === 'cancel' ? 'Cancel this event?' : pending.action === 'publish' ? 'Publish this event?' : 'Mark this event as completed?'}</h2><p>{pending.event.title}</p><p>{pending.action === 'cancel' ? 'Attendees will see that the event was cancelled. This cannot be undone.' : pending.action === 'publish' ? 'The event will appear in public discovery if its start time is in the future.' : 'The event will be marked as completed. This cannot be undone.'}</p><div className="button-row"><button className={`button ${pending.action === 'cancel' ? 'danger' : ''}`} onClick={transition} disabled={busy}>{busy ? 'Updating…' : 'Confirm'}</button><button className="button secondary" onClick={() => setPending(null)} disabled={busy}>Go back</button></div></section>}
    <div className="list-toolbar"><label htmlFor="event-status-filter">Show <select id="event-status-filter" value={filter} onChange={(event) => setFilter(event.target.value)}>{['all', 'draft', 'published', 'cancelled', 'completed'].map((value) => <option key={value} value={value}>{value === 'all' ? 'All events' : value}</option>)}</select></label><button className="text-link" disabled={busy || loading} onClick={reload}>Refresh ↻</button></div>
    {loading || error ? <Feedback loading={loading} error={error} retry={reload} /> : !results.length ? <Feedback title="A new experience starts here."><p>{events.length ? 'No events match this status.' : 'Create your first event and save it as a draft.'}</p><Link className="button" to="/organizer/new">Create event ↗</Link></Feedback> : <div className="organizer-list">{results.map((event) => {
      const future = Date.parse(event.starts_at) > now
      const editable = event.status === 'draft' || (event.status === 'published' && future)
      return <article className="organizer-event panel" key={event.id}><div><span className={`badge status-${event.status}`}>{event.status}</span><h2><Link to={`/events/${event.id}`}>{event.title}</Link></h2><p>{formatTime(event.starts_at)} · {event.location}</p><p>{event.active_registrations} active registrations{event.capacity !== null ? ` / ${event.capacity} places` : ' · No capacity limit'}</p></div><div className="organizer-actions"><Link className="button secondary small" to={`/organizer/${event.id}/participants`}>Participants</Link>{editable && <Link className="button secondary small" to={`/organizer/${event.id}/edit`}>Edit</Link>}{event.status === 'draft' && <button className="button small" disabled={busy} onClick={() => { setActionError(''); setPending({ event, action: 'publish' }) }}>Publish</button>}{editable && <button className="text-link danger-text" disabled={busy} onClick={() => { setActionError(''); setPending({ event, action: 'cancel' }) }}>Cancel event</button>}{event.status === 'published' && !future && <button className="button secondary small" disabled={busy} onClick={() => { setActionError(''); setPending({ event, action: 'complete' }) }}>Mark completed</button>}</div></article>
    })}</div>}
  </div>
}

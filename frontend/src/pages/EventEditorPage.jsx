import { useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import { request } from '../api/client.js'
import useResource from '../hooks/useResource.js'
import useNow from '../hooks/useNow.js'
import { categories, eventPayload, toTashkentInput } from '../data/events.js'
import Feedback from '../components/Feedback.jsx'
export default function EventEditorPage() {
  const { eventId } = useParams()
  return eventId ? <LoadEditor key={eventId} id={eventId} /> : <EventForm key="new" />
}
function LoadEditor({ id }) {
  const { user } = useAuth()
  const { data, loading, error, reload } = useResource(`/events/${id}`, true)
  const now = useNow()
  if (loading || error) return <Feedback loading={loading} error={error} retry={reload} />
  if (data.organizer.id !== user.id) return <Feedback title="This event belongs to another organizer."><p>You can edit events you created.</p><Link className="button" to="/organizer">My events</Link></Feedback>
  if (data.status !== 'draft' && !(data.status === 'published' && Date.parse(data.starts_at) > now)) return <Feedback title="This event can no longer be edited."><Link className="button" to="/organizer">Back to workspace</Link></Feedback>
  return <EventForm event={data} />
}
function EventForm({ event }) {
  const navigate = useNavigate()
  const [fields, setFields] = useState(() => ({ title: event?.title || '', description: event?.description || '', category: event?.category || 'academic', starts_at: event ? toTashkentInput(event.starts_at) : '', location: event?.location || '', capacity: event?.capacity ?? '' }))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const saving = useRef(false)
  function update(change) { setFields((current) => ({ ...current, [change.target.name]: change.target.value })) }
  async function save(submit) {
    submit.preventDefault()
    if (saving.current) return
    setError('')
    let payload
    try { payload = eventPayload(fields) } catch (error) { setError(error.message); return }
    saving.current = true; setBusy(true)
    try { await request(event ? `/events/${event.id}` : '/events', { method: event ? 'PATCH' : 'POST', auth: true, body: payload }); navigate('/organizer', { replace: true }) }
    catch (error) { setError(error.message) }
    finally { saving.current = false; setBusy(false) }
  }
  return <div className="container page-space editor-page"><Link className="text-link" to="/organizer">← Organizer workspace</Link><div className="page-heading"><p className="eyebrow muted">MAKE IT HAPPEN</p><h1>{event ? 'Fine-tune your event.' : 'Create something worth sharing.'}</h1><p>{event ? 'Keep your event details up to date.' : 'Start with the essentials. Your new event is saved as a draft.'}</p></div><form className="panel stack-form" onSubmit={save} aria-busy={busy}>
    <label htmlFor="event-title">Event title</label><input id="event-title" name="title" value={fields.title} onChange={update} maxLength={200} required disabled={busy} placeholder="Give your event a great name" />
    <label htmlFor="event-description">About the event</label><textarea id="event-description" name="description" value={fields.description} onChange={update} maxLength={5000} rows={7} required disabled={busy} placeholder="What can people expect? Who is it for?" />
    <div className="form-grid"><div><label htmlFor="event-category">Category</label><select id="event-category" name="category" value={fields.category} onChange={update} disabled={busy}>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div><div><label htmlFor="event-start">Start date and time</label><input id="event-start" name="starts_at" type="datetime-local" value={fields.starts_at} onChange={update} required disabled={busy} aria-describedby="timezone-help" /><p id="timezone-help" className="field-help">Tashkent time (UTC+5), regardless of your device timezone.</p></div></div>
    <label htmlFor="event-location">Location</label><input id="event-location" name="location" value={fields.location} onChange={update} maxLength={200} required disabled={busy} placeholder="Building, room or venue" />
    <label htmlFor="event-capacity">Capacity <span className="muted">(optional)</span></label><input id="event-capacity" name="capacity" type="number" min={Math.max(1, event?.active_registrations || 1)} step="1" value={fields.capacity} onChange={update} disabled={busy} aria-describedby="capacity-help" /><p id="capacity-help" className="field-help">Leave empty for no capacity limit.{event ? ` There are currently ${event.active_registrations} active registrations.` : ''}</p>
    {error && <p className="alert error" role="alert">{error}</p>}<div className="button-row"><button className="button" disabled={busy}>{busy ? 'Saving…' : event ? 'Save changes' : 'Save as draft'}</button><Link className="button secondary" to="/organizer">Back to workspace</Link></div>
  </form></div>
}

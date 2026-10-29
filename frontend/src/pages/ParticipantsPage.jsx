import { Link, useParams } from 'react-router'
import useResource from '../hooks/useResource.js'
import { formatTime } from '../data/events.js'
import Feedback from '../components/Feedback.jsx'
export default function ParticipantsPage() {
  const { eventId } = useParams()
  const { data, loading, error, reload } = useResource(`/events/${eventId}/participants`, true)
  return <div className="container page-space"><Link className="text-link" to="/organizer">← Organizer workspace</Link><div className="page-heading heading-row"><div><p className="eyebrow muted">YOUR EVENT COMMUNITY</p><h1>Participants.</h1><p>Active registrations for event #{eventId}.</p></div><button className="button secondary" onClick={reload} disabled={loading}>Refresh ↻</button></div>{loading || error ? <Feedback loading={loading} error={error} retry={reload} /> : !data.participants.length ? <Feedback title="The guest list starts here."><p>No one has registered yet. Publish your event so people can discover it.</p><Link className="button" to={`/events/${eventId}`}>View event ↗</Link></Feedback> : <div className="panel table-wrap"><table><caption>{data.count} active {data.count === 1 ? 'participant' : 'participants'}</caption><thead><tr><th scope="col">Name</th><th scope="col">Registered at · Tashkent time</th></tr></thead><tbody>{data.participants.map((person) => <tr key={person.user_id}><td>{person.display_name}</td><td><time dateTime={person.registered_at}>{formatTime(person.registered_at)}</time></td></tr>)}</tbody></table></div>}</div>
}

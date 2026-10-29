import { Link } from 'react-router'
import { categoryInfo, formatDate, formatTime } from '../data/events.js'
export default function EventCard({ event, children }) {
  const category = categoryInfo(event.category)
  return <article className="event-card"><Link className={`event-cover cover-${category.value}`} to={`/events/${event.id}`} aria-label={`View ${event.title}`}>
    <img src={category.image} alt="" loading="lazy" /><span className="category-tag">{category.label}</span><span className="card-arrow" aria-hidden="true">↗</span></Link>
    <div className="event-card-body"><div className="date-tile" aria-hidden="true"><span>{formatDate(event.starts_at, { month: 'short', day: undefined, year: undefined })}</span><strong>{formatDate(event.starts_at, { month: undefined, day: '2-digit', year: undefined })}</strong></div>
    <div className="event-card-info"><h3><Link to={`/events/${event.id}`}>{event.title}</Link></h3><p>{event.location}</p><p><time dateTime={event.starts_at}>{formatTime(event.starts_at)}</time></p><p className="availability">{event.available_places === null ? 'Open capacity' : event.available_places === 0 ? 'Fully booked' : `${event.available_places} places left`}</p></div></div>
    {children && <div className="event-card-actions">{children}</div>}</article>
}

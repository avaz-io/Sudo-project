import { Link, useSearchParams } from 'react-router'
import { useAuth } from './auth/AuthContext.js'
import useResource from './hooks/useResource.js'
import EventCard from './components/EventCard.jsx'
import Feedback from './components/Feedback.jsx'
import { categories, discoveryParams, filterEvents } from './data/events.js'
import './App.css'

export default function App() {
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const query = params.get('q') || ''
  const category = params.get('category') || ''
  const draft = query
  const { data, loading, error, reload } = useResource('/events')
  const events = Array.isArray(data) ? data : []
  const results = filterEvents(events, query, category)
  function filter(q, nextCategory) {
    setParams(discoveryParams(q, nextCategory), { replace: true })
  }
  function search(event) { event.preventDefault(); filter(draft, category); document.getElementById('events')?.scrollIntoView({ behavior: 'smooth' }) }
  function clearFilters() { filter('', '') }
  return <>
    <section className="hero" aria-labelledby="hero-title"><div className="container hero-layout"><div className="hero-copy">
      <p className="eyebrow">YOUR CAMPUS. YOUR COMMUNITY.</p><h1 id="hero-title">More than<br />a campus.<br /><span>A place to belong.</span></h1>
      <p className="hero-description">New experiences. Familiar faces. Your next good story starts with showing up.</p><a className="hero-link" href="#events">Find your next experience <span>↗</span></a>
    </div><div className="hero-collage" aria-hidden="true"><div className="collage-photo photo-one"><img src="/images/cultural.webp" alt="" /><span>MAKE SOME NOISE.</span></div><div className="collage-photo photo-two"><img src="/images/social.webp" alt="" /><span>FIND YOUR PEOPLE.</span></div><span className="hero-sticker">SEE YOU<br />THERE ↗</span><span className="hero-star">✳</span></div></div>
      <div className="container"><form className="search-form" role="search" onSubmit={search}><label><span>What are you looking for?</span><input type="search" maxLength={200} placeholder="Search events by title" value={draft} onChange={(event) => { filter(event.target.value, category) }} /></label><label><span>Category</span><select value={category} onChange={(event) => filter(draft, event.target.value)}><option value="">All categories</option>{categories.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label><button className="button" type="submit">Find events ↗</button></form></div>
    </section>
    <section className="container category-section" id="categories" aria-labelledby="categories-title"><div className="section-heading"><h2 id="categories-title">A little something for everyone.</h2><a className="text-link" href="#events">Explore events ↗</a></div><div className="category-list">{categories.map((item) => <button className="category-button" key={item.value} aria-pressed={category === item.value} onClick={() => { filter(draft, category === item.value ? '' : item.value); document.getElementById('events')?.scrollIntoView({ behavior: 'smooth' }) }}><span className="category-photo"><img src={item.image} alt="" loading="lazy" /><span>{item.symbol}</span></span>{item.label}</button>)}</div></section>
    <section className="container events-section" id="events" aria-labelledby="events-title"><div className="section-heading"><div><p className="eyebrow muted">GET OUT THERE</p><h2 id="events-title">Your next experience awaits.</h2></div><div className="filter-summary"><span role="status">{loading ? 'Loading events…' : error ? 'Events unavailable' : `${results.length} ${results.length === 1 ? 'event' : 'events'}`}</span><button className="text-link" onClick={reload} disabled={loading}>Refresh ↻</button>{(query || category) && <button className="text-link" onClick={clearFilters}>Clear filters ✕</button>}</div></div><p className="section-note">Upcoming campus events · Times in Tashkent (UTC+5)</p>
      {loading || error ? <Feedback loading={loading} error={error} retry={reload} /> : results.length ? <div className="event-grid">{results.map((event) => <EventCard key={event.id} event={event} />)}</div> : <Feedback title={events.length ? 'No matches this time.' : 'Good things are on their way.'}><p>{events.length ? 'Try another title or explore a different category.' : 'No upcoming events have been published yet. Check back soon.'}</p>{events.length > 0 && <button className="button secondary" onClick={clearFilters}>Show all events</button>}{user?.role === 'organizer' && <Link className="button" to="/organizer/new">Create an event ↗</Link>}</Feedback>}
    </section>
    <section className="community-band"><div className="container community-layout"><span className="community-mark" aria-hidden="true">✳</span><div><p className="eyebrow">MAKE ROOM FOR REAL CONNECTION</p><h2>Your people are out there.<br />Go find them.</h2><p>From a first workshop to a new campus tradition. Be part of what happens next.</p></div><Link className="button dark" to={user ? '/registrations' : '/signup'}>{user ? 'My registrations ↗' : 'Join your community ↗'}</Link></div></section>
    <section className="container organize-cta"><div><p className="eyebrow muted">BRING YOUR IDEAS TO LIFE</p><h2>Big idea. Small gathering.<br />Start something.</h2><p>Campusly helps campus organizers bring people together, manage registrations, and make every event count.</p></div><div><Link className="button secondary" to={user?.role === 'organizer' ? '/organizer/new' : '/profile'}>{user?.role === 'organizer' ? 'Create an event ↗' : 'View your account ↗'}</Link>{user?.role !== 'organizer' && <p className="small-note">Organizer access is granted by the project team.</p>}</div></section>
  </>
}

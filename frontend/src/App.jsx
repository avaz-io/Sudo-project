import { useState } from 'react'
import './App.css'

const categories = ['Academic', 'Cultural', 'Social', 'Extracurricular', 'Sports', 'Other']
const events = [
  { id: 1, title: 'AI & the Future of Learning', category: 'Academic', day: '05', time: '2:00 PM', location: 'Main Auditorium', description: 'Explore how artificial intelligence is changing education with students and guest speakers.' },
  { id: 2, title: 'Campus Culture Festival', category: 'Cultural', day: '07', time: '4:00 PM', location: 'University Courtyard', description: 'An afternoon of music, performances, and traditions from our campus community.' },
  { id: 3, title: 'Meet Your Campus Community', category: 'Social', day: '09', time: '3:00 PM', location: 'Student Lounge', description: 'Meet fellow students, exchange ideas, and discover your next campus connection.' },
  { id: 4, title: 'Build Your First Startup', category: 'Extracurricular', day: '12', time: '1:00 PM', location: 'Innovation Lab', description: 'Explore the first steps of turning an idea into a student startup.' },
  { id: 5, title: 'Interfaculty Football Cup', category: 'Sports', day: '14', time: '10:00 AM', location: 'University Sports Ground', description: 'Support your faculty and enjoy a day of friendly competition.' },
  { id: 6, title: 'Volunteer Together', category: 'Other', day: '16', time: '11:00 AM', location: 'Student Centre', description: 'Discover local volunteering opportunities and meet students who want to make a difference.' },
]

export default function App() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const results = events.filter((event) =>
    event.title.toLowerCase().includes(query.trim().toLowerCase()) &&
    (category === 'All' || event.category === category)
  )

  function resetFilters() {
    setQuery('')
    setCategory('All')
  }

  function search(event) {
    event.preventDefault()
    document.getElementById('events').scrollIntoView()
  }

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="site-header" id="home">
        <div className="container header-content">
          <a className="brand" href="#home">Campusly<span>↗</span></a>
          <nav aria-label="Main navigation"><a href="#home">Home</a><a href="#categories">Categories</a><a href="#events">Explore events →</a></nav>
        </div>
      </header>
      <main id="main">
        <section className="hero" aria-labelledby="hero-title">
          <div className="container">
            <p className="eyebrow">YOUR CAMPUS. YOUR COMMUNITY.</p>
            <h1 id="hero-title">Good things happen<br />when you <span>show up.</span></h1>
            <p className="hero-description">Discover events, meet new people, and make more of university life.</p>
            <form className="search-form" role="search" onSubmit={search}>
              <label className="search-field"><span>What are you looking for?</span><input type="search" placeholder="Search events by title" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
              <label className="category-field"><span>Category</span><select value={category} onChange={(event) => setCategory(event.target.value)}><option value="All">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
              <button className="primary-button" type="submit">Find events →</button>
            </form>
          </div>
        </section>
        <section className="container category-section" id="categories" aria-labelledby="category-title">
          <div className="section-heading"><h2 id="category-title">Explore categories</h2><button className="text-button" type="button" onClick={resetFilters}>Show all events ↗</button></div>
          <div className="category-list">{categories.map((item, index) => <button className="category-button" type="button" key={item} aria-pressed={category === item} onClick={() => setCategory(category === item ? 'All' : item)}><span className={`category-icon tone-${index}`} aria-hidden="true">{item.slice(0, 2)}</span>{item}</button>)}</div>
        </section>
        <section className="container events-section" id="events" aria-labelledby="events-title">
          <div className="section-heading"><div><p className="eyebrow section-eyebrow">SOMETHING FOR EVERYONE</p><h2 id="events-title">Find your next experience</h2></div><p className="result-count" role="status">{results.length} {results.length === 1 ? 'event' : 'events'} found</p></div>
          <p className="demo-note">Design preview · Sample events · Times shown in Tashkent time</p>
          <div className="event-grid">{results.map((event) => (
            <article className="event-card" key={event.id}>
              <div className={`event-art tone-${categories.indexOf(event.category)}`} aria-hidden="true"><span>{event.category}</span><strong>Campus<br />connections.</strong><span className="art-year">/ 2026</span></div>
              <div className="event-content"><div className="event-date"><span>NOV</span><strong>{event.day}</strong></div><div className="event-info"><p className="event-category">{event.category}</p><h3>{event.title}</h3><p>{event.location}</p><p>Nov {event.day}, 2026 · {event.time}</p></div></div>
              <details className="event-details"><summary>Event information</summary><p>{event.description}</p></details>
            </article>
          ))}</div>
          {results.length === 0 && <div className="empty-state"><h3>No events found</h3><p>Try another title or category.</p><button className="primary-button" type="button" onClick={resetFilters}>Clear filters</button></div>}
        </section>
      </main>
      <footer className="site-footer"><div className="container footer-content"><a className="brand" href="#home">Campusly</a><p>Make room for more than lectures.</p><span>University Event Manager</span></div></footer>
    </>
  )
}

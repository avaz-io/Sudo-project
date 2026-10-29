export const categories = [
  { value: 'academic', label: 'Academic', symbol: '◎', image: '/images/academic.webp' },
  { value: 'cultural', label: 'Cultural', symbol: '✺', image: '/images/cultural.webp' },
  { value: 'social', label: 'Social', symbol: '♡', image: '/images/social.webp' },
  { value: 'extracurricular', label: 'Extracurricular', symbol: '✳', image: '/images/extracurricular.webp' },
  { value: 'sports', label: 'Sports', symbol: '◉', image: '/images/sports.webp' },
  { value: 'other', label: 'Other', symbol: '↗', image: '/images/other.webp' },
]
export function categoryInfo(value) { return categories.find((item) => item.value === value) || categories[5] }
export function discoveryParams(query, category) {
  const params = new URLSearchParams()
  // Preserve input spaces while typing; trim only when matching event titles.
  if (query) params.set('q', query)
  if (category) params.set('category', category)
  return params
}
export function filterEvents(events, query, category) {
  const title = query.trim().toLowerCase()
  return events.filter((event) => event.title.toLowerCase().includes(title) && (!category || event.category === category))
}
export function formatDate(value, options = {}) { return new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Tashkent', month: 'short', day: 'numeric', year: 'numeric', ...options }).format(new Date(value)) }
export function formatTime(value) { return formatDate(value, { hour: 'numeric', minute: '2-digit', hour12: true }) }
export function toTashkentInput(value) { return new Date(new Date(value).getTime() + 5 * 60 * 60 * 1000).toISOString().slice(0, 16) }
export function eventPayload(fields) {
  const startsAt = new Date(`${fields.starts_at}:00+05:00`)
  if (!fields.title.trim() || !fields.description.trim() || !fields.location.trim()) throw new Error('Title, description and location cannot be blank.')
  if (Number.isNaN(startsAt.getTime()) || startsAt.getTime() <= Date.now()) throw new Error('Choose a future date and time in Tashkent time.')
  const capacity = fields.capacity === '' ? null : Number(fields.capacity)
  if (capacity !== null && (!Number.isSafeInteger(capacity) || capacity < 1)) throw new Error('Capacity must be a positive whole number, or leave it empty for no limit.')
  return { title: fields.title.trim(), description: fields.description.trim(), category: fields.category, location: fields.location.trim(), starts_at: startsAt.toISOString(), capacity }
}

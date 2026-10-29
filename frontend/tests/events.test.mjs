import test from 'node:test'
import assert from 'node:assert/strict'
import { eventPayload, formatTime, toTashkentInput, categoryInfo, discoveryParams, filterEvents } from '../src/data/events.js'
const future = '2099-12-31T23:30'
const fields = { title: ' Workshop ', description: ' Details ', location: ' Hall ', category: 'academic', starts_at: future, capacity: '' }
test('Tashkent input converts to UTC independently of device timezone', () => {
  const payload = eventPayload(fields)
  assert.equal(payload.starts_at, '2099-12-31T18:30:00.000Z')
  assert.equal(toTashkentInput(payload.starts_at), future)
  assert.equal(payload.capacity, null)
  assert.equal(payload.title, 'Workshop')
})
test('date formatting crosses the year boundary in Tashkent', () => {
  const output = formatTime('2099-12-31T22:00:00Z')
  assert.match(output, /2100/)
  assert.match(output, /3:00 AM/)
})
test('rejects blank fields, invalid dates and past dates', () => {
  assert.throws(() => eventPayload({ ...fields, title: '  ' }), /cannot be blank/)
  assert.throws(() => eventPayload({ ...fields, starts_at: 'bad' }), /future date/)
  assert.throws(() => eventPayload({ ...fields, starts_at: '2000-01-01T00:00' }), /future date/)
})
test('capacity is a positive whole number or unlimited', () => {
  assert.equal(eventPayload({ ...fields, capacity: '30' }).capacity, 30)
  for (const capacity of ['0','-1','1.5','bad']) assert.throws(() => eventPayload({ ...fields, capacity }), /positive whole number/)
})
test('unknown categories have a safe artwork fallback', () => {
  assert.equal(categoryInfo('unknown').value, 'other')
})

test('live search preserves spaces so a multiword title can be typed', () => {
  let query = ''
  for (const character of 'Campus Culture') {
    query = discoveryParams(query + character, '').get('q') || ''
  }
  assert.equal(query, 'Campus Culture')
  assert.equal(discoveryParams('Campus ', 'cultural').get('q'), 'Campus ')
})

test('search matches trimmed case-insensitive titles and combines with category', () => {
  const events = [
    { id: 1, title: 'Campus Culture Festival', category: 'cultural' },
    { id: 2, title: 'Campus Culture Discussion', category: 'academic' },
    { id: 3, title: 'Football Cup', category: 'sports' },
  ]
  assert.deepEqual(filterEvents(events, ' campus culture ', 'cultural').map((event) => event.id), [1])
  assert.deepEqual(filterEvents(events, 'CAMPUS CULTURE', '').map((event) => event.id), [1, 2])
  assert.deepEqual(filterEvents(events, '', 'sports').map((event) => event.id), [3])
  assert.equal(filterEvents(events, '', '').length, 3)
  assert.equal(discoveryParams('', '').toString(), '')
  assert.deepEqual(filterEvents([], '', ''), [])
})

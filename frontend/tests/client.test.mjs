import test from 'node:test'
import assert from 'node:assert/strict'
import { request, ApiError } from '../src/api/client.js'
const storage = new Map()
const events = new EventTarget()
globalThis.sessionStorage = { getItem: (key) => storage.get(key) || null }
globalThis.window = events

test('API client behavior', async (t) => {
  await t.test('public requests omit authorization and private requests include it', async () => {
    let options
    globalThis.fetch = async (url, init) => { assert.equal(url, '/api/events'); options = init; return Response.json([]) }
    await request('/events'); assert.equal(options.headers.Authorization, undefined)
    storage.set('campusly_token', 'test-token')
    await request('/events', { auth: true }); assert.equal(options.headers.Authorization, 'Bearer test-token')
  })
  await t.test('missing token prevents a private network request', async () => {
    storage.clear()
    globalThis.fetch = async () => { throw new Error('Must not run') }
    await assert.rejects(request('/users/me', { auth: true }), error => error instanceof ApiError && error.status === 401)
  })
  await t.test('sends JSON bodies and accepts logout 204', async () => {
    storage.set('campusly_token', 'test-token')
    globalThis.fetch = async (url, init) => {
      assert.equal(init.method, 'PATCH'); assert.equal(init.headers['Content-Type'], 'application/json')
      assert.deepEqual(JSON.parse(init.body), { display_name: 'Student' }); return Response.json({ display_name: 'Student' })
    }
    await request('/users/me', { auth: true, method: 'PATCH', body: { display_name: 'Student' } })
    globalThis.fetch = async () => new Response(null, { status: 204 })
    assert.equal(await request('/auth/logout', { auth: true, method: 'POST' }), null)
  })
  await t.test('private 401 expires the session; bad public login does not', async () => {
    let count = 0
    const listener = () => count++
    events.addEventListener('campusly:unauthorized', listener)
    globalThis.fetch = async () => Response.json({ detail: 'Expired' }, { status: 401 })
    await assert.rejects(request('/users/me', { auth: true }), error => error.status === 401)
    assert.equal(count, 1)
    await assert.rejects(request('/auth/login', { method: 'POST', body: {} }), error => error.status === 401)
    assert.equal(count, 1)
    events.removeEventListener('campusly:unauthorized', listener)
  })
  await t.test('preserves capacity/conflict messages and validation errors', async () => {
    for (const [status, detail] of [[400, 'This event is full'], [409, 'Already registered']]) {
      globalThis.fetch = async () => Response.json({ detail }, { status })
      await assert.rejects(request('/events/1/registration', { method: 'POST', auth: true }), error => error.status === status && error.message === detail)
    }
    globalThis.fetch = async () => Response.json({ detail: [{ msg: 'Invalid email' }] }, { status: 422 })
    await assert.rejects(request('/auth/register', { method: 'POST', body: {} }), /Invalid email/)
  })
  await t.test('handles HTML gateway errors, network errors and aborts', async () => {
    globalThis.fetch = async () => new Response('<html>Gateway error</html>', { status: 502 })
    await assert.rejects(request('/events'), error => error.status === 502)
    globalThis.fetch = async () => { throw new TypeError('Offline') }
    await assert.rejects(request('/events'), error => /Cannot connect/.test(error.message) && error.cause instanceof TypeError)
    globalThis.fetch = async () => { throw new DOMException('Aborted', 'AbortError') }
    await assert.rejects(request('/events'), error => error.name === 'AbortError')
  })
})

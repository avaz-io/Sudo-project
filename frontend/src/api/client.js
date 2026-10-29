export class ApiError extends Error {
  constructor(message, status = 0, cause) { super(message, { cause }); this.status = status }
}
export async function request(path, { method = 'GET', body, auth = false, signal } = {}) {
  const token = auth && sessionStorage.getItem('campusly_token')
  if (auth && !token) throw new ApiError('Please log in to continue.', 401)
  let response
  try {
    response = await fetch(`/api${path}`, { method, signal,
      headers: { ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Cannot connect. Check your connection and try again.', 0, error)
  }
  if (response.status === 204) return null
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && auth) window.dispatchEvent(new Event('campusly:unauthorized'))
    const message = typeof data?.detail === 'string' ? data.detail
      : Array.isArray(data?.detail) ? data.detail.map((item) => item.msg).join(' ')
      : response.status === 403 ? 'You do not have access to this action.'
      : response.status === 404 ? 'This page or event could not be found.' : 'Unable to complete the request. Please try again.'
    throw new ApiError(message, response.status)
  }
  if (data === null) throw new ApiError('The response could not be read. Refresh to check the latest status.')
  return data
}

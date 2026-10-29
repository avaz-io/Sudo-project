import { useCallback, useEffect, useState } from 'react'
import { request } from '../api/client.js'
import { AuthContext } from './AuthContext.js'
export default function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem('campusly_token'))
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(token ? 'checking' : 'anonymous')
  const [version, setVersion] = useState(0)
  const clear = useCallback(() => {
    sessionStorage.removeItem('campusly_token'); sessionStorage.removeItem('campusly_user')
    setToken(null); setUser(null); setStatus('anonymous')
  }, [])
  useEffect(() => { window.addEventListener('campusly:unauthorized', clear); return () => window.removeEventListener('campusly:unauthorized', clear) }, [clear])
  useEffect(() => {
    if (!token) return
    const controller = new AbortController()
    request('/users/me', { auth: true, signal: controller.signal }).then((account) => {
      if (controller.signal.aborted) return
      setUser(account); setStatus('authenticated'); sessionStorage.setItem('campusly_user', JSON.stringify(account))
    }).catch((error) => { if (!controller.signal.aborted && error.status !== 401) setStatus('unavailable') })
    return () => controller.abort()
  }, [token, version])
  async function authenticate(credentials, signup) {
    const data = await request(`/auth/${signup ? 'register' : 'login'}`, { method: 'POST', body: credentials })
    if (!data.access_token || !data.user) throw new Error('The account response could not be read.')
    sessionStorage.setItem('campusly_token', data.access_token); sessionStorage.setItem('campusly_user', JSON.stringify(data.user))
    setToken(data.access_token); setUser(data.user); setStatus('authenticated')
  }
  async function logout() {
    try { await request('/auth/logout', { method: 'POST', auth: true }) } catch (error) { if (error.status !== 401) throw error }
    clear()
  }
  function retry() { setStatus('checking'); setVersion((value) => value + 1) }
  function updateUser(account) { setUser(account); sessionStorage.setItem('campusly_user', JSON.stringify(account)) }
  return <AuthContext.Provider value={{ user, status, authenticate, logout, retry, updateUser }}>{children}</AuthContext.Provider>
}

import { useRef, useState } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import { request } from '../api/client.js'
export default function ProfilePage() {
  const { user, updateUser } = useAuth()
  const [name, setName] = useState(user.display_name)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const saving = useRef(false)
  async function save(event) {
    event.preventDefault()
    if (saving.current) return
    setError(''); setNotice('')
    if (!name.trim()) { setError('Please enter your name.'); return }
    saving.current = true; setBusy(true)
    try { const account = await request('/users/me', { method: 'PATCH', auth: true, body: { display_name: name.trim() } }); updateUser(account); setName(account.display_name); setNotice('Your profile has been saved.') }
    catch (error) { setError(error.message) }
    finally { saving.current = false; setBusy(false) }
  }
  return <div className="container page-space"><div className="page-heading"><p className="eyebrow muted">YOUR CAMPUSLY</p><h1>Make yourself at home.</h1><p>Your profile and account details.</p></div><div className="profile-layout"><aside className="profile-summary panel"><span className="profile-avatar" aria-hidden="true">{user.display_name.slice(0, 1).toUpperCase()}</span><h2>{user.display_name}</h2><p>{user.email}</p><span className="badge">{user.role === 'organizer' ? 'Organizer' : 'Campus member'}</span><Link className="text-link" to="/registrations">My registrations ↗</Link></aside><section className="panel"><h2>Personal information</h2><form className="stack-form" onSubmit={save} aria-busy={busy}><label htmlFor="profile-name">Display name</label><input id="profile-name" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} maxLength={100} disabled={busy} required /><label htmlFor="profile-email">Email address</label><input id="profile-email" type="email" value={user.email} readOnly /><p className="field-help">Email and account role are managed by the project team.</p>{error && <p className="alert error" role="alert">{error}</p>}{notice && <p className="alert success" role="status">{notice}</p>}<button className="button" disabled={busy || name.trim() === user.display_name}>{busy ? 'Saving…' : 'Save changes'}</button></form></section></div></div>
}

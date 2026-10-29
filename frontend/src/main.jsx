import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate,
} from 'react-router'

import './index.css'
import App from './App.jsx'
import Login from './pages/Login.jsx'

function LoginPage() {
  const navigate = useNavigate()

  async function handleLogin(credentials) {
    let response

    try {
      response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })
    } catch {
      throw new Error('Cannot connect to the sign-in service.')
    }

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(
        typeof data?.detail === 'string'
          ? data.detail
          : 'Unable to log in. Please try again.',
      )
    }

    if (!data?.access_token || !data?.user) {
      throw new Error('The sign-in service is currently unavailable.')
    }

    sessionStorage.setItem('campusly_token', data.access_token)
    sessionStorage.setItem('campusly_user', JSON.stringify(data.user))

    navigate('/', { replace: true })
  }

  return <Login onLogin={handleLogin} />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import '@fontsource-variable/montserrat/wght.css'
import '@fontsource-variable/open-sans/wght.css'
import './index.css'
import './App.css'
import App from './App.jsx'
import AuthProvider from './auth/AuthProvider.jsx'
import RequireAuth from './auth/RequireAuth.jsx'
import Layout from './components/Layout.jsx'
import AccountPage from './pages/AccountPage.jsx'
import EventPage from './pages/EventPage.jsx'
import RegistrationsPage from './pages/RegistrationsPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import OrganizerPage from './pages/OrganizerPage.jsx'
import EventEditorPage from './pages/EventEditorPage.jsx'
import ParticipantsPage from './pages/ParticipantsPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode><BrowserRouter><AuthProvider><Routes>
    <Route path="/login" element={<AccountPage key="login" />} />
    <Route path="/signup" element={<AccountPage key="signup" signup />} />
    <Route element={<Layout />}>
      <Route path="/" element={<App />} />
      <Route path="/events/:eventId" element={<EventPage />} />
      <Route path="/registrations" element={<RequireAuth><RegistrationsPage /></RequireAuth>} />
      <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
      <Route path="/organizer" element={<RequireAuth organizer><OrganizerPage /></RequireAuth>} />
      <Route path="/organizer/new" element={<RequireAuth organizer><EventEditorPage /></RequireAuth>} />
      <Route path="/organizer/:eventId/edit" element={<RequireAuth organizer><EventEditorPage /></RequireAuth>} />
      <Route path="/organizer/:eventId/participants" element={<RequireAuth organizer><ParticipantsPage /></RequireAuth>} />
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </Routes></AuthProvider></BrowserRouter></StrictMode>,
)

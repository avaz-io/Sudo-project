# Campusly frontend

React + Vite client for the existing University Event Manager API. All application changes are inside `frontend/`.

## Run locally

Keep the existing backend deployment running on `127.0.0.1:8000`.

```bash
cd ~/Sudo-project/frontend
npm ci
npm run check
npm run dev
```

Open `http://localhost:5173/` explicitly. Vite now uses a fixed port and stops with an error if an old process already occupies it, instead of silently moving to another port. Stop the older frontend server with Ctrl+C in its own terminal, then restart this one. No processes are killed automatically.

Both development and preview forward `/api` to the existing gateway at `127.0.0.1:8000`, preserving the path. If the backend is down, the UI shows a connection error; check `http://localhost:5173/api/health` for `{"status":"ok"}`.

## Seeing the older homepage after copying files?

The uploaded source was compared with the supplied full frontend package: all 45 frontend files matched. The older screenshot's letter categories and old heading are not present in the current homepage source. A screenshot cannot establish which local process or saved build served it, but the source replacement itself is correct.

There are three separate addresses:

| Address | What it serves |
| --- | --- |
| `http://localhost:5173/` | Live frontend source from `npm run dev` |
| `http://localhost:5174/` | Fresh production build from `npm run preview` |
| `http://localhost:8000/` | Existing Docker gateway; its frontend comes from its configured static directory |

Copying JSX/CSS changes source, but does not regenerate an already built Docker website. `make deploy` in this uploaded project does not build the React frontend. No Docker, backend, Makefile, or root environment changes were made in this repair.

For a fresh build preview, run:

```bash
cd ~/Sudo-project/frontend
npm run preview
```

This command rebuilds first and then serves on port 5174 with the same API proxy. Open the exact address above rather than a saved localhost tab with an unknown port. If the Docker gateway is already configured to serve `frontend/dist`, rebuilding updates those static files; otherwise coordinate the gateway's build-directory selection with the deployment owner.

For a read-only local diagnostic, use a second terminal:

```bash
cd ~/Sudo-project/frontend
npm run doctor
```

It prints this frontend folder, compares the page titles served on ports 5173/5174/8000, checks API health, and reports the count of public events. It does not read or modify credentials, accounts, database files, or deployment settings. A matching title identifies the current document version; it does not prove that every asset is the latest build.

## Empty event list

The homepage uses real API data. `/api/events` only returns **published events with a future start time**. Existing accounts do not create events automatically. Draft, cancelled, completed, and past events are excluded by the backend.

If the diagnostic shows a healthy API and zero public events, sign in with a team-provisioned organizer account, create an event with a future time, and publish it from the organizer workspace. A regular signup cannot grant itself organizer access. Sample events have not been inserted into your database.

## Pages

| URL | Purpose | Access |
| --- | --- | --- |
| `/` | Real upcoming published events, live title search, category filters | Public |
| `/signup` | Create a regular account | Public |
| `/login` | Sign in and return to the requested protected page | Public |
| `/events/:eventId` | Event details, capacity, register/cancel | Public; registration requires login |
| `/registrations` | Active registrations, organizer cancellation notices, cancel your place | Signed in |
| `/profile` | Account details and editable display name | Signed in |
| `/organizer` | Owned events, status filters and lifecycle actions | Organizer |
| `/organizer/new` | Create a draft | Organizer |
| `/organizer/:eventId/edit` | Edit an owned draft or upcoming published event | Owner |
| `/organizer/:eventId/participants` | Active participant names and registration times | Owner |
| Other URLs | Not-found page | Public |

Organizer roles are granted by the project team through the existing backend setup. Signup never grants organizer access. The backend independently enforces ownership and role checks.

## Behavior

- All event dates use Asia/Tashkent. Organizer date inputs explicitly use UTC+5 and convert to UTC for API submission, independently of the computer timezone.
- New events are drafts; publishing is a separate confirmed action. Cancelling/completing an event requires confirmation. No event deletion endpoint is used.
- Empty capacity means unlimited; other capacities must be positive whole numbers and cannot fall below current registrations.
- Registration and cancellation use existing API endpoints. Duplicate submissions are blocked while an action is pending. The server handles final capacity checks.
- JWTs use the existing sessionStorage keys. Sessions are verified with `/users/me`; a protected 401 clears the session. Logout calls the backend before clearing a successful session. Storage is per browser tab; closing that tab ends the local session.
- Profile updates submit display_name only. Email and role are read-only.
- Relative `/api` requests also work with the existing same-origin production gateway. No API secrets are bundled in frontend code.

## Design and assets

The interface adapts the supplied Figma reference to Campusly: dark purple/yellow branding, Montserrat headings, Open Sans body text, responsive layouts, shared navigation, category discovery, organizer call-to-action, and footer. Fonts are self-hosted through npm packages. Six optimized category images are extracted from the supplied Figma; they illustrate categories, not individual event photos. The current backend has no event image upload field.

This is an adaptation, not an exact reproduction of every Eventify/EventJoy screen. Payments, ticket checkout, chat, interests, email subscriptions, email changes, and password reset/change are not implemented because the existing backend has no matching endpoints. EventJoy mobile planning screens are a separate reference product.

## Verification

`npm test` covers API authentication/body/error behavior, session-expiry signals, timezone conversion and year boundaries, event validation, category fallbacks, multiword live search, and combined title/category filtering. `npm run check` runs all tests, lint, and the production build. A separate isolated backend integration check previously covered the supported workflows. Visual/browser verification remains pending: this execution environment blocked the preview hostname.

On your Mac, check:

1. Sign up, log out, sign back in; duplicate email and bad-password messages.
2. Search and filter real events; empty results; refresh.
3. Register, refresh, find the event in My registrations, cancel, and confirm removal.
4. Full events, unavailable events, and invalid event URLs.
5. Edit your display name; verify it updates in the header.
6. Regular users cannot access organizer tools.
7. With a team-provisioned organizer account: create draft, edit, publish, inspect participants, cancel; complete a published event after its start time.
8. Confirm cancelled events are visible in attendees' registrations and cannot receive new registrations.
9. Refresh protected URLs; test logout/expired sessions and a stopped backend.
10. Check mobile navigation, keyboard focus, long titles/descriptions, and layouts at roughly 375, 768, and 1440px.

## Git hygiene

Commit source, package manifests and lockfile, tests, and referenced public assets. Do not commit node_modules, dist, local secrets, logs, temporary archives/backups, or the original Figma archive. Keep package-lock.json committed for reproducible Docker/npm ci builds.

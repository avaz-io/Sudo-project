# CLAUDE.md

University Event Manager ("Campusly"): a midterm project where students browse and register for university events and organizers create and manage them. Source of truth for requirements: the project requirements PDF (FR-01…FR-12, NFR-01…NFR-05). The design notes are in `design/design.md`.

Repository layout: `backend/` (FastAPI API), `frontend/` (React app, not yet created), `design/`, `tests/`.

## Backend commands

All commands run from `backend/`.

```powershell
# One-time setup
python -m venv .venv
.venv\Scripts\Activate.ps1          # bash: source .venv/Scripts/activate
pip install -r requirements.txt
Copy-Item .env.example .env         # then set SECRET_KEY

# Run the dev server (http://localhost:8000, docs at /docs)
uvicorn app.main:app --reload
```

- Dependencies live in `backend/requirements.txt`. Add new packages there with a minimum version (`pkg>=x.y`).
- Use plain `uvicorn`, not `uvicorn[standard]`. Its extras pull in PyYAML, which has no wheel for the team's Python 3.15 yet.
- Settings come from `backend/.env` (see `.env.example`). `SECRET_KEY` is required and the app won't start without it. Never commit `.env`.
- Tables are created on startup by `Base.metadata.create_all`, which does **not** alter existing tables. After changing a model during development, delete `backend/event_manager.db` and restart. Switch to Alembic before the schema has data you need to keep.
- Interactive API docs: http://localhost:8000/docs. Use "Authorize" and paste a token from `/api/auth/login`.

## Backend architecture

```
backend/app/
  main.py            FastAPI app, CORS, router mounting under /api, table creation
  core/config.py     Settings (pydantic-settings, reads .env)
  core/security.py   Argon2 password hashing (pwdlib), JWT create/decode (PyJWT)
  db/session.py      Engine, SessionLocal, get_db dependency (SQLite FK pragma on)
  db/base.py         DeclarativeBase
  db/types.py        UTCDateTime column type, str_enum() helper
  models/            SQLAlchemy 2.0 ORM: User, Event, Registration + enums
  schemas/           Pydantic v2 request/response models
  api/deps.py        DbSession, OptionalUser, CurrentUser, Organizer dependencies
  api/routes/        One router per resource: auth, users, events, registrations
  services/          Business rules (event lifecycle, registration/capacity logic)
```

Request flow: route → `services/` function → ORM → DB. Routes stay thin. They parse input, call a service, and return a schema.

Key domain rules (from the requirements):
- Roles: `user` (default on signup) and `organizer` (granted by setup script/DB, never via the API).
- Event status: `draft → published | cancelled`, `published → cancelled` (before start), `published → completed` (after start, manual). Publishing requires a future `starts_at`.
- Drafts are visible only to their organizer. Return 404 to everyone else, not 403.
- Only the owning organizer may edit, change status, or view participants of an event.
- One `Registration` row per (user, event), enforced by a unique constraint. Re-registering reactivates the cancelled row instead of inserting a new one.
- Only `active` registrations count toward capacity. `capacity = NULL` means unlimited. Capacity can't drop below the active count.
- Registration is allowed only for published events that haven't started and have room. The capacity check and the insert must happen in one transaction that locks the event row (`with_for_update()`), so concurrent requests can't overbook (NFR-04).
- Logout increments `user.token_version`, which invalidates all of that user's existing JWTs.

## Coding guidelines

- **SQLAlchemy 2.0 style only**: `Mapped[...]`/`mapped_column`, `select()` + `db.scalars()`/`db.execute()`. No legacy `db.query()`.
- **Sync endpoints** (`def`, not `async def`). The DB driver is sync, and FastAPI runs these in a threadpool.
- **Schemas**: request bodies subclass `InputModel` (strips whitespace, forbids unknown fields). Responses subclass `APIModel` (`from_attributes=True`). Always set `response_model` on routes. Never return ORM objects that include `password_hash`.
- **Dependencies**: use the `Annotated` aliases from `api/deps.py` (`DbSession`, `CurrentUser`, `OptionalUser`, `Organizer`) instead of writing `Depends(...)` inline.
- **Authorization is a backend responsibility.** Check ownership in the service layer on every mutating or organizer endpoint, even if the UI hides the button.
- **Errors**: raise `HTTPException` with a human-readable `detail` the frontend can show directly. Status codes: 400 rule violation (e.g. event full, wrong status), 401 not authenticated / bad credentials, 403 wrong role or not owner, 404 not found or hidden draft, 409 duplicate (email, active registration), 422 validation (automatic).
- **Datetimes**: always timezone-aware. Store with the `UTCDateTime` column type (UTC), get "now" from `datetime.now(UTC)` (or `db.types.utcnow`), and accept ISO 8601 with offset from clients (`AwareDatetime`). `UNIVERSITY_TIMEZONE` is for display and docs only.
- **Enums**: Python `StrEnum` + `str_enum()` column helper (stores lowercase values as VARCHAR). The JSON values are the same lowercase strings.
- **Transactions**: services call `db.commit()` once per use case. Use `db.flush()` mid-function when you need generated IDs.
- **Secrets**: none in code or Git. Add new settings to `Settings` *and* `.env.example`.
- Style: PEP 8, type hints on all functions, 100-char lines, absolute imports from `app.`.
- `api/stubs.py` (`not_implemented()` → 501) marks endpoints whose contract exists but whose logic doesn't. Replace each one as you implement it, then delete the module.

## API conventions for the React frontend

- Base URL `/api`. JSON in and out. Field names are `snake_case`.
- Auth: `POST /api/auth/login` returns `{access_token, token_type, user}`. Send `Authorization: Bearer <token>` on protected calls. On a 401, the frontend should clear the token and redirect to login.
- Error body is always `{"detail": ...}`. It's a string for app errors and a list of field errors for 422.
- CORS allows origins listed in `CORS_ORIGINS` (default Vite dev server `http://localhost:5173`).

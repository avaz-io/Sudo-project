# University Event Manager

Campusly is a university event manager with a React/Vite frontend, FastAPI backend,
and SQLite database. Docker builds the frontend and serves it alongside the API
through one Nginx address or ngrok domain.

## Run with Docker

Install Docker Engine with the Compose plugin. Run commands from the repository
root; Node, npm, Make, and a manually built `frontend/dist/` are not required for
deployment.

1. Copy `.env.example` to `.env` if you do not already have a root `.env`.
2. Generate a key with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
   and put it in `.env` as `SECRET_KEY`. Keep this key between deployments.
3. Build, check, and start the application:

   ```bash
   docker compose up --build --force-recreate --always-recreate-deps \
     --wait --wait-timeout 180 web
   ```

Both backend tests and frontend checks must succeed before the backend starts.
The gateway waits for a healthy backend and checks the frontend homepage and API.
`make deploy` is an optional shortcut for the same Docker command.

- Website: http://localhost:8000/
- Login page: http://localhost:8000/login
- Signup page: http://localhost:8000/signup
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health
- Set `WEB_PORT` in `.env` to use a different available port.
- Public demo: add `NGROK_AUTHTOKEN` to `.env`, then follow the deployment guide.
- Verification: `python3 devops/verify_routing.py` or `make verify`.
- Stop containers while keeping data: `docker compose down --remove-orphans`.

The Node build stage uses the frontend's package lockfile, and the resulting assets
are copied into the Nginx image. The current login page already calls
`/api/auth/login` through the shared address. `FRONTEND_DIST_DIR` is no longer used.

See [the deployment guide](devops/README.md) for configuration, ngrok logs, and
check details, and database persistence.

## Team folders

| Location | Owner | Purpose |
| --- | --- | --- |
| `frontend/` | Azamat Eshqo'ziyev | Website pages, forms, navigation, and frontend integration. |
| `backend/` | Olmosbek Rustamov | API, database models, authentication, and application logic. |
| `tests/` | Avazbek Soibnazarov | Test cases, automated tests, and defect reports. |
| `design/` | Avazbek Soibnazarov | UI/UX layouts, wireframes, user flows, and design assets. |
| Repository root | Quvonchbek Qurbonov | DevOps, deployment, shared configuration, and project management files. |

Deployment configuration lives at the repository root and in `devops/`. The Docker
setup uses the backend and tests as supplied by their owners.

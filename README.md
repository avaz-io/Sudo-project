# University Event Manager

Campusly is a university event manager with a FastAPI backend and SQLite database.
The frontend has not been added yet. An Nginx gateway is ready to serve its static
production build and the backend through one local address or ngrok domain.

## Run with Docker

Install Docker Engine with the Compose plugin and GNU Make. Run commands from the
repository root.

1. Copy `.env.example` to `.env` if you do not already have a root `.env`.
2. Generate a key with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
   and put it in `.env` as `SECRET_KEY`. Keep this key between deployments.
3. Run the tests and start the backend and gateway:

   ```bash
   make test
   make deploy
   ```

`make deploy` builds the images, reruns every test, and starts the backend only after
the test job succeeds. The gateway starts after the backend becomes healthy. Both
services must pass their health checks before the command returns success.

- Website: http://localhost:8000/ (HTTP 503 until a frontend build is supplied)
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health
- Public demo: add `NGROK_AUTHTOKEN` to the root `.env`, then run `make demo`.
- Routing and test-gate verification: `make verify`.
- Stop the containers while keeping the database: `make down`.

## Connect the frontend when it is ready

The frontend owner should provide a static production build containing `index.html`
and its assets, with API calls using relative paths such as `/api/events`. Set
`FRONTEND_DIST_DIR=./frontend/dist` in the root `.env` if that is the build output,
then run `make deploy` locally or `make demo` to share it. The directory must exist
before deployment. Nginx serves pages and forwards API traffic under the same origin.

See [the deployment guide](devops/README.md) for configuration, ngrok logs, and
the frontend handoff requirements.

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

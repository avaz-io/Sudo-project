# Website deployment

Docker builds the current React/Vite frontend, runs its checks and the backend
suite, and serves the compiled site through Nginx. You do not need Node, npm,
a host `dist/` directory, or Make to deploy. Make provides optional shortcuts;
Python 3.10+ is needed for `devops/verify_routing.py`.

## Current blocking frontend issue

The production frontend build succeeds and all 52 backend tests pass. The existing
frontend lint command fails at `frontend/src/main.jsx:14` with
`react-refresh/only-export-components`: `LoginPage` is defined in the entry module
without an export. The usual frontend fix is to move it into an exported component
module and import it into `main.jsx`.

Frontend lint is a required startup check. Until the frontend owner fixes this
error, `make test`, `make deploy`, `make demo`, and the full `make verify` command
return a failure. This setup keeps the owner's source and lint configuration
unchanged. A successful production build alone does not satisfy the deployment gate.

The built images were checked independently in disposable containers: compiled
HTML, JavaScript, CSS, `/login` refresh, API/docs routes, registration, login,
bearer authentication, login errors, and HTTP/HTTPS redirects passed. That runtime
compatibility check does not waive the failing lint job.

## Local preview while lint is pending

To inspect the application before the frontend owner fixes lint, opt in explicitly:

```bash
docker compose -p campusly-preview -f compose.yaml -f compose.preview.yaml up \\
  --build --force-recreate --always-recreate-deps --wait --wait-timeout 180 web
```

`compose.preview.yaml` defers only the lint command. The frontend production build,
any available frontend test script, and all backend tests remain required. There
is currently no frontend test script. Normal deployment continues to require lint.
The preview's separate project name gives it its own SQLite volume.

Open the root `.env`'s `WEB_PORT` (8001 in the current local environment). To stop
this preview while keeping its data:

```bash
docker compose -p campusly-preview -f compose.yaml -f compose.preview.yaml down
```

## Configure the root environment

Copy `.env.example` to `.env` if a root `.env` does not already exist. Set
`SECRET_KEY` to a random value and keep it between deployments. For example,
generate a value with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Required backend JWT signing secret | No default |
| `WEB_PORT` | Shared website/API port on the host's loopback interface | `8000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime | `1440` |
| `CORS_ORIGINS` | JSON list of allowed browser origins | `[]` |
| `UNIVERSITY_TIMEZONE` | Backend display timezone | `Asia/Tashkent` |
| `NGROK_AUTHTOKEN` | Required only for the public demo | No default |

An existing `BACKEND_PORT` remains a fallback when `WEB_PORT` is unset. Choose a
free port, such as `WEB_PORT=8001`, if another project uses 8000. Older
`FRONTEND_DIST_DIR` values are no longer used: frontend assets are packaged in the
web image, and no host frontend directory is mounted.

The root `.env` is ignored by Git and excluded from image builds. Backend settings
and the ngrok token go only to their respective containers. No root secrets are
passed to Vite or included in the frontend build.

Validate without printing secrets:

```bash
docker compose config --quiet
```

## Build and run locally

After the frontend lint issue is fixed, run from the repository root:

```bash
docker compose up --build --force-recreate --always-recreate-deps \
  --wait --wait-timeout 180 web
```

Or use `make deploy`. The pipeline is:

1. The Node 24 build stage installs the frontend's locked dependencies with
   [`npm ci`](https://docs.npmjs.com/cli/commands/npm-ci/) and runs the existing
   [`npm run build`](https://vite.dev/guide/static-deploy) script. A build error
   prevents deployment. The resulting `dist/` is copied into the Nginx runtime image.
2. The `frontend-checks` job runs `npm run lint`, then `npm run test --if-present`.
   There is currently no frontend test script; lint is the available frontend check.
3. The `tests` job runs every existing backend test with the supplied `pytest.ini`.
   Both jobs must complete successfully before the backend can start.
4. The backend must pass `/api/health` before Nginx starts. Nginx checks both the
   frontend homepage and the proxied API health endpoint before becoming healthy.

Deployment recreates the check jobs on every invocation, including unchanged
sources. It can interrupt a running demo. The readiness timeout is 180 seconds;
image builds happen before readiness checks.

At the configured `WEB_PORT` (8000 by default), open:

- `http://localhost:8000/` for the existing frontend homepage.
- `http://localhost:8000/login` for the React login page.
- `http://localhost:8000/docs` for API documentation.
- `http://localhost:8000/api/health` for API health.

Only the web service publishes a host port. Backend, web, and frontend-check
containers run as non-root users with read-only root filesystems, temporary `/tmp`
filesystems, and dropped Linux capabilities. This host rejects execution with
`no-new-privileges`, so that option remains at its default.

## Run checks separately

```bash
docker compose build web frontend-checks tests
docker compose run --rm --no-deps frontend-checks
docker compose run --rm --no-deps tests
```

`make test` runs those commands in sequence and stops at the first failure. One-off
check containers are removed afterward. Backend tests use isolated temporary
SQLite databases and never mount the application database volume.

## One origin for frontend and backend

| Path | Destination |
| --- | --- |
| `/` and `/login` | Compiled frontend, with SPA fallback to `index.html` |
| `/assets/...` | Built JavaScript/CSS; missing assets return 404 |
| `/api` and `/api/...` | FastAPI, preserving the path and query string |
| `/docs`, `/redoc`, `/openapi.json` | FastAPI documentation |

The current login code already calls `/api/auth/login` using a relative URL.
Nginx forwards those requests to `backend:8000` under the same origin, so a separate
frontend API hostname and CORS allowlist are unnecessary for this deployment.
The public host, port, and forwarded HTTPS scheme are preserved in API redirects.

## Share through ngrok

Set `NGROK_AUTHTOKEN` in the root `.env`, then run:

```bash
docker compose -f compose.yaml -f compose.ngrok.yaml up \
  --build --force-recreate --always-recreate-deps \
  --wait --wait-timeout 180 ngrok
docker compose -f compose.yaml -f compose.ngrok.yaml logs --tail=50 ngrok
```

Or use `make demo`. The optional ngrok service waits for a healthy web service,
then forwards to `http://web:8080`. The URL in its logs serves both the website and
API. An empty token rejects configuration before startup. A live public tunnel
has not been verified without a supplied authtoken; a running ngrok container does
not by itself prove that its public endpoint has been established.

Keep the Docker host online while sharing the URL. The current frontend lint
failure also blocks this command.

## Verify the integrated application

```bash
python3 devops/verify_routing.py
```

Or use `make verify`. This builds all images and uses an isolated Compose project
with an automatically assigned loopback port. It forces backend tests and frontend
checks to fail in separate cases, confirming that each gate prevents both backend
and web startup. It then runs the real checks and, if successful, verifies the
actual compiled frontend, hashed assets, login page refresh, API/docs routes,
redirect headers, and registration/login requests through the gateway.

There is no frontend fixture or host bind mount. Test accounts exist only in the
verification project's disposable database. Containers, its volume, and temporary
overrides are removed afterward; the normal deployment and its data are untouched.
The intentional failures appear before `PASS` messages for the negative checks.
The current real lint failure prevents the full verification from passing.

This HTTP smoke check verifies serving and API connectivity. It does not execute
React in a browser or replace frontend component/browser tests.

## Logs and shutdown

```bash
docker compose ps --all
docker compose logs --tail=100
docker compose down --remove-orphans
```

The corresponding shortcuts are `make status`, `make logs`, and `make down`.
`tests` and `frontend-checks` showing `Exited (0)` are expected successful results.
Shutdown includes the optional ngrok container and preserves the
`campusly_backend-data` named volume at `/data/event_manager.db` in the backend.
Do not add `--volumes` when shutting down the normal deployment if you need its data.
The disposable verification command uses `--volumes` only for its own project.

SQLite data stays on its Docker host. Moving the project to another host requires
moving the database separately. Backend startup creates missing tables but does
not migrate existing schemas; coordinate schema changes with the backend owner.

## Maintain dependencies

The root Dockerfile applies `devops/constraints.txt` to the unchanged
`backend/requirements.txt`. To regenerate constraints with uv:

```bash
uv pip compile backend/requirements.txt --python-version 3.12 --universal --no-annotate --output-file devops/constraints.txt
```

Frontend dependencies come from the unchanged `frontend/package-lock.json`.
Keep that lockfile consistent with its package manifest; `npm ci` rejects a mismatch.
Python, Node, Nginx, and ngrok images are pinned by digest. After source, dependency,
or image updates, rerun checks and deployment verification.

The backend suite currently reports one upstream Starlette TestClient deprecation
warning about `httpx`; all 52 backend tests pass despite that warning.

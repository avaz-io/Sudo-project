# Website deployment

Run all commands from the repository root. You need Docker Engine with a Compose
plugin that supports `up --wait`, GNU Make, and Python 3.10+ for the initial secret
and routing verification. This setup was exercised with Docker Engine 29.8.0 and
Compose 5.5.1.

## One address for the website

The request path is browser → ngrok → Nginx (`web:8080`) → frontend files or FastAPI
(`backend:8000`). Only Nginx publishes a host port. The backend stays on the internal
Compose network, and its SQLite database stays in the existing named volume.

| Public path | Destination |
| --- | --- |
| `/` and frontend routes such as `/events/123` | Frontend files, with SPA fallback to `index.html` |
| `/assets/...` | Frontend assets; missing assets return HTTP 404 |
| `/api` and `/api/...` | FastAPI, preserving the original path and query string |
| `/docs`, `/redoc`, and `/openapi.json` | FastAPI documentation |

Nginx [serves files and forwards API requests](https://nginx.org/en/docs/beginners_guide.html)
under the same origin. The frontend should call `/api/...`; the default
`CORS_ORIGINS=[]` works for that arrangement.

## Configure once

Copy the root `.env.example` to the root `.env` if that file does not exist. Generate
a key with the following command, then set `SECRET_KEY` to its output in `.env`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep the key between deployments so existing login tokens remain valid. The root
`.env` is ignored by Git and excluded from the Docker build context. Compose passes
the configured backend settings into its container; no `backend/.env` is needed.
The ngrok token is passed only to the ngrok container.

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Required JWT signing secret | No default |
| `WEB_PORT` | Shared website and API port on the host's loopback interface | `8000` |
| `FRONTEND_DIST_DIR` | Existing directory containing the static frontend build | `./devops/site` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime | `1440` |
| `CORS_ORIGINS` | JSON array of allowed browser origins | `[]` |
| `UNIVERSITY_TIMEZONE` | Backend display timezone | `Asia/Tashkent` |
| `NGROK_AUTHTOKEN` | Required only for the public demo | No default |

An existing `BACKEND_PORT` value remains a fallback when `WEB_PORT` is unset.
`FRONTEND_DIST_DIR` is resolved relative to the repository root and mounted read-only.
A nonexistent directory rejects deployment; Compose will not create directories
inside the frontend owner's folder.

Validate the base configuration without printing secrets:

```bash
docker compose config --quiet
```

## Test and deploy

```bash
make test
make deploy
make status
```

`make test` builds the `tests` Dockerfile target and runs the complete `tests/`
suite with the repository's existing `pytest.ini`. It returns a failing status if
pytest fails. Tests use temporary SQLite databases, receive a test-only secret,
and never mount the application database volume.

`make deploy` builds the backend, test, and Nginx images and recreates the test job
on every invocation.
The backend depends on the tests with
[`service_completed_successfully`](https://docs.docker.com/compose/how-tos/startup-order/),
so it cannot start unless that job exits successfully. The command waits for the
backend's `/api/health` check, then starts Nginx and checks that health endpoint
through the proxy. It uses a 180-second readiness timeout. A failed test run prevents
both the new backend and gateway containers from starting. A deployment recreates
containers and can interrupt an existing local demo.

The backend and gateway run as non-root users with dropped Linux capabilities and
read-only root filesystems. Their `/tmp` directories are temporary; the backend's
`/data` is its persistent volume. The gateway listens on `127.0.0.1:8000` on the host
by default. Open `/docs` for interactive API documentation, `/api/health` for health
status, or `/api/events` for public events.
This Docker host rejects process execution with `no-new-privileges` enabled, so
Compose leaves that setting at its default.

The default `devops/site/` directory is intentionally empty. Until a frontend build
is supplied, page requests return HTTP 503 with a short availability message, and
the API remains usable. Gateway health checks cover the API; an API-only deployment
can therefore be healthy while the frontend is still unavailable.

For recent output and service exit codes:

```bash
make logs
make status
```

`tests` showing `Exited (0)` is the expected successful result.

## Frontend handoff

The frontend owner needs to provide:

1. A static production build containing `index.html` and its assets. The build must
   target the site root `/`, and its files and directories must be readable by Nginx.
2. API requests using relative URLs such as `/api/events` and `/api/auth/login`.
   Keep `/api`, `/docs`, `/redoc`, and `/openapi.json` reserved for the backend.
3. The package manifest, dependency lockfile, build command, and test command so
   frontend builds and tests can be added to the Docker pipeline once they exist.

For a frontend producing `frontend/dist/`, set these values in the root `.env`
after the frontend owner builds it:

```dotenv
WEB_PORT=8000
FRONTEND_DIST_DIR=./frontend/dist
```

Then run `make deploy` or `make demo`. Page refreshes on SPA routes are supported.
The current setup serves a prebuilt directory; it does not install frontend
dependencies, build nonexistent source, or run frontend tests that have not been
provided. Node and the appropriate package manager are needed where that frontend
build is produced; the Nginx container only serves its output.

Docker, Make, the root `SECRET_KEY`, a valid `NGROK_AUTHTOKEN`, and an online host
with internet access are the remaining requirements for sharing the site. The
frontend receives no root `.env` secrets.

## Share through ngrok

Add your ngrok authtoken as `NGROK_AUTHTOKEN` in the root `.env`, then run:

```bash
make demo
docker compose -f compose.yaml -f compose.ngrok.yaml logs --tail=50 ngrok
```

`make demo` uses the optional `compose.ngrok.yaml` override. It reruns the tests,
waits for a healthy backend and gateway, and starts the
[official ngrok Docker agent](https://ngrok.com/download/docker) forwarding to
`http://web:8080` on the Compose network. An empty token rejects the command before
services start. The HTTPS URL serves the frontend at `/`, API routes under `/api`,
and API documentation at `/docs`. Nginx preserves the forwarded public host and
HTTPS scheme so backend redirects keep the public address.

The base deployment works without an ngrok token. The ngrok image, CLI, configuration,
and missing-token check have been verified; establishing a live public tunnel still
requires your valid authtoken. Compose waiting for the ngrok container to run does
not verify that ngrok has established a public endpoint; check its logs for the URL.

## Verify routing and the deployment gate

```bash
make verify
```

This builds the images and runs all existing backend tests in a separate Compose
project with a temporary static frontend fixture and an automatically assigned
loopback port. It checks frontend pages, SPA fallback, assets, missing assets,
hidden files, API routes and query strings, documentation, and HTTP/HTTPS redirect
headers. It also checks API availability without a frontend build and forces the
test job to fail to confirm that neither backend nor gateway starts.

The fixture is created under the ignored root `.cache/` directory so it is visible
to the Docker daemon. The check removes its own containers, volume, and fixture
afterward; the normal deployment and database are untouched. The intentional test
failure appears in the output before the final `PASS` message. These checks verify
gateway behavior with a fixture; the real frontend still needs its owner's tests.

## Stop and preserve data

```bash
make down
```

This removes the project's containers, including the optional ngrok container, and
keeps the `campusly_backend-data` named volume. The SQLite database is stored at
`/data/event_manager.db` in the backend container and survives container recreation.
Starting again with `make deploy` reruns the tests and reuses that volume. Avoid
adding `--volumes` to shutdown commands if you need to keep the database.

This demo uses one Uvicorn worker and the backend's existing SQLite configuration.
Backend startup creates missing tables; it does not migrate existing table schemas.
Coordinate schema changes and migrations with the backend owner.

## Maintain dependencies

The Dockerfile reads `backend/requirements.txt` without modifying it and applies
the exact package versions in `devops/constraints.txt` to both image targets.
The runtime target contains backend source; the test target also contains the
existing test suite and pytest configuration. No source directories are mounted
from the host.

After the backend owner changes dependencies, regenerate constraints with `uv`:

```bash
uv pip compile backend/requirements.txt --python-version 3.12 --universal --no-annotate --output-file devops/constraints.txt
make test
```

The Python, Nginx, and ngrok base images are pinned by digest. Update those digests
deliberately and rerun the test and deployment checks when changing images.

## Validation performed

- All 52 existing tests pass inside the read-only test container.
- A temporary Compose override forcing the test job to exit with code 1 prevented
  both backend and gateway from ever starting; no application or test source was changed.
- API health, OpenAPI, interactive docs, and the public event list returned HTTP 200.
- Container recreation reran the full test suite and preserved the SQLite database
  and volume contents across `make down` followed by `make deploy`.
- The ngrok override validates, its container reports agent version 3.39.13, and
  `make demo` rejects an empty token. A live tunnel awaits your token.
- `make verify` passes for a static frontend fixture, including SPA routes, assets,
  missing frontend behavior, preserved API paths, and HTTPS redirects through Nginx.

The current dependency set reports one Starlette TestClient deprecation warning
about `httpx`; it does not fail the suite.

# Backend deployment

Run all commands from the repository root. You need Docker Engine with a Compose
plugin that supports `up --wait`, GNU Make, and Python 3 to generate the initial
secret. This setup was exercised with Docker Engine 29.8.0 and Compose 5.5.1.

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
| `BACKEND_PORT` | Backend port on the host's loopback interface | `8000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime | `1440` |
| `CORS_ORIGINS` | JSON array of allowed browser origins | `[]` |
| `UNIVERSITY_TIMEZONE` | Backend display timezone | `Asia/Tashkent` |
| `NGROK_AUTHTOKEN` | Required only for the public demo | No default |

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

`make deploy` builds both images and recreates the test job on every invocation.
The backend depends on the tests with
[`service_completed_successfully`](https://docs.docker.com/compose/how-tos/startup-order/),
so it cannot start unless that job exits successfully. The command waits for the
backend's `/api/health` check and uses a 180-second readiness timeout.
A failed test run prevents the new backend container from starting. A deployment
recreates containers and can interrupt an existing local demo.

The backend runs as a non-root user with dropped Linux capabilities and a
read-only root filesystem. `/tmp` is temporary and `/data` is its persistent volume.
It listens on `127.0.0.1:8000` on the host by default. Open `/docs` for interactive
API documentation, `/api/health` for health status, or `/api/events` for public events.
This Docker host rejects process execution with `no-new-privileges` enabled, so
Compose leaves that setting at its default.

For recent output and service exit codes:

```bash
make logs
make status
```

`tests` showing `Exited (0)` is the expected successful result.

## Share through ngrok

Add your ngrok authtoken as `NGROK_AUTHTOKEN` in the root `.env`, then run:

```bash
make demo
docker compose -f compose.yaml -f compose.ngrok.yaml logs --tail=50 ngrok
```

`make demo` uses the optional `compose.ngrok.yaml` override. It reruns the tests,
waits for a healthy backend, and starts the
[official ngrok Docker agent](https://ngrok.com/download/docker) forwarding to
`http://backend:8000` on the Compose network. An empty token rejects the command
before services start. Find the HTTPS URL in the ngrok logs and append `/docs` or
`/api/health` to it. No frontend container is involved.

The base deployment works without an ngrok token. The ngrok image, CLI, configuration,
and missing-token check have been verified; establishing a live public tunnel still
requires your valid authtoken. Compose waiting for the ngrok container to run does
not verify that ngrok has established a public endpoint; check its logs for the URL.

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

The Python and ngrok base images are pinned by digest. Update those digests
deliberately and rerun the test and deployment checks when changing images.

## Validation performed

- All 52 existing tests pass inside the read-only test container.
- A temporary Compose override forcing the test job to exit with code 1 prevented
  the backend from ever starting; no application or test source was changed.
- API health, OpenAPI, interactive docs, and the public event list returned HTTP 200.
- Container recreation reran the full test suite and preserved the SQLite database
  and volume contents across `make down` followed by `make deploy`.
- The ngrok override validates, its container reports agent version 3.39.13, and
  `make demo` rejects an empty token. A live tunnel awaits your token.

The current dependency set reports one Starlette TestClient deprecation warning
about `httpx`; it does not fail the suite.

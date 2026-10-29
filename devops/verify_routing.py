"""Exercise the website gateway in an isolated, disposable Compose project."""

import json
import os
import subprocess
import tempfile
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


def fetch(
    base_url: str,
    path: str,
    expected_status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, Message]:
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(Request(base_url + path, headers=headers or {}), timeout=5)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == expected_status, f"{path}: HTTP {response.status}"
        return response.read(), response.headers


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = f"campusly-routing-check-{uuid4().hex[:8]}"
    compose_files = ["-f", str(root / "compose.yaml")]
    cache = root / ".cache"
    cache.mkdir(exist_ok=True)

    # Keep bind mounts in the workspace, which is shared with the Docker daemon.
    with tempfile.TemporaryDirectory(prefix="routing-", dir=cache) as directory:
        workspace = Path(directory)
        workspace.chmod(0o755)
        frontend = workspace / "frontend"
        frontend.mkdir(mode=0o755)
        assets = frontend / "assets"
        assets.mkdir(mode=0o755)
        index = frontend / "index.html"
        html = "<!doctype html><title>Routing fixture</title><main>Campusly routing fixture</main>"
        index.write_text(html)
        (assets / "app.js").write_text("console.log('routing fixture');")
        (frontend / ".env").write_text("fixture-only")

        environment = os.environ.copy()
        environment.update(WEB_PORT="0", FRONTEND_DIST_DIR=str(frontend))

        def compose(
            *args: str, check: bool = True, capture: bool = False
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["docker", "compose", "-p", project, *compose_files, *args],
                cwd=root,
                env=environment,
                check=check,
                capture_output=capture,
                text=True,
            )

        try:
            compose(
                "up", "--build", "--force-recreate", "--always-recreate-deps",
                "--wait", "--wait-timeout", "180", "web",
            )
            address = compose("port", "web", "8080", capture=True).stdout.strip()
            base_url = f"http://{address}"

            for path in ["/", "/events/123"]:
                body, _ = fetch(base_url, path)
                assert body.decode() == html, path
            body, headers = fetch(base_url, "/assets/app.js")
            assert body == b"console.log('routing fixture');"
            assert "javascript" in headers["Content-Type"]
            fetch(base_url, "/assets/missing.js", 404)
            fetch(base_url, "/.env", 404)

            body, _ = fetch(base_url, "/api/health")
            assert json.loads(body) == {"status": "ok"}
            body, _ = fetch(base_url, "/api/events?search=routing-fixture")
            assert json.loads(body) == []
            body, _ = fetch(base_url, "/api/missing", 404)
            assert json.loads(body) == {"detail": "Not Found"}
            body, _ = fetch(base_url, "/openapi.json")
            assert "/api/health" in json.loads(body)["paths"]
            for path in ["/docs", "/docs/oauth2-redirect", "/redoc"]:
                _, headers = fetch(base_url, path)
                assert "text/html" in headers["Content-Type"], path

            _, headers = fetch(base_url, "/api/events/", 307)
            assert headers["Location"] == f"{base_url}/api/events"
            _, headers = fetch(
                base_url, "/api/events/?search=fixture", 307,
                {"Host": "campusly.example", "X-Forwarded-Proto": "https"},
            )
            assert headers["Location"] == "https://campusly.example/api/events?search=fixture"
            print("PASS: frontend, SPA routes, assets, API, docs, and HTTPS redirects.", flush=True)

            index.unlink()
            body, _ = fetch(base_url, "/", 503)
            assert b"Frontend build is not available yet" in body
            fetch(base_url, "/api/health")
            print("PASS: missing frontend returns 503 while the API stays available.", flush=True)

            compose("down", "--volumes")
            override = workspace / "fail-tests.json"
            override.write_text(json.dumps({"services": {
                "tests": {"command": ["python", "-c", "raise SystemExit(1)"]},
            }}))
            compose_files.extend(["-f", str(override)])
            result = compose(
                "up", "--no-build", "--force-recreate", "--wait",
                "--wait-timeout", "30", "web", check=False,
            )
            assert result.returncode != 0, "Failing tests must reject deployment"
            for service in ["backend", "web"]:
                container = compose("ps", "--all", "--quiet", service, capture=True).stdout.strip()
                state = json.loads(subprocess.check_output(
                    ["docker", "inspect", "--format", "{{json .State}}", container], text=True,
                ))
                assert state["Status"] == "created", f"{service} started after failed tests"
                assert state["StartedAt"] == "0001-01-01T00:00:00Z", service
            print("PASS: failing tests prevent both backend and gateway startup.", flush=True)
        finally:
            compose("down", "--volumes")


if __name__ == "__main__":
    main()

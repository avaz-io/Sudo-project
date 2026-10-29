"""Verify the compiled website and both deployment gates in a disposable project."""

import json
import os
import subprocess
import tempfile
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


class AssetLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"src", "href"} and value and value.startswith("/assets/"):
                self.urls.add(value)


def fetch(
    base_url: str,
    path: str,
    expected_status: int = 200,
    headers: dict[str, str] | None = None,
    payload: dict[str, str] | None = None,
) -> tuple[bytes, Message]:
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(base_url + path, data=data, headers=request_headers)
    try:
        response = opener.open(request, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == expected_status, f"{path}: HTTP {response.status}"
        return response.read(), response.headers


def verify_site(base_url: str) -> None:
    html, headers = fetch(base_url, "/")
    assert "text/html" in headers["Content-Type"]
    assert b'id="root"' in html
    assert b"/src/main.jsx" not in html, "The gateway served unbuilt Vite source"
    body, _ = fetch(base_url, "/login")
    assert body == html, "Refreshing the React login route must return the app shell"

    assets = AssetLinks()
    assets.feed(html.decode())
    assert any(url.endswith(".js") for url in assets.urls)
    assert any(url.endswith(".css") for url in assets.urls)
    for url in assets.urls:
        body, headers = fetch(base_url, url)
        assert body, f"Empty asset: {url}"
        if url.endswith(".js"):
            assert "javascript" in headers["Content-Type"], url
        elif url.endswith(".css"):
            assert "text/css" in headers["Content-Type"], url
    fetch(base_url, "/favicon.svg")
    fetch(base_url, "/assets/missing.js", 404)
    fetch(base_url, "/.env", 404)

    body, _ = fetch(base_url, "/api/health")
    assert json.loads(body) == {"status": "ok"}
    body, _ = fetch(base_url, "/api/events?search=routing-check")
    assert json.loads(body) == []
    body, _ = fetch(base_url, "/api/missing", 404)
    assert json.loads(body) == {"detail": "Not Found"}
    body, _ = fetch(base_url, "/openapi.json")
    assert "/api/auth/login" in json.loads(body)["paths"]
    for route in ["/docs", "/docs/oauth2-redirect", "/redoc"]:
        _, headers = fetch(base_url, route)
        assert "text/html" in headers["Content-Type"], route

    _, headers = fetch(base_url, "/api/events/", 307)
    assert headers["Location"] == f"{base_url}/api/events"
    _, headers = fetch(
        base_url, "/api/events/?search=check", 307,
        {"Host": "campusly.example", "X-Forwarded-Proto": "https"},
    )
    assert headers["Location"] == "https://campusly.example/api/events?search=check"
    print("PASS: compiled frontend, login route, assets, API, docs, and redirects.", flush=True)

    credentials = {"email": f"routing-{uuid4().hex[:8]}@example.com", "password": uuid4().hex}
    fetch(
        base_url, "/api/auth/register", 201,
        payload={**credentials, "display_name": "Routing Check"},
    )
    body, _ = fetch(base_url, "/api/auth/login", payload=credentials)
    login = json.loads(body)
    assert login["access_token"] and login["user"]["email"] == credentials["email"]
    body, _ = fetch(
        base_url, "/api/users/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert json.loads(body)["email"] == credentials["email"]
    body, _ = fetch(
        base_url, "/api/auth/login", 401,
        payload={**credentials, "password": "incorrect-password"},
    )
    assert isinstance(json.loads(body)["detail"], str)
    print("PASS: registration, login, bearer auth, and login errors via Nginx.", flush=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = f"campusly-routing-check-{uuid4().hex[:8]}"
    base_files = ["-f", str(root / "compose.yaml")]
    compose_files = list(base_files)
    environment = os.environ.copy()
    environment["WEB_PORT"] = "0"

    with tempfile.TemporaryDirectory(prefix="campusly-routing-") as directory:
        workspace = Path(directory)

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
            compose("build", "web", "frontend-checks", "backend", "tests")
            for failing_service in ["tests", "frontend-checks"]:
                override = workspace / f"fail-{failing_service}.json"
                override.write_text(json.dumps({"services": {
                    service: {"command": [
                        "sh", "-c", f"exit {1 if service == failing_service else 0}",
                    ]}
                    for service in ["tests", "frontend-checks"]
                }}))
                compose_files[:] = [*base_files, "-f", str(override)]
                result = compose(
                    "up", "--no-build", "--force-recreate", "--wait",
                    "--wait-timeout", "30", "web", check=False,
                )
                assert result.returncode != 0, f"{failing_service} must block startup"
                for service in ["backend", "web"]:
                    container = compose(
                        "ps", "--all", "--quiet", service, capture=True,
                    ).stdout.strip()
                    state = json.loads(subprocess.check_output(
                        ["docker", "inspect", "--format", "{{json .State}}", container],
                        text=True,
                    ))
                    assert state["Status"] == "created", service
                    assert state["StartedAt"] == "0001-01-01T00:00:00Z", service
                print(f"PASS: failure in {failing_service} blocks deployment.", flush=True)
                compose("down", "--volumes")

            compose_files[:] = base_files
            result = compose(
                "up", "--no-build", "--force-recreate", "--always-recreate-deps",
                "--wait", "--wait-timeout", "180", "web", check=False,
            )
            if result.returncode != 0:
                compose("logs", "--tail=40", "tests", "frontend-checks")
                raise RuntimeError("Deployment checks failed; inspect the job output above")
            address = compose("port", "web", "8080", capture=True).stdout.strip()
            verify_site(f"http://{address}")
        finally:
            compose("down", "--volumes")


if __name__ == "__main__":
    main()

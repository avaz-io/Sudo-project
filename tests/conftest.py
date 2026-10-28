"""Shared fixtures for the backend API tests.

Run from the repository root:
    pip install -r backend/requirements.txt pytest httpx
    pytest tests -v
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

# The app reads its settings when it is imported, so set them first.
# 32+ bytes: shorter HS256 keys trigger PyJWT's InsecureKeyLengthWarning.
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["DATABASE_URL"] = "sqlite://"  # placeholder, replaced by the test engine below

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Event, EventCategory, EventStatus, User, UserRole  # noqa: E402

PASSWORD = "password123"


@pytest.fixture
def db_engine(tmp_path):
    """A fresh SQLite file per test, so tests never affect each other."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session_factory(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client(db_session_factory):
    def _get_test_db():
        with db_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def future(days: int = 7) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)


@pytest.fixture
def make_user(client):
    """Registers a standard user through the API and returns their auth headers."""

    def _make_user(email: str, name: str = "Student") -> dict[str, str]:
        response = client.post(
            "/api/auth/register",
            json={"display_name": name, "email": email, "password": PASSWORD},
        )
        assert response.status_code == 201, response.text
        return auth_header(response.json()["access_token"])

    return _make_user


@pytest.fixture
def make_organizer(client, db_session_factory):
    """Creates an organizer directly in the DB (FR-07: organizer access comes from a
    setup procedure, not from the API) and returns their auth headers."""

    def _make_organizer(email: str, name: str = "Organizer") -> dict[str, str]:
        with db_session_factory() as db:
            db.add(
                User(
                    email=email,
                    display_name=name,
                    password_hash=hash_password(PASSWORD),
                    role=UserRole.ORGANIZER,
                )
            )
            db.commit()
        response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return auth_header(response.json()["access_token"])

    return _make_organizer


@pytest.fixture
def create_event(client):
    """Creates an event through the API. Published by default."""

    def _create_event(
        organizer_headers: dict[str, str],
        capacity: int | None = None,
        publish: bool = True,
        title: str = "Python Workshop",
    ) -> dict:
        body = {
            "title": title,
            "description": "Intro to FastAPI",
            "category": "academic",
            "starts_at": future().isoformat(),
            "location": "UCA220",
            "capacity": capacity,
        }
        response = client.post("/api/events", json=body, headers=organizer_headers)
        assert response.status_code == 201, response.text
        created = response.json()
        if publish:
            response = client.post(f"/api/events/{created['id']}/publish", headers=organizer_headers)
            assert response.status_code == 200, response.text
            created = response.json()
        return created

    return _create_event


@pytest.fixture
def insert_event(db_session_factory):
    """Inserts an event straight into the DB. Used for states the API won't let us
    create, such as a published event whose start time has already passed."""

    def _insert_event(organizer_email: str, starts_at: datetime, status: EventStatus) -> int:
        with db_session_factory() as db:
            organizer = db.scalars(select(User).where(User.email == organizer_email)).one()
            new_event = Event(
                organizer_id=organizer.id,
                title="Past Event",
                description="Already started",
                category=EventCategory.OTHER,
                starts_at=starts_at,
                location="UCA220",
                capacity=None,
                status=status,
            )
            db.add(new_event)
            db.commit()
            return new_event.id

    return _insert_event

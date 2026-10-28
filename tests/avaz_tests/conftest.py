"""Shared fixtures: an isolated SQLite database per test, a TestClient wired to it,
and ready-made users (student + organizers) with valid JWTs."""

import os

# Must be set before anything imports app.core.config, which reads settings at import time.
# Environment variables take precedence over backend/.env, so tests never touch the dev DB.
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.db.types import utcnow
from app.main import app
from app.models import Event, EventCategory, EventStatus, User, UserRole

TEST_PASSWORD = "correct-horse-battery"


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    """A fresh SQLite file per test, so tests can't leak state into each other."""
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Session for arranging data and checking results directly in the test database."""
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """TestClient whose requests use the test database instead of the app's engine.

    Not entered as a context manager, so the app lifespan (create_all on the real engine)
    never runs.
    """

    def _override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@dataclass
class AuthUser:
    user: User
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture
def make_user(db_session: Session) -> Callable[..., AuthUser]:
    """Factory: inserts a user directly and returns it with a valid access token."""

    def _make_user(
        email: str, display_name: str = "Test User", role: UserRole = UserRole.USER
    ) -> AuthUser:
        user = User(
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            display_name=display_name,
            role=role,
        )
        db_session.add(user)
        db_session.commit()
        return AuthUser(user=user, token=create_access_token(user.id, user.token_version))

    return _make_user


@pytest.fixture
def student(make_user: Callable[..., AuthUser]) -> AuthUser:
    return make_user("student@university.edu", "Sam Student")


@pytest.fixture
def organizer(make_user: Callable[..., AuthUser]) -> AuthUser:
    return make_user("organizer@university.edu", "Olivia Organizer", UserRole.ORGANIZER)


@pytest.fixture
def other_organizer(make_user: Callable[..., AuthUser]) -> AuthUser:
    return make_user("other.organizer@university.edu", "Oscar Organizer", UserRole.ORGANIZER)



@pytest.fixture
def make_event(db_session: Session) -> Callable[..., Event]:
    """Factory: inserts an event directly, bypassing the API's status rules."""

    def _make_event(
        organizer: AuthUser,
        title: str = "Sample Event",
        status: EventStatus = EventStatus.PUBLISHED,
        starts_at: datetime | None = None,
        capacity: int | None = None,
        category: EventCategory = EventCategory.ACADEMIC,
    ) -> Event:
        event = Event(
            organizer_id=organizer.user.id,
            title=title,
            description=f"Description of {title}",
            category=category,
            starts_at=starts_at or utcnow() + timedelta(days=7),
            location="Main Hall",
            capacity=capacity,
            status=status,
        )
        db_session.add(event)
        db_session.commit()
        return event

    return _make_event

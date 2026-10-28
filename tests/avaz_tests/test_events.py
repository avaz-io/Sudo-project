"""FR-05 discovery, FR-06 details, FR-07 creation, FR-08 management, FR-12 status."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.types import utcnow
from app.models import Event, EventStatus


def _event_body(**overrides) -> dict:
    body = {
        "title": "Intro to Machine Learning",
        "description": "A beginner-friendly workshop.",
        "category": "academic",
        "starts_at": (utcnow() + timedelta(days=10)).isoformat(),
        "location": "Room 101",
        "capacity": 30,
    }
    return {**body, **overrides}


def _titles(response) -> list[str]:
    return [event["title"] for event in response.json()]


# --- FR-05 ----------------------------------------------------------------------------------


def test_get_published_events_public(client: TestClient, organizer, make_event) -> None:
    make_event(organizer, "Robotics Workshop", starts_at=utcnow() + timedelta(days=5))
    make_event(organizer, "Chess Club Night", starts_at=utcnow() + timedelta(days=2))
    make_event(organizer, "Secret Draft Workshop", status=EventStatus.DRAFT)
    make_event(organizer, "Cancelled Workshop", status=EventStatus.CANCELLED)
    make_event(organizer, "Past Workshop", starts_at=utcnow() - timedelta(days=1))

    # Anonymous: only published, upcoming events, soonest first.
    response = client.get("/api/events")
    assert response.status_code == 200
    assert _titles(response) == ["Chess Club Night", "Robotics Workshop"]

    first = response.json()[0]
    assert first["organizer"] == {"id": organizer.user.id, "display_name": "Olivia Organizer"}
    assert "email" not in first["organizer"]

    # Title search is case-insensitive and still excludes drafts/cancelled/past events.
    search = client.get("/api/events", params={"q": "workshop"})
    assert search.status_code == 200
    assert _titles(search) == ["Robotics Workshop"]

    assert client.get("/api/events", params={"q": "no such event"}).json() == []


def test_search_treats_wildcards_literally(client: TestClient, organizer, make_event) -> None:
    make_event(organizer, "100% Fun Run")
    make_event(organizer, "Movie Night")

    assert _titles(client.get("/api/events", params={"q": "%"})) == ["100% Fun Run"]


def test_filter_by_category(client: TestClient, organizer, make_event) -> None:
    make_event(organizer, "Football Match", category="sports")
    make_event(organizer, "Physics Lecture", category="academic")

    response = client.get("/api/events", params={"category": "sports"})
    assert _titles(response) == ["Football Match"]


# --- FR-06 ----------------------------------------------------------------------------------


def test_draft_events_hidden_from_public(
    client: TestClient, organizer, other_organizer, student, make_event
) -> None:
    draft = make_event(organizer, "Unannounced Gala", status=EventStatus.DRAFT)
    url = f"/api/events/{draft.id}"

    # Anonymous, other users, and other organizers all get 404 (not 403).
    assert client.get(url).status_code == 404
    assert client.get(url, headers=student.headers).status_code == 404
    assert client.get(url, headers=other_organizer.headers).status_code == 404
    assert client.get("/api/events/999999").status_code == 404

    # The owner sees it, both directly and on My Events.
    own = client.get(url, headers=organizer.headers)
    assert own.status_code == 200
    assert own.json()["status"] == "draft"

    mine = client.get("/api/users/me/events", headers=organizer.headers)
    assert _titles(mine) == ["Unannounced Gala"]
    assert client.get("/api/users/me/events", headers=other_organizer.headers).json() == []


def test_published_event_details_public(client: TestClient, organizer, make_event) -> None:
    event = make_event(organizer, "Open Day", capacity=50)

    response = client.get(f"/api/events/{event.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Open Day"
    assert data["active_registrations"] == 0
    assert data["available_places"] == 50
    assert data["my_registration_status"] is None


# --- FR-07 ----------------------------------------------------------------------------------


def test_create_event_by_organizer(client: TestClient, organizer, db_session: Session) -> None:
    response = client.post("/api/events", json=_event_body(), headers=organizer.headers)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"  # always starts as a draft
    assert data["organizer"]["id"] == organizer.user.id
    assert data["capacity"] == 30
    assert data["available_places"] == 30

    event = db_session.get(Event, data["id"])
    assert event is not None
    assert event.organizer_id == organizer.user.id
    assert event.status == EventStatus.DRAFT

    # Not visible publicly until published.
    assert client.get("/api/events").json() == []


def test_create_event_without_capacity_is_unlimited(client: TestClient, organizer) -> None:
    body = _event_body()
    del body["capacity"]
    response = client.post("/api/events", json=body, headers=organizer.headers)

    assert response.status_code == 201
    assert response.json()["capacity"] is None
    assert response.json()["available_places"] is None


def test_create_event_non_organizer_forbidden(
    client: TestClient, student, db_session: Session
) -> None:
    assert client.post("/api/events", json=_event_body()).status_code == 401
    response = client.post("/api/events", json=_event_body(), headers=student.headers)
    assert response.status_code == 403

    assert db_session.scalar(select(func.count()).select_from(Event)) == 0


def test_create_event_validation(client: TestClient, organizer) -> None:
    invalid_bodies = [
        _event_body(title=""),
        _event_body(capacity=0),
        _event_body(category="not-a-category"),
        _event_body(starts_at="2030-01-01T10:00:00"),  # no timezone offset
        _event_body(status="published"),  # status can't be set on create
        _event_body(organizer_id=12345),
    ]
    for body in invalid_bodies:
        response = client.post("/api/events", json=body, headers=organizer.headers)
        assert response.status_code == 422, body


# --- FR-08 ----------------------------------------------------------------------------------


def test_prevent_editing_other_organizer_event(
    client: TestClient, organizer, other_organizer, student, make_event, db_session: Session
) -> None:
    published = make_event(organizer, "Owned Event")
    draft = make_event(organizer, "Owned Draft", status=EventStatus.DRAFT)
    change = {"title": "Hijacked"}

    # Another organizer: 403 on a published event, 404 on a hidden draft.
    response = client.patch(
        f"/api/events/{published.id}", json=change, headers=other_organizer.headers
    )
    assert response.status_code == 403
    response = client.patch(f"/api/events/{draft.id}", json=change, headers=other_organizer.headers)
    assert response.status_code == 404

    # Status changes are protected the same way.
    for action in ("publish", "cancel", "complete"):
        response = client.post(
            f"/api/events/{published.id}/{action}", headers=other_organizer.headers
        )
        assert response.status_code == 403, action

    # A student isn't an organizer at all.
    response = client.patch(f"/api/events/{published.id}", json=change, headers=student.headers)
    assert response.status_code == 403

    db_session.refresh(published)
    db_session.refresh(draft)
    assert published.title == "Owned Event"
    assert published.status == EventStatus.PUBLISHED
    assert draft.title == "Owned Draft"

    # The owner can edit.
    response = client.patch(
        f"/api/events/{published.id}",
        json={"title": "Renamed Event", "capacity": None},
        headers=organizer.headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed Event"
    assert response.json()["capacity"] is None


def test_cannot_edit_finished_events(client: TestClient, organizer, make_event) -> None:
    cancelled = make_event(organizer, "Cancelled", status=EventStatus.CANCELLED)
    started = make_event(organizer, "Started", starts_at=utcnow() - timedelta(hours=1))

    for event in (cancelled, started):
        response = client.patch(
            f"/api/events/{event.id}", json={"title": "New"}, headers=organizer.headers
        )
        assert response.status_code == 400, event.title


# --- FR-12 ----------------------------------------------------------------------------------


def test_event_status_transitions(client: TestClient, organizer, db_session: Session) -> None:
    def create() -> int:
        response = client.post("/api/events", json=_event_body(), headers=organizer.headers)
        assert response.status_code == 201
        return response.json()["id"]

    def act(event_id: int, action: str):
        return client.post(f"/api/events/{event_id}/{action}", headers=organizer.headers)

    def backdate(event_id: int) -> None:
        """Simulate time passing: move the start time into the past."""
        event = db_session.get(Event, event_id)
        event.starts_at = utcnow() - timedelta(hours=2)
        db_session.commit()

    # draft -> published -> completed (only after the start time)
    event_id = create()
    assert act(event_id, "complete").status_code == 400  # a draft can't be completed
    published = act(event_id, "publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert event_id in [e["id"] for e in client.get("/api/events").json()]

    assert act(event_id, "publish").status_code == 400  # already published
    assert act(event_id, "complete").status_code == 400  # hasn't started yet

    backdate(event_id)
    assert act(event_id, "cancel").status_code == 400  # can't cancel once started
    completed = act(event_id, "complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    # completed is final
    for action in ("publish", "cancel", "complete"):
        assert act(event_id, action).status_code == 400, action

    # draft -> cancelled
    event_id = create()
    cancelled = act(event_id, "cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert act(event_id, "publish").status_code == 400  # cancelled is final

    # published -> cancelled (before start); still viewable, but not in discovery
    event_id = create()
    assert act(event_id, "publish").status_code == 200
    cancelled = act(event_id, "cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get(f"/api/events/{event_id}").json()["status"] == "cancelled"
    assert event_id not in [e["id"] for e in client.get("/api/events").json()]

    # a draft with a past start time can't be published
    event_id = create()
    backdate(event_id)
    response = act(event_id, "publish")
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)

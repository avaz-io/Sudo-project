"""FR-09 / FR-10 / NFR-04: registering for events and cancelling registrations."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from app.models import EventStatus

# Status codes follow CLAUDE.md: 400 rule violation, 404 hidden draft, 409 duplicate.


def register(client, event_id, headers):
    return client.post(f"/api/events/{event_id}/registration", headers=headers)


def cancel(client, event_id, headers):
    return client.delete(f"/api/events/{event_id}/registration", headers=headers)


# ---------- FR-09: registration ----------


def test_user_can_register_for_published_event(client, make_user, make_organizer, create_event):
    organizer = make_organizer("org@newuu.uz")
    student = make_user("student@newuu.uz")
    event = create_event(organizer, capacity=10)

    response = register(client, event["id"], student)

    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert response.json()["event_id"] == event["id"]


def test_anonymous_user_cannot_register(client, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"))

    response = client.post(f"/api/events/{event['id']}/registration")

    assert response.status_code == 401


def test_duplicate_registration_is_rejected(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"), capacity=10)
    student = make_user("student@newuu.uz")
    assert register(client, event["id"], student).status_code == 201

    response = register(client, event["id"], student)

    assert response.status_code == 409
    detail = client.get(f"/api/events/{event['id']}").json()
    assert detail["active_registrations"] == 1


def test_registration_beyond_capacity_is_rejected(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"), capacity=2)
    assert register(client, event["id"], make_user("a@newuu.uz")).status_code == 201
    assert register(client, event["id"], make_user("b@newuu.uz")).status_code == 201

    response = register(client, event["id"], make_user("c@newuu.uz"))

    assert response.status_code == 400
    detail = client.get(f"/api/events/{event['id']}").json()
    assert detail["active_registrations"] == 2
    assert detail["available_places"] == 0


def test_event_without_capacity_allows_many_registrations(
    client, make_user, make_organizer, create_event
):
    event = create_event(make_organizer("org@newuu.uz"), capacity=None)

    for i in range(5):
        assert register(client, event["id"], make_user(f"s{i}@newuu.uz")).status_code == 201

    detail = client.get(f"/api/events/{event['id']}").json()
    assert detail["active_registrations"] == 5
    assert detail["available_places"] is None


def test_cannot_register_for_draft_event(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"), publish=False)

    response = register(client, event["id"], make_user("student@newuu.uz"))

    assert response.status_code == 404


def test_cannot_register_for_cancelled_event(client, make_user, make_organizer, create_event):
    organizer = make_organizer("org@newuu.uz")
    event = create_event(organizer)
    assert client.post(f"/api/events/{event['id']}/cancel", headers=organizer).status_code == 200

    response = register(client, event["id"], make_user("student@newuu.uz"))

    assert response.status_code == 400


def test_cannot_register_for_started_event(client, make_user, make_organizer, insert_event):
    make_organizer("org@newuu.uz")
    started = datetime.now(UTC) - timedelta(hours=1)
    event_id = insert_event("org@newuu.uz", started, EventStatus.PUBLISHED)

    response = register(client, event_id, make_user("student@newuu.uz"))

    assert response.status_code == 400


def test_cannot_register_for_completed_event(client, make_user, make_organizer, insert_event):
    make_organizer("org@newuu.uz")
    started = datetime.now(UTC) - timedelta(days=1)
    event_id = insert_event("org@newuu.uz", started, EventStatus.COMPLETED)

    response = register(client, event_id, make_user("student@newuu.uz"))

    assert response.status_code == 400


def test_register_for_missing_event_returns_404(client, make_user):
    response = register(client, 9999, make_user("student@newuu.uz"))

    assert response.status_code == 404


# ---------- FR-10: cancelling and re-registering ----------


def test_cancelling_releases_the_place(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"), capacity=1)
    first = make_user("a@newuu.uz")
    second = make_user("b@newuu.uz")
    assert register(client, event["id"], first).status_code == 201
    assert register(client, event["id"], second).status_code == 400  # full

    response = cancel(client, event["id"], first)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert register(client, event["id"], second).status_code == 201  # place is free again


def test_user_can_register_again_after_cancelling(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"), capacity=5)
    student = make_user("student@newuu.uz")
    first = register(client, event["id"], student).json()
    cancel(client, event["id"], student)

    response = register(client, event["id"], student)

    assert response.status_code == 201
    assert response.json()["status"] == "active"
    # One row per (user, event): the old registration is reactivated, not duplicated.
    assert response.json()["id"] == first["id"]


def test_cannot_cancel_without_active_registration(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("org@newuu.uz"))

    response = cancel(client, event["id"], make_user("student@newuu.uz"))

    assert response.status_code in (400, 404)


def test_cannot_cancel_after_event_started(
    client, make_user, make_organizer, create_event, db_session_factory
):
    event = create_event(make_organizer("org@newuu.uz"))
    student = make_user("student@newuu.uz")
    assert register(client, event["id"], student).status_code == 201

    # Move the event into the past to simulate that it has started.
    from app.models import Event

    with db_session_factory() as db:
        db.get(Event, event["id"]).starts_at = datetime.now(UTC) - timedelta(minutes=5)
        db.commit()

    response = cancel(client, event["id"], student)

    assert response.status_code == 400


def test_my_registrations_lists_registered_events(client, make_user, make_organizer, create_event):
    organizer = make_organizer("org@newuu.uz")
    student = make_user("student@newuu.uz")
    first = create_event(organizer, title="Workshop A")
    second = create_event(organizer, title="Workshop B")
    register(client, first["id"], student)
    register(client, second["id"], student)

    response = client.get("/api/users/me/registrations", headers=student)

    assert response.status_code == 200
    titles = {row["event"]["title"] for row in response.json()}
    assert titles == {"Workshop A", "Workshop B"}


def test_my_registrations_shows_event_cancelled_by_organizer(
    client, make_user, make_organizer, create_event
):
    organizer = make_organizer("org@newuu.uz")
    student = make_user("student@newuu.uz")
    event = create_event(organizer)
    register(client, event["id"], student)
    client.post(f"/api/events/{event['id']}/cancel", headers=organizer)

    rows = client.get("/api/users/me/registrations", headers=student).json()

    assert len(rows) == 1
    assert rows[0]["event"]["status"] == "cancelled"


# ---------- NFR-04: concurrent requests ----------


def test_concurrent_registrations_do_not_exceed_capacity(
    client, make_user, make_organizer, create_event
):
    event = create_event(make_organizer("org@newuu.uz"), capacity=1)
    students = [make_user(f"s{i}@newuu.uz") for i in range(8)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(lambda h: register(client, event["id"], h).status_code, students))

    assert codes.count(201) == 1
    detail = client.get(f"/api/events/{event['id']}").json()
    assert detail["active_registrations"] == 1

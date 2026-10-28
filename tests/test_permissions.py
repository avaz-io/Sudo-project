"""FR-04 / FR-07 / FR-08 / FR-11: role and ownership checks."""

from datetime import UTC, datetime, timedelta

# Status codes follow CLAUDE.md: 403 wrong role or not owner, 404 hidden draft.


def event_body(**overrides):
    body = {
        "title": "Hackathon",
        "description": "24h coding",
        "category": "extracurricular",
        "starts_at": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        "location": "Main Hall",
        "capacity": 50,
    }
    body.update(overrides)
    return body


# ---------- FR-07: only organizers create events ----------


def test_standard_user_cannot_create_event(client, make_user):
    response = client.post("/api/events", json=event_body(), headers=make_user("s@newuu.uz"))

    assert response.status_code == 403


def test_anonymous_user_cannot_create_event(client):
    response = client.post("/api/events", json=event_body())

    assert response.status_code == 401


def test_organizer_creates_event_as_draft(client, make_organizer):
    response = client.post("/api/events", json=event_body(), headers=make_organizer("o@newuu.uz"))

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_capacity_must_be_positive(client, make_organizer):
    organizer = make_organizer("o@newuu.uz")

    for bad_capacity in (0, -5):
        response = client.post(
            "/api/events", json=event_body(capacity=bad_capacity), headers=organizer
        )
        assert response.status_code == 422


# ---------- FR-08: organizers only manage their own events ----------


def test_standard_user_cannot_edit_event(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("o@newuu.uz"))

    response = client.patch(
        f"/api/events/{event['id']}", json={"title": "Hacked"}, headers=make_user("s@newuu.uz")
    )

    assert response.status_code == 403


def test_organizer_cannot_edit_another_organizers_event(client, make_organizer, create_event):
    event = create_event(make_organizer("owner@newuu.uz"))
    other = make_organizer("other@newuu.uz")

    response = client.patch(f"/api/events/{event['id']}", json={"title": "Hacked"}, headers=other)

    assert response.status_code == 403
    assert client.get(f"/api/events/{event['id']}").json()["title"] == event["title"]


def test_organizer_cannot_publish_or_cancel_another_organizers_event(
    client, make_organizer, create_event
):
    draft = create_event(make_organizer("owner@newuu.uz"), publish=False)
    other = make_organizer("other@newuu.uz")

    # The draft is hidden from other organizers, so they get 404, not 403 (CLAUDE.md).
    assert client.post(f"/api/events/{draft['id']}/publish", headers=other).status_code == 404
    assert client.post(f"/api/events/{draft['id']}/cancel", headers=other).status_code == 404


def test_owner_can_edit_own_event(client, make_organizer, create_event):
    owner = make_organizer("owner@newuu.uz")
    event = create_event(owner)

    response = client.patch(f"/api/events/{event['id']}", json={"title": "Renamed"}, headers=owner)

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_capacity_cannot_go_below_active_registrations(
    client, make_user, make_organizer, create_event
):
    owner = make_organizer("owner@newuu.uz")
    event = create_event(owner, capacity=5)
    for i in range(3):
        client.post(f"/api/events/{event['id']}/registration", headers=make_user(f"s{i}@newuu.uz"))

    too_low = client.patch(f"/api/events/{event['id']}", json={"capacity": 2}, headers=owner)
    exact = client.patch(f"/api/events/{event['id']}", json={"capacity": 3}, headers=owner)

    assert too_low.status_code == 400
    assert exact.status_code == 200


def test_draft_is_hidden_from_other_users(client, make_user, make_organizer, create_event):
    owner = make_organizer("owner@newuu.uz")
    draft = create_event(owner, publish=False)

    assert client.get(f"/api/events/{draft['id']}").status_code == 404
    assert client.get(f"/api/events/{draft['id']}", headers=make_user("s@newuu.uz")).status_code == 404
    assert client.get(f"/api/events/{draft['id']}", headers=owner).status_code == 200


# ---------- FR-11: participant lists are private to the owner ----------


def test_owner_sees_participant_list(client, make_user, make_organizer, create_event):
    owner = make_organizer("owner@newuu.uz")
    event = create_event(owner)
    client.post(
        f"/api/events/{event['id']}/registration", headers=make_user("s@newuu.uz", name="Ali")
    )

    response = client.get(f"/api/events/{event['id']}/participants", headers=owner)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["participants"][0]["display_name"] == "Ali"
    assert "registered_at" in body["participants"][0]


def test_participant_list_hidden_from_standard_user(client, make_user, make_organizer, create_event):
    event = create_event(make_organizer("owner@newuu.uz"))

    response = client.get(
        f"/api/events/{event['id']}/participants", headers=make_user("s@newuu.uz")
    )

    assert response.status_code == 403


def test_participant_list_hidden_from_other_organizer(client, make_organizer, create_event):
    event = create_event(make_organizer("owner@newuu.uz"))

    response = client.get(
        f"/api/events/{event['id']}/participants", headers=make_organizer("other@newuu.uz")
    )

    assert response.status_code == 403


# ---------- FR-04: users cannot change their own role ----------


def test_user_cannot_promote_themselves_to_organizer(client, make_user):
    student = make_user("s@newuu.uz")

    response = client.patch("/api/users/me", json={"role": "organizer"}, headers=student)

    assert response.status_code == 422
    assert client.get("/api/users/me", headers=student).json()["role"] == "user"

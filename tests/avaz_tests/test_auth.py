"""FR-01 registration, FR-02 login, FR-04 profile."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models import User, UserRole

PASSWORD = "correct-horse-battery"  # matches conftest.TEST_PASSWORD


def _register(client: TestClient, email: str = "new.student@university.edu", **overrides):
    body = {"display_name": "New Student", "email": email, "password": PASSWORD, **overrides}
    return client.post("/api/auth/register", json=body)


# --- FR-01 ----------------------------------------------------------------------------------


def test_register_user_success(client: TestClient, db_session: Session) -> None:
    response = _register(client, email="New.Student@University.edu")

    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["display_name"] == "New Student"
    assert data["user"]["email"] == "new.student@university.edu"  # normalized to lowercase
    assert data["user"]["role"] == "user"
    assert "password" not in data["user"] and "password_hash" not in data["user"]

    # The returned token identifies the new account and works on a protected endpoint.
    me = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["id"] == data["user"]["id"]

    # Stored hashed, never in plain text.
    user = db_session.scalar(select(User).where(User.email == "new.student@university.edu"))
    assert user is not None
    assert user.password_hash != PASSWORD


def test_register_duplicate_email_fails(client: TestClient, db_session: Session) -> None:
    assert _register(client).status_code == 201

    # Same address with different casing is still a duplicate.
    response = _register(client, email="NEW.STUDENT@university.edu", display_name="Someone Else")

    assert response.status_code == 409
    assert isinstance(response.json()["detail"], str)
    count = db_session.scalars(select(User).where(User.email == "new.student@university.edu")).all()
    assert len(count) == 1


def test_register_rejects_role_field(client: TestClient) -> None:
    """Signing up can't grant the organizer role."""
    response = _register(client, role="organizer")
    assert response.status_code == 422


# --- FR-02 ----------------------------------------------------------------------------------


def test_login_success(client: TestClient, student) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "student@university.edu", "password": PASSWORD}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["id"] == student.user.id

    payload = decode_access_token(data["access_token"])
    assert payload["sub"] == str(student.user.id)
    assert payload["ver"] == student.user.token_version
    assert payload["exp"] > payload["iat"]


def test_login_invalid_password_fails(client: TestClient, student) -> None:
    wrong_password = client.post(
        "/api/auth/login", json={"email": "student@university.edu", "password": "wrong-password"}
    )
    unknown_email = client.post(
        "/api/auth/login", json={"email": "nobody@university.edu", "password": PASSWORD}
    )

    for response in (wrong_password, unknown_email):
        assert response.status_code == 401
        assert "access_token" not in response.json()
    # Same message either way, so the API doesn't reveal which emails are registered.
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_protected_endpoint_rejects_bad_token(client: TestClient) -> None:
    assert client.get("/api/users/me").status_code == 401
    bad = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert bad.status_code == 401


# --- FR-04 ----------------------------------------------------------------------------------


def test_update_display_name(client: TestClient, student, db_session: Session) -> None:
    response = client.patch(
        "/api/users/me", json={"display_name": "  Samantha  "}, headers=student.headers
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Samantha"  # surrounding whitespace stripped
    assert client.get("/api/users/me", headers=student.headers).json()["display_name"] == (
        "Samantha"
    )

    db_session.refresh(student.user)
    assert student.user.display_name == "Samantha"


def test_update_display_name_rejects_empty(client: TestClient, student) -> None:
    response = client.patch("/api/users/me", json={"display_name": "   "}, headers=student.headers)
    assert response.status_code == 422


def test_user_cannot_escalate_own_role(client: TestClient, student, db_session: Session) -> None:
    attempts = [
        {"role": "organizer"},
        {"display_name": "Sneaky", "role": "organizer"},
        {"display_name": "Sneaky", "email": "admin@university.edu"},
    ]
    for body in attempts:
        response = client.patch("/api/users/me", json=body, headers=student.headers)
        assert response.status_code == 422, body

    me = client.get("/api/users/me", headers=student.headers).json()
    assert me["role"] == "user"
    assert me["email"] == "student@university.edu"
    assert me["display_name"] == "Sam Student"

    db_session.refresh(student.user)
    assert student.user.role == UserRole.USER

    # And the student still can't use organizer-only endpoints.
    response = client.get("/api/users/me/events", headers=student.headers)
    assert response.status_code == 403

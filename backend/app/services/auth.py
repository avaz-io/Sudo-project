from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead

# Verified against when the email is unknown, so a failed login takes about as long
# whether or not the account exists.
_DUMMY_HASH = hash_password("not-a-real-password")


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.token_version),
        user=UserRead.model_validate(user),
    )


def register(db: Session, body: RegisterRequest) -> TokenResponse:
    """FR-01: new accounts always get the standard user role."""
    if db.scalar(select(User.id).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    return _token_response(user)


def login(db: Session, body: LoginRequest) -> TokenResponse:
    """FR-02: the same generic error for an unknown email and a wrong password."""
    user = db.scalar(select(User).where(User.email == body.email))
    password_ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _token_response(user)


def logout(db: Session, user: User) -> None:
    """FR-03: invalidates every token issued to this user so far."""
    user.token_version += 1
    db.commit()

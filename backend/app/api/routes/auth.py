from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession):
    """FR-01: create a standard user. 409 on duplicate email."""
    return auth_service.register(db, body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession):
    """FR-02: 401 with a generic message on wrong email or password."""
    return auth_service.login(db, body)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, db: DbSession) -> None:
    """FR-03: bump user.token_version so existing tokens stop working."""
    auth_service.logout(db, user)

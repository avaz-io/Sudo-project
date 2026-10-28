from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.api.stubs import not_implemented
from app.schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession):
    """FR-01: create a standard user. 409 on duplicate email."""
    raise not_implemented()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession):
    """FR-02: 401 with a generic message on wrong email or password."""
    raise not_implemented()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, db: DbSession):
    """FR-03: bump user.token_version so existing tokens stop working."""
    raise not_implemented()

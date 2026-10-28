from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, Organizer
from app.api.stubs import not_implemented
from app.schemas import EventRead, MyRegistrationRead, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(user: CurrentUser):
    """FR-04: current user's profile."""
    raise not_implemented()


@router.patch("/me", response_model=UserRead)
def update_me(body: UserUpdate, user: CurrentUser, db: DbSession):
    """FR-04: only display_name is editable."""
    raise not_implemented()


@router.get("/me/registrations", response_model=list[MyRegistrationRead])
def my_registrations(user: CurrentUser, db: DbSession):
    """FR-10: My Registrations page, including events cancelled by the organizer."""
    raise not_implemented()


@router.get("/me/events", response_model=list[EventRead])
def my_events(organizer: Organizer, db: DbSession):
    """FR-08: My Events page, all statuses for the current organizer."""
    raise not_implemented()

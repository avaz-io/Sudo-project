from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.api.stubs import not_implemented
from app.schemas import RegistrationRead

router = APIRouter(prefix="/events/{event_id}/registration", tags=["registrations"])


@router.post("", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, user: CurrentUser, db: DbSession):
    """FR-09: create or reactivate the caller's registration, enforcing capacity atomically."""
    raise not_implemented()


@router.delete("", response_model=RegistrationRead)
def cancel_registration(event_id: int, user: CurrentUser, db: DbSession):
    """FR-10: cancel the caller's active registration before the event starts."""
    raise not_implemented()

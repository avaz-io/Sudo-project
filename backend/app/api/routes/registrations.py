from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas import RegistrationRead
from app.services import registrations as registration_service

router = APIRouter(prefix="/events/{event_id}/registration", tags=["registrations"])


@router.post("", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, user: CurrentUser, db: DbSession):
    """FR-09: create or reactivate the caller's registration, enforcing capacity atomically."""
    return registration_service.register(db, event_id, user)


@router.delete("", response_model=RegistrationRead)
def cancel_registration(event_id: int, user: CurrentUser, db: DbSession):
    """FR-10: cancel the caller's active registration before the event starts."""
    return registration_service.cancel(db, event_id, user)

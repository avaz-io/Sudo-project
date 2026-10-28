from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, OptionalUser, Organizer
from app.api.stubs import not_implemented
from app.models import EventCategory
from app.schemas import EventCreate, EventDetail, EventRead, EventUpdate, ParticipantList
from app.services import events as event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(
    db: DbSession,
    q: str | None = Query(default=None, max_length=200, description="Title search"),
    category: EventCategory | None = None,
):
    """FR-05: published, upcoming events only, soonest first."""
    return event_service.list_public_events(db, q, category)


@router.post("", response_model=EventDetail, status_code=status.HTTP_201_CREATED)
def create_event(body: EventCreate, organizer: Organizer, db: DbSession):
    """FR-07: always created as a draft owned by the caller."""
    event = event_service.create_event(db, body, organizer)
    return event_service.to_detail(db, event, organizer)


@router.get("/{event_id}", response_model=EventDetail)
def get_event(event_id: int, db: DbSession, user: OptionalUser):
    """FR-06: drafts are 404 for everyone except their organizer."""
    event = event_service.get_visible_event(db, event_id, user)
    return event_service.to_detail(db, event, user)


@router.patch("/{event_id}", response_model=EventDetail)
def update_event(event_id: int, body: EventUpdate, organizer: Organizer, db: DbSession):
    """FR-08: owner only; draft or upcoming published; capacity >= active registrations."""
    event = event_service.update_event(db, event_id, body, organizer)
    return event_service.to_detail(db, event, organizer)


@router.post("/{event_id}/publish", response_model=EventDetail)
def publish_event(event_id: int, organizer: Organizer, db: DbSession):
    """FR-12: draft -> published; requires a future start time."""
    event = event_service.publish_event(db, event_id, organizer)
    return event_service.to_detail(db, event, organizer)


@router.post("/{event_id}/cancel", response_model=EventDetail)
def cancel_event(event_id: int, organizer: Organizer, db: DbSession):
    """FR-12: draft -> cancelled, or published -> cancelled before start."""
    event = event_service.cancel_event(db, event_id, organizer)
    return event_service.to_detail(db, event, organizer)


@router.post("/{event_id}/complete", response_model=EventDetail)
def complete_event(event_id: int, organizer: Organizer, db: DbSession):
    """FR-12: published -> completed after the start time has passed."""
    event = event_service.complete_event(db, event_id, organizer)
    return event_service.to_detail(db, event, organizer)


@router.get("/{event_id}/participants", response_model=ParticipantList)
def list_participants(event_id: int, organizer: Organizer, db: DbSession):
    """FR-11: owner only; active registrations with names and dates."""
    raise not_implemented()

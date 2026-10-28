from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.db.types import utcnow
from app.models import (
    Event,
    EventCategory,
    EventStatus,
    Registration,
    RegistrationStatus,
    User,
)
from app.schemas import EventCreate, EventDetail, EventRead, EventUpdate, UserSummary

_NOT_FOUND = "Event not found"


# --- Serialization --------------------------------------------------------------------------


def _active_counts(db: Session, event_ids: Sequence[int]) -> dict[int, int]:
    if not event_ids:
        return {}
    rows = db.execute(
        select(Registration.event_id, func.count())
        .where(
            Registration.event_id.in_(event_ids),
            Registration.status == RegistrationStatus.ACTIVE,
        )
        .group_by(Registration.event_id)
    )
    return {event_id: count for event_id, count in rows}


def active_count(db: Session, event_id: int) -> int:
    """Active registrations for one event, i.e. the places taken (FR-09)."""
    return _active_counts(db, [event_id]).get(event_id, 0)


def _read_fields(event: Event, active: int) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "starts_at": event.starts_at,
        "location": event.location,
        "capacity": event.capacity,
        "status": event.status,
        "organizer": UserSummary.model_validate(event.organizer),
        "active_registrations": active,
        "available_places": None if event.capacity is None else event.capacity - active,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def to_read_list(db: Session, events: Sequence[Event]) -> list[EventRead]:
    counts = _active_counts(db, [e.id for e in events])
    return [EventRead(**_read_fields(e, counts.get(e.id, 0))) for e in events]


def to_detail(db: Session, event: Event, user: User | None) -> EventDetail:
    active = _active_counts(db, [event.id]).get(event.id, 0)
    my_status = None
    if user is not None:
        my_status = db.scalar(
            select(Registration.status).where(
                Registration.event_id == event.id, Registration.user_id == user.id
            )
        )
    return EventDetail(**_read_fields(event, active), my_registration_status=my_status)


# --- Lookups and access checks --------------------------------------------------------------


def lock_event(db: Session, event_id: int) -> Event | None:
    """Loads the event and locks its row until the transaction ends (NFR-04).

    PostgreSQL honours FOR UPDATE. SQLite ignores it, so there we first issue a no-op UPDATE,
    which takes SQLite's database write lock and makes concurrent callers wait their turn.
    """
    if db.get_bind().dialect.name == "sqlite":
        db.execute(
            update(Event).where(Event.id == event_id).values(updated_at=Event.updated_at)
        )
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return db.scalar(stmt)


def get_visible_event(
    db: Session, event_id: int, user: User | None, *, lock: bool = False
) -> Event:
    """FR-06: drafts are 404 for everyone except their organizer."""
    event = lock_event(db, event_id) if lock else db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    if event.status == EventStatus.DRAFT and (user is None or user.id != event.organizer_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    return event


def get_owned_event(db: Session, event_id: int, organizer: User, *, lock: bool = False) -> Event:
    """Returns the event if `organizer` owns it: 404 if missing or a hidden draft, else 403."""
    event = lock_event(db, event_id) if lock else db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
    if event.organizer_id != organizer.id:
        if event.status == EventStatus.DRAFT:
            raise HTTPException(status.HTTP_404_NOT_FOUND, _NOT_FOUND)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only manage your own events")
    return event


# --- Use cases ------------------------------------------------------------------------------


def list_public_events(
    db: Session, q: str | None, category: EventCategory | None
) -> list[EventRead]:
    """FR-05: published events that haven't started yet, soonest first."""
    stmt = (
        select(Event)
        .options(selectinload(Event.organizer))
        .where(Event.status == EventStatus.PUBLISHED, Event.starts_at > utcnow())
        .order_by(Event.starts_at, Event.id)
    )
    if q:
        stmt = stmt.where(Event.title.icontains(q, autoescape=True))
    if category is not None:
        stmt = stmt.where(Event.category == category)
    return to_read_list(db, db.scalars(stmt).all())


def list_organizer_events(db: Session, organizer: User) -> list[EventRead]:
    """FR-08: every event of this organizer, in any status."""
    stmt = (
        select(Event)
        .options(selectinload(Event.organizer))
        .where(Event.organizer_id == organizer.id)
        .order_by(Event.starts_at, Event.id)
    )
    return to_read_list(db, db.scalars(stmt).all())


def create_event(db: Session, body: EventCreate, organizer: User) -> Event:
    """FR-07: new events always start as drafts owned by the caller."""
    event = Event(**body.model_dump(), organizer_id=organizer.id, status=EventStatus.DRAFT)
    db.add(event)
    db.commit()
    return event


def update_event(db: Session, event_id: int, body: EventUpdate, organizer: User) -> Event:
    """FR-08: owner only; drafts and upcoming published events are editable."""
    # Locked so a concurrent registration can't push the active count past a new capacity.
    event = get_owned_event(db, event_id, organizer, lock=True)
    now = utcnow()
    is_upcoming_published = event.status == EventStatus.PUBLISHED and event.starts_at > now
    if event.status != EventStatus.DRAFT and not is_upcoming_published:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only drafts and published events that haven't started can be edited",
        )

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field != "capacity":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{field} cannot be empty")

    if event.status == EventStatus.PUBLISHED and "starts_at" in changes:
        if changes["starts_at"] <= now:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "A published event must start in the future"
            )

    if changes.get("capacity") is not None:
        active = _active_counts(db, [event.id]).get(event.id, 0)
        if changes["capacity"] < active:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Capacity can't be lower than the {active} active registrations",
            )

    for field, value in changes.items():
        setattr(event, field, value)
    db.commit()
    return event


def publish_event(db: Session, event_id: int, organizer: User) -> Event:
    """FR-12: draft -> published, only with a future start time."""
    event = get_owned_event(db, event_id, organizer)
    if event.status != EventStatus.DRAFT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only draft events can be published")
    if event.starts_at <= utcnow():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Set a future start time before publishing"
        )
    event.status = EventStatus.PUBLISHED
    db.commit()
    return event


def cancel_event(db: Session, event_id: int, organizer: User) -> Event:
    """FR-12: draft -> cancelled, or published -> cancelled before the start time."""
    event = get_owned_event(db, event_id, organizer)
    if event.status == EventStatus.PUBLISHED:
        if event.starts_at <= utcnow():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "An event that has started can't be cancelled"
            )
    elif event.status != EventStatus.DRAFT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"A {event.status} event can't be cancelled"
        )
    event.status = EventStatus.CANCELLED
    db.commit()
    return event


def complete_event(db: Session, event_id: int, organizer: User) -> Event:
    """FR-12: published -> completed, only once the start time has passed."""
    event = get_owned_event(db, event_id, organizer)
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only published events can be marked completed"
        )
    if event.starts_at > utcnow():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "An event can't be completed before it starts"
        )
    event.status = EventStatus.COMPLETED
    db.commit()
    return event

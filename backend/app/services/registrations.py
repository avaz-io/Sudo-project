from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.types import utcnow
from app.models import Event, EventStatus, Registration, RegistrationStatus, User
from app.schemas import MyRegistrationRead, ParticipantList, ParticipantRead
from app.services import events as event_service


def _find_registration(db: Session, event_id: int, user: User) -> Registration | None:
    return db.scalar(
        select(Registration).where(
            Registration.event_id == event_id, Registration.user_id == user.id
        )
    )


def register(db: Session, event_id: int, user: User) -> Registration:
    """FR-09: register for a published, upcoming event that has room.

    The event row stays locked from the capacity check until commit, so concurrent requests
    can't overbook it (NFR-04). A previously cancelled registration is reactivated.
    """
    event = event_service.get_visible_event(db, event_id, user, lock=True)
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This event is not open for registration"
        )
    if event.starts_at <= utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This event has already started")

    registration = _find_registration(db, event.id, user)
    if registration is not None and registration.status == RegistrationStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already registered for this event")
    if event.capacity is not None and event_service.active_count(db, event.id) >= event.capacity:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This event is full")

    if registration is None:
        registration = Registration(user_id=user.id, event_id=event.id)
        db.add(registration)
    else:
        registration.status = RegistrationStatus.ACTIVE
        registration.registered_at = utcnow()
    try:
        db.commit()
    except IntegrityError:
        # The same user registered twice at once; the unique constraint caught the second.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already registered for this event")
    return registration


def cancel(db: Session, event_id: int, user: User) -> Registration:
    """FR-10: cancel the caller's active registration before the event starts."""
    event = event_service.get_visible_event(db, event_id, user)
    registration = _find_registration(db, event.id, user)
    if registration is None or registration.status != RegistrationStatus.ACTIVE:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "You don't have an active registration for this event"
        )
    if event.starts_at <= utcnow():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Registrations can't be cancelled after the event starts"
        )

    registration.status = RegistrationStatus.CANCELLED
    db.commit()
    return registration


def list_my_registrations(db: Session, user: User) -> list[MyRegistrationRead]:
    """FR-10: the caller's active registrations, including events the organizer cancelled."""
    registrations = db.scalars(
        select(Registration)
        .join(Registration.event)
        .where(
            Registration.user_id == user.id,
            Registration.status == RegistrationStatus.ACTIVE,
        )
        .order_by(Event.starts_at, Event.id)
    ).all()
    events = event_service.to_read_list(db, [r.event for r in registrations])
    return [
        MyRegistrationRead(
            id=r.id, status=r.status, registered_at=r.registered_at, event=event
        )
        for r, event in zip(registrations, events, strict=True)
    ]


def list_participants(db: Session, event_id: int, organizer: User) -> ParticipantList:
    """FR-11: owner only; active registrations, earliest first."""
    event = event_service.get_owned_event(db, event_id, organizer)
    rows = db.execute(
        select(User.id, User.display_name, Registration.registered_at)
        .join(Registration.user)
        .where(
            Registration.event_id == event.id,
            Registration.status == RegistrationStatus.ACTIVE,
        )
        .order_by(Registration.registered_at, Registration.id)
    ).all()
    participants = [
        ParticipantRead(user_id=user_id, display_name=name, registered_at=registered_at)
        for user_id, name, registered_at in rows
    ]
    return ParticipantList(event_id=event.id, count=len(participants), participants=participants)

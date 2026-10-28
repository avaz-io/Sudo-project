from datetime import datetime

from pydantic import AwareDatetime, Field, PositiveInt

from app.models import EventCategory, EventStatus, RegistrationStatus
from app.schemas.common import APIModel, InputModel
from app.schemas.user import UserSummary


class EventCreate(InputModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    category: EventCategory
    starts_at: AwareDatetime  # ISO 8601 with offset, e.g. 2026-11-05T18:00:00+05:00
    location: str = Field(min_length=1, max_length=200)
    capacity: PositiveInt | None = None


class EventUpdate(InputModel):
    """Partial update. Sending "capacity": null explicitly removes the limit;
    use model_fields_set to tell it apart from an omitted field."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    category: EventCategory | None = None
    starts_at: AwareDatetime | None = None
    location: str | None = Field(default=None, min_length=1, max_length=200)
    capacity: PositiveInt | None = None


class EventRead(APIModel):
    id: int
    title: str
    description: str
    category: EventCategory
    starts_at: datetime
    location: str
    capacity: int | None
    status: EventStatus
    organizer: UserSummary
    active_registrations: int
    available_places: int | None  # None when the event has no capacity limit
    created_at: datetime
    updated_at: datetime


class EventDetail(EventRead):
    # None when anonymous or never registered.
    my_registration_status: RegistrationStatus | None = None

from datetime import datetime

from app.models import RegistrationStatus
from app.schemas.common import APIModel
from app.schemas.event import EventRead


class RegistrationRead(APIModel):
    id: int
    event_id: int
    status: RegistrationStatus
    registered_at: datetime


class MyRegistrationRead(APIModel):
    """Row on the My Registrations page. Includes the event so its status
    (e.g. cancelled by the organizer) is visible."""

    id: int
    status: RegistrationStatus
    registered_at: datetime
    event: EventRead


class ParticipantRead(APIModel):
    user_id: int
    display_name: str
    registered_at: datetime


class ParticipantList(APIModel):
    event_id: int
    count: int
    participants: list[ParticipantRead]

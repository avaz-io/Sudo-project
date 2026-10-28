"""Import every model here so Base.metadata knows about all tables."""

from app.models.event import Event, EventCategory, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole

__all__ = [
    "Event",
    "EventCategory",
    "EventStatus",
    "Registration",
    "RegistrationStatus",
    "User",
    "UserRole",
]

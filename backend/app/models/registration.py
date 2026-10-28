from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime, str_enum, utcnow

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class RegistrationStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class Registration(Base):
    """One row per (user, event). Re-registering reactivates the cancelled row."""

    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_registrations_user_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    registered_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    status: Mapped[RegistrationStatus] = mapped_column(
        str_enum(RegistrationStatus), default=RegistrationStatus.ACTIVE
    )

    user: Mapped[User] = relationship(back_populates="registrations")
    event: Mapped[Event] = relationship(back_populates="registrations")

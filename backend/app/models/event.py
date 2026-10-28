from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime, str_enum, utcnow

if TYPE_CHECKING:
    from app.models.registration import Registration
    from app.models.user import User


class EventCategory(StrEnum):
    ACADEMIC = "academic"
    CULTURAL = "cultural"
    SOCIAL = "social"
    EXTRACURRICULAR = "extracurricular"
    SPORTS = "sports"
    OTHER = "other"


class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_events_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[EventCategory] = mapped_column(str_enum(EventCategory), index=True)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    location: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[int | None]  # None = no capacity limit
    status: Mapped[EventStatus] = mapped_column(
        str_enum(EventStatus), default=EventStatus.DRAFT, index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    organizer: Mapped[User] = relationship(back_populates="events")
    registrations: Mapped[list[Registration]] = relationship(back_populates="event")

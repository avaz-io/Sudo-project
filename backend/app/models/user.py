from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime, str_enum, utcnow

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.registration import Registration


class UserRole(StrEnum):
    USER = "user"
    ORGANIZER = "organizer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(str_enum(UserRole), default=UserRole.USER)
    # Incremented on logout; tokens carrying an older version are rejected.
    token_version: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    events: Mapped[list[Event]] = relationship(back_populates="organizer")
    registrations: Mapped[list[Registration]] = relationship(back_populates="user")

    @property
    def is_organizer(self) -> bool:
        return self.role == UserRole.ORGANIZER

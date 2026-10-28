from pydantic import EmailStr, Field

from app.models import UserRole
from app.schemas.common import APIModel, InputModel


class UserRead(APIModel):
    id: int
    email: EmailStr
    display_name: str
    role: UserRole


class UserSummary(APIModel):
    """Public view of a user, e.g. an event's organizer."""

    id: int
    display_name: str


class UserUpdate(InputModel):
    # Only the display name is editable; role/email changes are rejected (extra="forbid").
    display_name: str = Field(min_length=1, max_length=100)

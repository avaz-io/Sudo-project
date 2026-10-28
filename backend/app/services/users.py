from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserUpdate


def update_profile(db: Session, user: User, body: UserUpdate) -> User:
    """FR-04: only the display name is editable. Role and email can't be sent at all."""
    user.display_name = body.display_name
    db.commit()
    return user

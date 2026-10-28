"""Organizer setup procedure (FR-07: organizer access is granted outside the API).

Creates an organizer account, or promotes an existing account to organizer.
Run from backend/ with the venv active:

    python -m app.seed organizer@newuu.uz "Organizer Name" password123
"""

import argparse

from sqlalchemy import select

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User, UserRole


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote an organizer account.")
    parser.add_argument("email")
    parser.add_argument("display_name")
    parser.add_argument("password", help="at least 8 characters (ignored when promoting)")
    args = parser.parse_args()

    email = args.email.strip().lower()
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            user.role = UserRole.ORGANIZER
            print(f"Promoted existing user {email} to organizer.")
        else:
            if len(args.password) < 8:
                parser.error("password must be at least 8 characters")
            db.add(
                User(
                    email=email,
                    display_name=args.display_name.strip(),
                    password_hash=hash_password(args.password),
                    role=UserRole.ORGANIZER,
                )
            )
            print(f"Created organizer {email}.")
        db.commit()


if __name__ == "__main__":
    main()

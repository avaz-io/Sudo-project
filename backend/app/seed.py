"""Setup procedures: organizer accounts (FR-07) and demo content.

FR-07 says organizer access is granted outside the API. This creates an organizer account
or promotes an existing account to organizer. Run from backend/ with the venv active:

    python -m app.seed organizer@newuu.uz "Organizer Name" password123

Demo content (users, events, registrations) so a fresh database isn't empty:

    python -m app.seed --demo

The server also seeds the demo content on startup when SEED_DEMO_DATA=true. Either way it
only seeds a database with no events, so running it again never duplicates anything. Event
times are relative to "now", so a fresh database always has upcoming events. All demo
accounts use the password DEMO_PASSWORD.
"""

import argparse
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.db.types import utcnow
from app.models import (
    Event,
    EventCategory,
    EventStatus,
    Registration,
    RegistrationStatus,
    User,
    UserRole,
)

DEMO_PASSWORD = "password123"

_DEMO_USERS = [
    ("organizer@newuu.uz", "Student Affairs Office", UserRole.ORGANIZER),
    ("clubs@newuu.uz", "Student Clubs Council", UserRole.ORGANIZER),
    ("student@newuu.uz", "Aziza Karimova", UserRole.USER),
    ("student2@newuu.uz", "Timur Rashidov", UserRole.USER),
    ("student3@newuu.uz", "Madina Yusupova", UserRole.USER),
    ("student4@newuu.uz", "Jasur Aliyev", UserRole.USER),
    ("student5@newuu.uz", "Nilufar Tursunova", UserRole.USER),
]

# (organizer email, title, description, category, days from now, location, capacity, status)
_DEMO_EVENTS = [
    (
        "organizer@newuu.uz",
        "AI in Education: Guest Lecture",
        "A guest lecture on how machine learning is changing teaching and assessment, "
        "followed by an open Q&A session.",
        EventCategory.ACADEMIC,
        5,
        "Main Building, Hall A",
        120,
        EventStatus.PUBLISHED,
    ),
    (
        "organizer@newuu.uz",
        "Career Fair 2026",
        "Meet recruiters from leading companies in Tashkent. Bring your CV and dress "
        "professionally.",
        EventCategory.ACADEMIC,
        12,
        "Sports Complex",
        None,
        EventStatus.PUBLISHED,
    ),
    (
        "organizer@newuu.uz",
        "Research Writing Workshop",
        "Hands-on workshop on structuring research papers, citing sources, and avoiding "
        "plagiarism. Seats are limited.",
        EventCategory.ACADEMIC,
        3,
        "Library, Room 204",
        3,
        EventStatus.PUBLISHED,
    ),
    (
        "organizer@newuu.uz",
        "Python for Data Analysis Bootcamp",
        "A two-hour practical session on pandas and data visualization. Bring a laptop "
        "with Python installed.",
        EventCategory.ACADEMIC,
        8,
        "IT Lab, Room 105",
        30,
        EventStatus.PUBLISHED,
    ),
    (
        "organizer@newuu.uz",
        "Mental Health Awareness Talk",
        "University counselors share practical strategies for managing exam stress and "
        "where to find support on campus.",
        EventCategory.OTHER,
        6,
        "Main Building, Hall B",
        80,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Navruz Cultural Festival",
        "Celebrate with traditional music, dance performances, and national dishes "
        "prepared by student clubs.",
        EventCategory.CULTURAL,
        20,
        "University Courtyard",
        300,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "International Food Day",
        "Students from different countries share dishes and stories from home.",
        EventCategory.CULTURAL,
        17,
        "Cafeteria Terrace",
        None,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Inter-Faculty Football Cup",
        "Faculties compete in a one-day football tournament. Players and supporters welcome.",
        EventCategory.SPORTS,
        9,
        "University Stadium",
        200,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Morning Campus Run",
        "A friendly 5 km run around campus. All fitness levels welcome.",
        EventCategory.SPORTS,
        1,
        "Main Gate",
        50,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Board Games Night",
        "A relaxed evening of strategy and party games. Snacks provided.",
        EventCategory.SOCIAL,
        2,
        "Student Lounge",
        40,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Movie Night: Student Picks",
        "Vote for the film when you arrive. Popcorn provided.",
        EventCategory.SOCIAL,
        11,
        "Main Building, Hall A",
        100,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Debate Club Open Tournament",
        "British Parliamentary format debate tournament open to all students.",
        EventCategory.EXTRACURRICULAR,
        15,
        "Main Building, Room 310",
        48,
        EventStatus.PUBLISHED,
    ),
    (
        "clubs@newuu.uz",
        "Robotics Club Showcase",
        "See the robots the club built this semester and try controlling them yourself.",
        EventCategory.EXTRACURRICULAR,
        24,
        "Engineering Building, Lobby",
        60,
        EventStatus.PUBLISHED,
    ),
    (
        "organizer@newuu.uz",
        "Spring Volunteering Day",
        "Draft: details are still being confirmed with partner organizations.",
        EventCategory.OTHER,
        30,
        "To be announced",
        60,
        EventStatus.DRAFT,
    ),
    (
        "clubs@newuu.uz",
        "Photography Walk",
        "Cancelled because of the weather forecast.",
        EventCategory.CULTURAL,
        4,
        "Main Gate",
        25,
        EventStatus.CANCELLED,
    ),
    (
        "organizer@newuu.uz",
        "Freshers' Orientation",
        "Welcome session for first-year students covering campus services and facilities.",
        EventCategory.SOCIAL,
        -10,
        "Main Building, Hall A",
        150,
        EventStatus.COMPLETED,
    ),
]

# (student email, event title, status)
_DEMO_REGISTRATIONS = [
    ("student@newuu.uz", "AI in Education: Guest Lecture", RegistrationStatus.ACTIVE),
    ("student@newuu.uz", "Board Games Night", RegistrationStatus.ACTIVE),
    ("student@newuu.uz", "Research Writing Workshop", RegistrationStatus.ACTIVE),
    ("student@newuu.uz", "Python for Data Analysis Bootcamp", RegistrationStatus.ACTIVE),
    ("student@newuu.uz", "Movie Night: Student Picks", RegistrationStatus.CANCELLED),
    ("student@newuu.uz", "Photography Walk", RegistrationStatus.ACTIVE),
    ("student@newuu.uz", "Freshers' Orientation", RegistrationStatus.ACTIVE),
    ("student2@newuu.uz", "Research Writing Workshop", RegistrationStatus.ACTIVE),
    ("student2@newuu.uz", "Inter-Faculty Football Cup", RegistrationStatus.ACTIVE),
    ("student2@newuu.uz", "Morning Campus Run", RegistrationStatus.ACTIVE),
    ("student2@newuu.uz", "Freshers' Orientation", RegistrationStatus.ACTIVE),
    ("student3@newuu.uz", "Research Writing Workshop", RegistrationStatus.ACTIVE),
    ("student3@newuu.uz", "Navruz Cultural Festival", RegistrationStatus.ACTIVE),
    ("student3@newuu.uz", "Mental Health Awareness Talk", RegistrationStatus.ACTIVE),
    ("student4@newuu.uz", "Python for Data Analysis Bootcamp", RegistrationStatus.ACTIVE),
    ("student4@newuu.uz", "Inter-Faculty Football Cup", RegistrationStatus.ACTIVE),
    ("student4@newuu.uz", "Robotics Club Showcase", RegistrationStatus.ACTIVE),
    ("student5@newuu.uz", "International Food Day", RegistrationStatus.ACTIVE),
    ("student5@newuu.uz", "Debate Club Open Tournament", RegistrationStatus.ACTIVE),
    ("student5@newuu.uz", "Morning Campus Run", RegistrationStatus.ACTIVE),
]


def seed_demo_data(db: Session) -> bool:
    """Fills an empty database with demo users, events, and registrations.

    Returns False without changing anything if the database already has events.
    """
    if db.scalar(select(Event.id).limit(1)) is not None:
        return False

    password_hash = hash_password(DEMO_PASSWORD)
    users: dict[str, User] = {}
    for email, display_name, role in _DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email, display_name=display_name, password_hash=password_hash, role=role
            )
            db.add(user)
        users[email] = user

    now = utcnow().replace(minute=0, second=0, microsecond=0)
    events: dict[str, Event] = {}
    for organizer, title, description, category, days, location, capacity, status in (
        _DEMO_EVENTS
    ):
        event = Event(
            organizer=users[organizer],
            title=title,
            description=description,
            category=category,
            starts_at=now + timedelta(days=days, hours=2),
            location=location,
            capacity=capacity,
            status=status,
        )
        db.add(event)
        events[title] = event

    for email, title, status in _DEMO_REGISTRATIONS:
        db.add(Registration(user=users[email], event=events[title], status=status))

    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or promote an organizer account, or seed demo content."
    )
    parser.add_argument(
        "--demo", action="store_true", help="seed demo users, events, and registrations"
    )
    parser.add_argument("email", nargs="?")
    parser.add_argument("display_name", nargs="?")
    parser.add_argument(
        "password", nargs="?", help="at least 8 characters (ignored when promoting)"
    )
    args = parser.parse_args()

    if args.demo:
        if args.email is not None:
            parser.error("--demo takes no other arguments")
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            if seed_demo_data(db):
                print(f"Seeded demo content. Demo accounts use the password {DEMO_PASSWORD!r}.")
            else:
                print("Database already has events; demo content not seeded.")
        return

    if args.password is None:
        parser.error("the following arguments are required: email, display_name, password")

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

import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Equipment, Room, User, UserRole
from app.security import get_password_hash


def get_or_create_equipment(db: Session, title: str, category: str) -> Equipment:
    equipment = db.scalar(select(Equipment).where(Equipment.title == title))
    if equipment is not None:
        return equipment
    equipment = Equipment(title=title, category=category)
    db.add(equipment)
    db.flush()
    return equipment


def get_or_create_room(
    db: Session,
    name: str,
    capacity: int,
    hourly_rate: float,
    equipment: list[Equipment],
) -> Room:
    room = db.scalar(select(Room).where(Room.name == name))
    if room is not None:
        return room
    room = Room(name=name, capacity=capacity, hourly_rate=hourly_rate, equipment=equipment)
    db.add(room)
    db.flush()
    return room


def seed_admin(db: Session) -> None:
    email = os.getenv("ROOMFLOW_ADMIN_EMAIL")
    password = os.getenv("ROOMFLOW_ADMIN_PASSWORD")
    if not email or not password:
        return
    admin = db.scalar(select(User).where(User.email == email))
    if admin is not None:
        return
    db.add(
        User(
            email=email,
            full_name="Studio Admin",
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
        )
    )
    db.flush()


def seed_demo_data(db: Session) -> None:
    if os.getenv("ROOMFLOW_SEED_DEMO") != "1":
        return
    seed_admin(db)
    drum = get_or_create_equipment(db, "Drum kit", "rhythm")
    bass = get_or_create_equipment(db, "Bass amp", "amplification")
    mic = get_or_create_equipment(db, "Vocal microphone", "vocal")
    piano = get_or_create_equipment(db, "Stage piano", "keys")
    get_or_create_room(db, "Neon Garage", 6, 1800, [drum, bass, mic])
    get_or_create_room(db, "Velvet Room", 4, 1400, [mic, piano])
    get_or_create_room(db, "Loft Stage", 10, 2600, [drum, bass, mic, piano])
    db.commit()

import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import Base, engine, session_factory
from app.models import Equipment, Room, User, UserRole
from app.security import get_password_hash


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Set {name}")
    return value


def get_or_create_equipment(db, title: str, category: str) -> Equipment:
    equipment = db.scalar(select(Equipment).where(Equipment.title == title))
    if equipment is not None:
        return equipment
    equipment = Equipment(title=title, category=category)
    db.add(equipment)
    db.flush()
    return equipment


def get_or_create_room(db, name: str, capacity: int, hourly_rate: float, equipment: list[Equipment]) -> Room:
    room = db.scalar(select(Room).where(Room.name == name))
    if room is not None:
        return room
    room = Room(name=name, capacity=capacity, hourly_rate=hourly_rate, equipment=equipment)
    db.add(room)
    db.flush()
    return room


def main() -> None:
    email = require_env("ROOMFLOW_ADMIN_EMAIL")
    password = require_env("ROOMFLOW_ADMIN_PASSWORD")
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    try:
        admin = db.scalar(select(User).where(User.email == email))
        if admin is None:
            admin = User(
                email=email,
                full_name="Studio Admin",
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.flush()
        drum = get_or_create_equipment(db, "Drum kit", "rhythm")
        bass = get_or_create_equipment(db, "Bass amp", "amplification")
        mic = get_or_create_equipment(db, "Vocal microphone", "vocal")
        piano = get_or_create_equipment(db, "Stage piano", "keys")
        get_or_create_room(db, "Neon Garage", 6, 1800, [drum, bass, mic])
        get_or_create_room(db, "Velvet Room", 4, 1400, [mic, piano])
        get_or_create_room(db, "Loft Stage", 10, 2600, [drum, bass, mic, piano])
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()

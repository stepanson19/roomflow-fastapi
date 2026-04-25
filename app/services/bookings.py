from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Room
from app.schemas import BookingCreate, BookingUpdate


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def calculate_total_price(room: Room, starts_at: datetime, ends_at: datetime) -> float:
    hours = (ends_at - starts_at).total_seconds() / 3600
    return round(room.hourly_rate * hours, 2)


def get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def ensure_room_can_be_booked(room: Room, participant_count: int) -> None:
    if not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Room is inactive",
        )
    if room.capacity < participant_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Room capacity is too small for this booking",
        )


def booking_has_overlap(
    db: Session,
    room_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    query = select(Booking).where(
        Booking.room_id == room_id,
        Booking.status == BookingStatus.BOOKED,
        Booking.starts_at < ends_at,
        Booking.ends_at > starts_at,
    )
    if exclude_booking_id is not None:
        query = query.where(Booking.id != exclude_booking_id)
    return db.scalar(query) is not None


def create_booking(db: Session, user_id: int, payload: BookingCreate) -> Booking:
    room = get_room_or_404(db, payload.room_id)
    starts_at = normalize_datetime(payload.starts_at)
    ends_at = normalize_datetime(payload.ends_at)
    ensure_room_can_be_booked(room, payload.participant_count)
    if booking_has_overlap(db, room.id, starts_at, ends_at):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is already booked")
    booking = Booking(
        user_id=user_id,
        room_id=room.id,
        starts_at=starts_at,
        ends_at=ends_at,
        participant_count=payload.participant_count,
        total_price=calculate_total_price(room, starts_at, ends_at),
        note=payload.note,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def update_booking(db: Session, booking: Booking, payload: BookingUpdate) -> Booking:
    changes = payload.model_dump(exclude_unset=True)
    starts_at = normalize_datetime(changes.pop("starts_at", booking.starts_at))
    ends_at = normalize_datetime(changes.pop("ends_at", booking.ends_at))
    participant_count = changes.pop("participant_count", booking.participant_count)
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="ends_at must be later than starts_at",
        )
    ensure_room_can_be_booked(booking.room, participant_count)
    if booking_has_overlap(db, booking.room_id, starts_at, ends_at, booking.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is already booked")
    booking.starts_at = starts_at
    booking.ends_at = ends_at
    booking.participant_count = participant_count
    booking.total_price = calculate_total_price(booking.room, starts_at, ends_at)
    for field, value in changes.items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return booking

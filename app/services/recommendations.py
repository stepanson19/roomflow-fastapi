from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Booking, BookingStatus, Room
from app.schemas import RecommendationRequest, RoomSuggestion
from app.services.bookings import calculate_total_price, normalize_datetime


BookingsByRoom = dict[int, list[Booking]]


def align_to_half_hour(value: datetime) -> datetime:
    normalized = normalize_datetime(value).replace(second=0, microsecond=0)
    minute = normalized.minute
    if minute in (0, 30):
        return normalized
    if minute < 30:
        return normalized.replace(minute=30)
    return (normalized.replace(minute=0) + timedelta(hours=1))


def has_time_conflict(bookings: list[Booking], starts_at: datetime, ends_at: datetime) -> bool:
    return any(booking.starts_at < ends_at and booking.ends_at > starts_at for booking in bookings)


def load_candidate_rooms(
    db: Session,
    participants: int,
    required_equipment: set[int],
) -> list[Room]:
    rooms = db.scalars(
        select(Room)
        .options(selectinload(Room.equipment))
        .where(Room.is_active.is_(True), Room.capacity >= participants)
    ).all()
    return [
        room
        for room in rooms
        if required_equipment.issubset({equipment.id for equipment in room.equipment})
    ]


def load_bookings_by_room(
    db: Session,
    room_ids: list[int],
    starts_after: datetime,
    ends_before: datetime,
) -> BookingsByRoom:
    bookings = db.scalars(
        select(Booking).where(
            Booking.room_id.in_(room_ids),
            Booking.status == BookingStatus.BOOKED,
            Booking.starts_at < ends_before,
            Booking.ends_at > starts_after,
        )
    ).all()
    bookings_by_room: BookingsByRoom = defaultdict(list)
    for booking in bookings:
        bookings_by_room[booking.room_id].append(booking)
    return bookings_by_room


def score_slot(
    room: Room,
    participants: int,
    total_price: float,
    max_price: float | None,
    slot_index: int,
) -> float:
    capacity_gap = room.capacity - participants
    price_score = max(0, 1 - total_price / max_price) if max_price else 1 / (1 + total_price / 1000)
    return round(55 + 20 / (1 + capacity_gap) + 20 * price_score + 5 / (1 + slot_index), 2)


def build_room_slot_suggestions(
    room: Room,
    payload: RecommendationRequest,
    starts_after: datetime,
    ends_before: datetime,
    room_bookings: list[Booking],
    required_equipment: set[int],
) -> list[RoomSuggestion]:
    duration = timedelta(minutes=payload.duration_minutes)
    room_equipment_ids = {equipment.id for equipment in room.equipment}
    current_start = align_to_half_hour(starts_after)
    slot_index = 0
    suggestions: list[RoomSuggestion] = []
    while current_start + duration <= ends_before:
        current_end = current_start + duration
        total_price = calculate_total_price(room, current_start, current_end)
        in_budget = payload.max_price is None or total_price <= payload.max_price
        if in_budget and not has_time_conflict(room_bookings, current_start, current_end):
            suggestions.append(
                RoomSuggestion(
                    room_id=room.id,
                    room_name=room.name,
                    starts_at=current_start,
                    ends_at=current_end,
                    total_price=total_price,
                    score=score_slot(
                        room,
                        payload.participants,
                        total_price,
                        payload.max_price,
                        slot_index,
                    ),
                    matched_equipment_ids=sorted(room_equipment_ids & required_equipment),
                )
            )
        current_start += timedelta(minutes=30)
        slot_index += 1
    return suggestions


def build_room_suggestions(db: Session, payload: RecommendationRequest) -> list[RoomSuggestion]:
    starts_after = normalize_datetime(payload.starts_after)
    ends_before = normalize_datetime(payload.ends_before)
    required_equipment = set(payload.equipment_ids)
    rooms = load_candidate_rooms(db, payload.participants, required_equipment)
    if not rooms:
        return []
    room_ids = [room.id for room in rooms]
    bookings_by_room = load_bookings_by_room(db, room_ids, starts_after, ends_before)
    suggestions: list[RoomSuggestion] = []
    for room in rooms:
        suggestions.extend(
            build_room_slot_suggestions(
                room,
                payload,
                starts_after,
                ends_before,
                bookings_by_room.get(room.id, []),
                required_equipment,
            )
        )
    suggestions.sort(key=lambda item: (-item.score, item.total_price, item.starts_at))
    return suggestions[: payload.limit]

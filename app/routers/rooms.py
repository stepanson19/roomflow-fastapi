from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import require_admin
from app.models import Booking, Equipment, Room, User
from app.schemas import RoomCreate, RoomOut, RoomUpdate


router = APIRouter(prefix="/rooms", tags=["rooms"])


def get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.scalar(
        select(Room).options(selectinload(Room.equipment)).where(Room.id == room_id)
    )
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def load_equipment(db: Session, equipment_ids: list[int]) -> list[Equipment]:
    if not equipment_ids:
        return []
    equipment = list(db.scalars(select(Equipment).where(Equipment.id.in_(equipment_ids))).all())
    if len(equipment) != len(set(equipment_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some equipment was not found",
        )
    return equipment


@router.get("", response_model=list[RoomOut])
def list_rooms(
    db: Annotated[Session, Depends(get_db)],
    min_capacity: int | None = None,
    is_active: bool | None = None,
) -> list[Room]:
    query = select(Room).options(selectinload(Room.equipment)).order_by(Room.hourly_rate, Room.name)
    if min_capacity is not None:
        query = query.where(Room.capacity >= min_capacity)
    if is_active is not None:
        query = query.where(Room.is_active.is_(is_active))
    return list(db.scalars(query).all())


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Room:
    existing = db.scalar(select(Room).where(Room.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room already exists")
    room = Room(
        name=payload.name,
        capacity=payload.capacity,
        hourly_rate=payload.hourly_rate,
        is_active=payload.is_active,
        equipment=load_equipment(db, payload.equipment_ids),
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}", response_model=RoomOut)
def read_room(room_id: int, db: Annotated[Session, Depends(get_db)]) -> Room:
    return get_room_or_404(db, room_id)


@router.patch("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    payload: RoomUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Room:
    room = get_room_or_404(db, room_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        existing = db.scalar(select(Room).where(Room.name == changes["name"], Room.id != room_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room already exists")
    equipment_ids = changes.pop("equipment_ids", None)
    if equipment_ids is not None:
        room.equipment = load_equipment(db, equipment_ids)
    for field, value in changes.items():
        setattr(room, field, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    room = get_room_or_404(db, room_id)
    has_bookings = db.scalar(select(Booking).where(Booking.room_id == room_id)) is not None
    if has_bookings:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room has bookings")
    db.delete(room)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

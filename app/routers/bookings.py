from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Booking, BookingStatus, User, UserRole
from app.schemas import BookingCreate, BookingOut, BookingUpdate
from app.services.bookings import create_booking, update_booking


router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_booking_or_404(db: Session, booking_id: int) -> Booking:
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.room))
        .where(Booking.id == booking_id)
    )
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


def ensure_booking_access(current_user: User, booking: Booking) -> None:
    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("", response_model=list[BookingOut])
def list_bookings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: BookingStatus | None = None,
) -> list[Booking]:
    query = select(Booking).options(selectinload(Booking.room)).order_by(Booking.starts_at)
    if current_user.role != UserRole.ADMIN:
        query = query.where(Booking.user_id == current_user.id)
    if status_filter is not None:
        query = query.where(Booking.status == status_filter)
    return list(db.scalars(query).all())


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def add_booking(
    payload: BookingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    return create_booking(db, current_user.id, payload)


@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(
    booking_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    booking = get_booking_or_404(db, booking_id)
    ensure_booking_access(current_user, booking)
    return booking


@router.patch("/{booking_id}", response_model=BookingOut)
def patch_booking(
    booking_id: int,
    payload: BookingUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Booking:
    booking = get_booking_or_404(db, booking_id)
    ensure_booking_access(current_user, booking)
    if current_user.role != UserRole.ADMIN and payload.status == BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can complete booking",
        )
    return update_booking(db, booking, payload)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    booking = get_booking_or_404(db, booking_id)
    ensure_booking_access(current_user, booking)
    db.delete(booking)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

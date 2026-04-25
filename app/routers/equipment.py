from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Equipment, User
from app.schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate


router = APIRouter(prefix="/equipment", tags=["equipment"])


def get_equipment_or_404(db: Session, equipment_id: int) -> Equipment:
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return equipment


@router.get("", response_model=list[EquipmentOut])
def list_equipment(
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
) -> list[Equipment]:
    query = select(Equipment).order_by(Equipment.category, Equipment.title)
    if category:
        query = query.where(Equipment.category == category)
    return list(db.scalars(query).all())


@router.post("", response_model=EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Equipment:
    existing = db.scalar(select(Equipment).where(Equipment.title == payload.title))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment already exists")
    equipment = Equipment(title=payload.title, category=payload.category)
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("/{equipment_id}", response_model=EquipmentOut)
def read_equipment(equipment_id: int, db: Annotated[Session, Depends(get_db)]) -> Equipment:
    return get_equipment_or_404(db, equipment_id)


@router.patch("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Equipment:
    equipment = get_equipment_or_404(db, equipment_id)
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes:
        existing = db.scalar(
            select(Equipment).where(
                Equipment.title == changes["title"],
                Equipment.id != equipment_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Equipment already exists",
            )
    for field, value in changes.items():
        setattr(equipment, field, value)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    equipment = get_equipment_or_404(db, equipment_id)
    db.delete(equipment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

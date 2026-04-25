from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import RecommendationOut, RecommendationRequest
from app.services.recommendations import build_room_suggestions


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/rooms", response_model=RecommendationOut)
def recommend_rooms(
    payload: RecommendationRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationOut:
    return RecommendationOut(suggestions=build_room_suggestions(db, payload))

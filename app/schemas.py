from datetime import datetime, timedelta
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import BookingStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "student@example.com",
                "full_name": "Alex Student",
                "password": "StrongPass123",
            }
        }
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Alex Updated",
                "role": "member",
            }
        }
    )

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return " ".join(value.strip().split())


class UserOut(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentBase(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)

    @field_validator("title", "category")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class EquipmentCreate(EquipmentBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Guitar combo amp",
                "category": "amplification",
            }
        }
    )


class EquipmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    category: str | None = Field(default=None, min_length=2, max_length=80)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Stage piano",
                "category": "keys",
            }
        }
    )

    @field_validator("title", "category")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return " ".join(value.strip().split())


class EquipmentOut(EquipmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoomBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    capacity: int = Field(ge=1, le=200)
    hourly_rate: float = Field(gt=0, le=100000)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class RoomCreate(RoomBase):
    equipment_ids: list[int] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Neon Garage",
                "capacity": 6,
                "hourly_rate": 1800,
                "is_active": True,
                "equipment_ids": [1, 2, 3],
            }
        }
    )


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    capacity: int | None = Field(default=None, ge=1, le=200)
    hourly_rate: float | None = Field(default=None, gt=0, le=100000)
    is_active: bool | None = None
    equipment_ids: list[int] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "capacity": 8,
                "hourly_rate": 1900,
                "equipment_ids": [1, 2, 3, 4],
            }
        }
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return " ".join(value.strip().split())


class RoomOut(RoomBase):
    id: int
    equipment: list[EquipmentOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BookingBase(BaseModel):
    room_id: int = Field(gt=0)
    starts_at: datetime
    ends_at: datetime
    participant_count: int = Field(ge=1, le=200)
    note: str | None = Field(default=None, max_length=600)

    @model_validator(mode="after")
    def validate_time_window(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        if self.ends_at - self.starts_at > timedelta(hours=12):
            raise ValueError("booking cannot be longer than 12 hours")
        return self


class BookingCreate(BookingBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "room_id": 1,
                "starts_at": "2026-05-01T10:00:00",
                "ends_at": "2026-05-01T12:00:00",
                "participant_count": 4,
                "note": "Rehearsal before concert",
            }
        }
    )


class BookingUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    participant_count: int | None = Field(default=None, ge=1, le=200)
    status: BookingStatus | None = None
    note: str | None = Field(default=None, max_length=600)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "participant_count": 5,
                "note": "Need extra microphone stand",
            }
        }
    )

    @model_validator(mode="after")
    def validate_time_window(self) -> Self:
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class BookingOut(BookingBase):
    id: int
    user_id: int
    status: BookingStatus
    total_price: float
    created_at: datetime
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)


class RecommendationRequest(BaseModel):
    participants: int = Field(ge=1, le=200)
    equipment_ids: list[int] = Field(default_factory=list)
    starts_after: datetime
    ends_before: datetime
    duration_minutes: int = Field(ge=30, le=720, multiple_of=30)
    max_price: float | None = Field(default=None, gt=0, le=500000)
    limit: int = Field(default=5, ge=1, le=20)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "participants": 4,
                "equipment_ids": [1, 2],
                "starts_after": "2026-05-01T10:00:00",
                "ends_before": "2026-05-01T16:00:00",
                "duration_minutes": 120,
                "max_price": 4000,
                "limit": 3,
            }
        }
    )

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.ends_before <= self.starts_after:
            raise ValueError("ends_before must be later than starts_after")
        if self.ends_before - self.starts_after < timedelta(minutes=self.duration_minutes):
            raise ValueError("search window is shorter than requested duration")
        return self


class RoomSuggestion(BaseModel):
    room_id: int
    room_name: str
    starts_at: datetime
    ends_at: datetime
    total_price: float
    score: float
    matched_equipment_ids: list[int]


class RecommendationOut(BaseModel):
    suggestions: list[RoomSuggestion]

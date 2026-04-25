import os
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ROOMFLOW_SECRET_KEY", "test-secret-key-with-enough-length")
os.environ.setdefault("ROOMFLOW_DATABASE_URL", "sqlite:///./test-roomflow.db")

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register(client: TestClient, email: str, password: str, full_name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    register(client, "admin@example.com", "StrongPass123", "Alex Admin")
    token = login(client, "admin@example.com", "StrongPass123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def member_headers(client: TestClient, admin_headers: dict[str, str]) -> dict[str, str]:
    assert admin_headers
    register(client, "member@example.com", "StrongPass123", "Mira Member")
    token = login(client, "member@example.com", "StrongPass123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def equipment_ids(client: TestClient, admin_headers: dict[str, str]) -> list[int]:
    payloads = [
        {"title": "Drum kit", "category": "rhythm"},
        {"title": "Bass amp", "category": "amplification"},
        {"title": "Vocal microphone", "category": "vocal"},
    ]
    ids = []
    for payload in payloads:
        response = client.post("/api/v1/equipment", json=payload, headers=admin_headers)
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    return ids


@pytest.fixture()
def room_id(
    client: TestClient,
    admin_headers: dict[str, str],
    equipment_ids: list[int],
) -> int:
    response = client.post(
        "/api/v1/rooms",
        json={
            "name": "Neon Garage",
            "capacity": 6,
            "hourly_rate": 1800,
            "equipment_ids": equipment_ids,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture()
def tomorrow_start() -> datetime:
    return (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0, tzinfo=None
    )

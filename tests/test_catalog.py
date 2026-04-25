from fastapi.testclient import TestClient


def test_admin_manages_equipment(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/v1/equipment",
        json={"title": "Stage piano", "category": "keys"},
        headers=admin_headers,
    )
    equipment_id = created.json()["id"]

    listed = client.get("/api/v1/equipment", params={"category": "keys"})
    updated = client.patch(
        f"/api/v1/equipment/{equipment_id}",
        json={"category": "keyboard"},
        headers=admin_headers,
    )
    deleted = client.delete(f"/api/v1/equipment/{equipment_id}", headers=admin_headers)
    missing = client.get(f"/api/v1/equipment/{equipment_id}")

    assert created.status_code == 201
    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "Stage piano"
    assert updated.status_code == 200
    assert updated.json()["category"] == "keyboard"
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_member_cannot_create_catalog_items(
    client: TestClient,
    member_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/equipment",
        json={"title": "Mixer", "category": "sound"},
        headers=member_headers,
    )

    assert response.status_code == 403


def test_admin_creates_updates_and_filters_rooms(
    client: TestClient,
    admin_headers: dict[str, str],
    equipment_ids: list[int],
) -> None:
    created = client.post(
        "/api/v1/rooms",
        json={
            "name": "Blue Box",
            "capacity": 5,
            "hourly_rate": 1500,
            "equipment_ids": equipment_ids[:2],
        },
        headers=admin_headers,
    )
    room_id = created.json()["id"]

    filtered = client.get("/api/v1/rooms", params={"min_capacity": 4, "is_active": True})
    updated = client.patch(
        f"/api/v1/rooms/{room_id}",
        json={"hourly_rate": 1600, "equipment_ids": equipment_ids},
        headers=admin_headers,
    )
    read_room = client.get(f"/api/v1/rooms/{room_id}")
    deleted = client.delete(f"/api/v1/rooms/{room_id}", headers=admin_headers)

    assert created.status_code == 201
    assert filtered.status_code == 200
    assert filtered.json()[0]["name"] == "Blue Box"
    assert updated.status_code == 200
    assert updated.json()["hourly_rate"] == 1600
    assert len(read_room.json()["equipment"]) == 3
    assert deleted.status_code == 204

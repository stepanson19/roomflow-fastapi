from datetime import timedelta

from fastapi.testclient import TestClient


def test_member_creates_reads_updates_and_deletes_booking(
    client: TestClient,
    member_headers: dict[str, str],
    room_id: int,
    tomorrow_start,
) -> None:
    starts_at = tomorrow_start
    ends_at = starts_at + timedelta(hours=2)

    created = client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "participant_count": 4,
            "note": "evening rehearsal",
        },
        headers=member_headers,
    )
    booking_id = created.json()["id"]
    read_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=member_headers)
    updated = client.patch(
        f"/api/v1/bookings/{booking_id}",
        json={"participant_count": 5},
        headers=member_headers,
    )
    listed = client.get("/api/v1/bookings", headers=member_headers)
    deleted = client.delete(f"/api/v1/bookings/{booking_id}", headers=member_headers)

    assert created.status_code == 201
    assert created.json()["total_price"] == 3600
    assert read_booking.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["participant_count"] == 5
    assert len(listed.json()) == 1
    assert deleted.status_code == 204


def test_booking_rejects_overlap_and_capacity(
    client: TestClient,
    member_headers: dict[str, str],
    room_id: int,
    tomorrow_start,
) -> None:
    first_payload = {
        "room_id": room_id,
        "starts_at": tomorrow_start.isoformat(),
        "ends_at": (tomorrow_start + timedelta(hours=2)).isoformat(),
        "participant_count": 4,
    }
    overlap_payload = {
        "room_id": room_id,
        "starts_at": (tomorrow_start + timedelta(hours=1)).isoformat(),
        "ends_at": (tomorrow_start + timedelta(hours=3)).isoformat(),
        "participant_count": 4,
    }
    large_group_payload = {
        "room_id": room_id,
        "starts_at": (tomorrow_start + timedelta(hours=4)).isoformat(),
        "ends_at": (tomorrow_start + timedelta(hours=5)).isoformat(),
        "participant_count": 20,
    }

    created = client.post("/api/v1/bookings", json=first_payload, headers=member_headers)
    overlap = client.post("/api/v1/bookings", json=overlap_payload, headers=member_headers)
    capacity = client.post("/api/v1/bookings", json=large_group_payload, headers=member_headers)

    assert created.status_code == 201
    assert overlap.status_code == 409
    assert capacity.status_code == 422


def test_recommendation_skips_busy_slots_and_respects_budget(
    client: TestClient,
    member_headers: dict[str, str],
    room_id: int,
    equipment_ids: list[int],
    tomorrow_start,
) -> None:
    busy_start = tomorrow_start
    busy_end = busy_start + timedelta(hours=2)
    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "starts_at": busy_start.isoformat(),
            "ends_at": busy_end.isoformat(),
            "participant_count": 4,
        },
        headers=member_headers,
    )

    recommendation = client.post(
        "/api/v1/recommendations/rooms",
        json={
            "participants": 4,
            "equipment_ids": equipment_ids[:2],
            "starts_after": busy_start.isoformat(),
            "ends_before": (busy_start + timedelta(hours=5)).isoformat(),
            "duration_minutes": 120,
            "max_price": 4000,
            "limit": 3,
        },
        headers=member_headers,
    )
    suggestions = recommendation.json()["suggestions"]

    assert booking_response.status_code == 201
    assert recommendation.status_code == 200
    assert suggestions
    assert suggestions[0]["starts_at"] >= busy_end.isoformat()
    assert suggestions[0]["total_price"] <= 4000
    assert set(suggestions[0]["matched_equipment_ids"]) == set(equipment_ids[:2])


def test_recommendation_requires_auth(
    client: TestClient,
    room_id: int,
    equipment_ids: list[int],
    tomorrow_start,
) -> None:
    assert room_id
    response = client.post(
        "/api/v1/recommendations/rooms",
        json={
            "participants": 4,
            "equipment_ids": equipment_ids[:1],
            "starts_after": tomorrow_start.isoformat(),
            "ends_before": (tomorrow_start + timedelta(hours=3)).isoformat(),
            "duration_minutes": 60,
        },
    )

    assert response.status_code == 401

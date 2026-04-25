from fastapi.testclient import TestClient

from tests.conftest import login, register


def test_first_user_becomes_admin_and_can_read_profile(client: TestClient) -> None:
    user = register(client, "owner@example.com", "StrongPass123", "Owner User")
    token = login(client, "owner@example.com", "StrongPass123")

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == user["email"]
    assert response.json()["role"] == "admin"


def test_duplicate_registration_and_wrong_login_return_errors(client: TestClient) -> None:
    register(client, "repeat@example.com", "StrongPass123", "Repeat User")

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "repeat@example.com",
            "password": "StrongPass123",
            "full_name": "Repeat User",
        },
    )
    wrong_login = client.post(
        "/api/v1/auth/login",
        data={"username": "repeat@example.com", "password": "bad-password"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"
    assert wrong_login.status_code == 401


def test_admin_lists_users_and_member_cannot(client: TestClient, member_headers: dict[str, str]) -> None:
    admin_token = login(client, "admin@example.com", "StrongPass123")

    admin_response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    member_response = client.get("/api/v1/users", headers=member_headers)

    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 2
    assert member_response.status_code == 403


def test_user_can_update_self_but_not_role(client: TestClient, member_headers: dict[str, str]) -> None:
    profile = client.get("/api/v1/auth/me", headers=member_headers).json()

    updated = client.patch(
        f"/api/v1/users/{profile['id']}",
        json={"full_name": "Mira Updated"},
        headers=member_headers,
    )
    forbidden = client.patch(
        f"/api/v1/users/{profile['id']}",
        json={"role": "admin"},
        headers=member_headers,
    )

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Mira Updated"
    assert forbidden.status_code == 403

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_signup_and_login_flow():
    signup_payload = {
        "email": "tester@example.com",
        "password": "Secret123!",
        "full_name": "Test User",
    }

    signup_response = client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_token_returns_new_access_token():
    signup_payload = {
        "email": "refresh@example.com",
        "password": "Secret123!",
        "full_name": "Refresh User",
    }
    client.post("/auth/signup", json=signup_payload)

    login_response = client.post(
        "/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["access_token"]
    assert data["refresh_token"]

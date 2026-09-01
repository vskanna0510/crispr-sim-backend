import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_google_auth_new_user():
    email = "google_user_test_01@gmail.com"
    res = client.post(
        "/auth/google",
        json={
            "id_token": "mock_google_id_token_12345",
            "email": email,
            "full_name": "Google Research Scientist",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["full_name"] == "Google Research Scientist"
    assert data["user"]["is_active"] is True

def test_google_auth_existing_user_login():
    email = "google_user_test_01@gmail.com"
    res = client.post(
        "/auth/google",
        json={
            "id_token": "mock_google_id_token_67890",
            "email": email,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

def test_google_auth_invalid_email():
    res = client.post(
        "/auth/google",
        json={
            "id_token": "mock_google_id_token_xyz",
            "email": "invalid_email_format",
        },
    )
    assert res.status_code == 422

def test_google_auth_missing_credentials():
    res = client.post("/auth/google", json={})
    assert res.status_code in (400, 422)

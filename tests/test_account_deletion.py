import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_delete_account():
    # 1. Register test user
    email = "delete_me_user@gmail.com"
    res = client.post(
        "/auth/google",
        json={
            "id_token": "mock_delete_token",
            "email": email,
            "full_name": "Temporary User",
        },
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    # 2. Verify account info
    res_me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == email

    # 3. Delete account
    res_del = client.delete("/auth/delete-account", headers={"Authorization": f"Bearer {token}"})
    assert res_del.status_code == 200
    assert "deleted" in res_del.json()["message"]

    # 4. Verify account no longer exists
    res_after = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_after.status_code in (401, 404)

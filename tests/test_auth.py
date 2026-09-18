import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_admin_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "radek", "password": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "radek"
    assert data["user"]["role"] == "admin"

def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "radek", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Nesprávné" in response.json()["detail"]

def test_get_me_with_valid_token(client):
    login_res = client.post(
        "/api/auth/login",
        json={"username": "radek", "password": "admin"}
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["username"] == "radek"

def test_wife_login(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "monika", "password": "monika"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "monika"
    assert data["user"]["role"] == "user"

def test_non_admin_cannot_create_user(client):
    # Log in as Monika (regular user)
    login_res = client.post(
        "/api/auth/login",
        json={"username": "monika", "password": "monika"}
    )
    token = login_res.json()["access_token"]

    res = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "hacker",
            "password": "123",
            "display_name": "Hacker"
        }
    )
    assert res.status_code == 403

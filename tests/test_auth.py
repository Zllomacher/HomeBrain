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

def test_register_new_user(client):
    res = client.post(
        "/api/auth/register",
        json={
            "username": "pepa",
            "display_name": "Pepa z depa",
            "password": "pepa_heslo_123",
            "initial_email": "pepa@depo.cz"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "pepa"

def test_update_profile(client):
    login_res = client.post(
        "/api/auth/login",
        json={"username": "pepa", "password": "pepa_heslo_123"}
    )
    token = login_res.json()["access_token"]

    update_res = client.put(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Josef Novák",
            "current_password": "pepa_heslo_123",
            "new_password": "nove_heslo_456"
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["display_name"] == "Josef Novák"

    # Verify login with new password
    login_new = client.post(
        "/api/auth/login",
        json={"username": "pepa", "password": "nove_heslo_456"}
    )
    assert login_new.status_code == 200

def test_non_admin_cannot_create_user(client):
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

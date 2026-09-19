import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def auth_client():
    client = TestClient(app)
    login_res = client.post(
        "/api/auth/login",
        json={"username": "radek", "password": "admin"}
    )
    token = login_res.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

def test_get_categories(auth_client):
    res = auth_client.get("/api/settings/categories")
    assert res.status_code == 200
    cats = res.json()
    assert len(cats) >= 4
    names = [c["name"] for c in cats]
    assert "Paragon" in names
    assert "Lékařská zpráva" in names

def test_add_edit_and_delete_category(auth_client):
    # Add new category
    create_res = auth_client.post(
        "/api/settings/categories",
        json={
            "name": "Pojištění",
            "icon": "file-text",
            "target_folder_name": "Pojisteni"
        }
    )
    assert create_res.status_code == 200
    new_cat = create_res.json()
    assert new_cat["name"] == "Pojištění"

    # Edit category
    edit_res = auth_client.put(
        f"/api/settings/categories/{new_cat['id']}",
        json={
            "name": "Pojištění a smlouvy",
            "icon": "home",
            "target_folder_name": "Pojisteni_Smlouvy"
        }
    )
    assert edit_res.status_code == 200
    edited = edit_res.json()
    assert edited["name"] == "Pojištění a smlouvy"
    assert edited["target_folder_name"] == "Pojisteni_Smlouvy"

    # Delete it
    del_res = auth_client.delete(f"/api/settings/categories/{new_cat['id']}")
    assert del_res.status_code == 200

def test_upload_document_and_check_inbox(auth_client):
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")
    files = {"file": ("test_paragon.jpg", fake_image, "image/jpeg")}
    data = {
        "category_id": 1,
        "target_email": "radek.prace@firma.cz",
        "note": "Parkování u kliniky"
    }

    upload_res = auth_client.post("/api/documents/upload", data=data, files=files)
    assert upload_res.status_code == 200
    doc = upload_res.json()
    assert doc["status"] == "pending"
    assert doc["sent_to_email"] == "radek.prace@firma.cz"
    assert doc["email_status"] in ["sent", "mock_sent"]
    assert "Parkování" in doc["email_subject"]

    # Check that document appears in inbox
    inbox_res = auth_client.get("/api/documents/inbox?status_filter=pending")
    assert inbox_res.status_code == 200
    inbox = inbox_res.json()
    matching = [d for d in inbox if d["id"] == doc["id"]]
    assert len(matching) == 1

    # Mark document as saved_to_pc
    update_res = auth_client.put(
        f"/api/documents/{doc['id']}/status",
        json={"status": "saved_to_pc"}
    )
    assert update_res.status_code == 200

    # Verify status changed
    inbox_res2 = auth_client.get("/api/documents/inbox?status_filter=saved_to_pc")
    assert inbox_res2.status_code == 200
    matching2 = [d for d in inbox_res2.json() if d["id"] == doc["id"]]
    assert len(matching2) == 1

def test_export_zip(auth_client):
    res = auth_client.get("/api/documents/export-zip?status_filter=all")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/x-zip-compressed"
    assert len(res.content) > 0

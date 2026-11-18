import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("user_data_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "local-test-secret-only"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)


def _account(email):
    client.post("/auth/register", json={"name": email, "email": email, "password": "Passw0rd!x"})
    response = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_data_requires_authentication():
    assert client.get("/user-data/journal").status_code == 401
    assert client.post("/user-data/journal", json={"data": {"text": "x"}}).status_code == 401


def test_user_data_crud_and_owner_isolation():
    owner = _account(f"user-data-owner-{datetime.now().strftime("%Y%m%d%H%M%S%f")}@example.com")
    other = _account(f"user-data-other-{datetime.now().strftime("%Y%m%d%H%M%S%f")}@example.com")
    created = client.post("/user-data/journal", headers=owner, json={"data": {"text": "persistent entry"}})
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]
    assert client.get("/user-data/journal", headers=other).json() == []
    assert client.put(f"/user-data/journal/{record_id}", headers=other, json={"data": {"text": "stolen"}}).status_code == 404
    loaded = client.get("/user-data/journal", headers=owner).json()
    assert len(loaded) == 1 and loaded[0]["data"]["text"] == "persistent entry"
    updated = client.put(f"/user-data/journal/{record_id}", headers=owner, json={"data": {"text": "updated"}})
    assert updated.status_code == 200 and updated.json()["data"]["text"] == "updated"
    assert client.delete(f"/user-data/journal/{record_id}", headers=owner).status_code == 204
    assert client.get("/user-data/journal", headers=owner).json() == []


def test_daily_log_update_and_periodization_delete_are_owner_scoped():
    owner = _account(f"tracker-owner-{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com")
    other = _account(f"tracker-other-{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com")
    daily = client.post("/daily-log/", headers=owner, json={"calories": 1200, "date": "2026-10-30T12:00:00"})
    assert daily.status_code == 200, daily.text
    log_id = daily.json()["id"]
    assert client.put(f"/daily-log/{log_id}", headers=other, json={"calories": 1500}).status_code == 404
    assert client.put(f"/daily-log/{log_id}", headers=owner, json={"calories": 1500}).json()["calories"] == 1500
    block = client.post("/periodization/", headers=owner, json={"block_name": "Base", "focus": "Strength", "start_date": "2026-10-30T00:00:00", "end_date": "2026-11-27T00:00:00"})
    assert block.status_code == 200, block.text
    block_id = block.json()["id"]
    assert client.delete(f"/periodization/{block_id}", headers=other).status_code == 404
    assert client.delete(f"/periodization/{block_id}", headers=owner).status_code == 204

import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "pro_area_test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

import pytest
from fastapi.testclient import TestClient
from app.database.migrate import run_migrations
from app.main import app
from app.database.connection import SessionLocal
from app.models.injury import Injury
from app.models.login_log import LoginLog
from app.models.org_membership import OrganizationMembership
from app.models.hardware import UserDevice

run_migrations()
client = TestClient(app)


def register_and_login(email):
    response = client.post("/auth/register", json={"name": email, "email": email, "password": "GoodPass123!"})
    assert response.status_code == 200, response.text
    response = client.post("/auth/login", json={"email": email, "password": "GoodPass123!"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_owned_area_apis_require_authentication():
    assert client.get("/org/mine").status_code == 401
    assert client.get("/hardware/me/devices").status_code == 401
    assert client.get("/medical/injury/me").status_code == 401
    assert client.get("/ai/records").status_code == 401
    assert client.post("/live/class/join", json={"class_id": 1}).status_code == 401
    assert client.get("/medical/recovery/protocol/1").status_code == 401


def test_login_records_event_and_injury_body_cannot_choose_owner():
    owner = register_and_login("injury-owner@example.com")
    other = register_and_login("injury-other@example.com")
    db = SessionLocal()
    try:
        owner_id = int(client.get("/auth/me", headers=owner).json()["id"])
        other_id = int(client.get("/auth/me", headers=other).json()["id"])
        assert db.query(LoginLog).filter(LoginLog.user_id == owner_id).count() >= 1
    finally:
        db.close()
    response = client.post("/medical/injury/log", headers=owner, json={"user_id": other_id, "type": "ankle sprain", "severity": "moderate", "occurred_at": "2026-10-30T12:00:00"})
    assert response.status_code == 200, response.text
    injury_id = response.json()["id"]
    db = SessionLocal()
    try:
        assert db.query(Injury).filter_by(id=injury_id).one().user_id == owner_id
    finally:
        db.close()
    pt = client.post("/medical/pt/create", headers=owner, json={"injury_id": injury_id, "name": "Clinician PT plan"})
    assert pt.status_code == 200 and pt.json().get("id")
    assert client.get(f"/medical/pt/injury/{injury_id}", headers=owner).json()[0]["name"] == "Clinician PT plan"
    protocol = client.post("/medical/recovery/create", headers=owner, json={"injury_id": injury_id, "name": "Clinician recovery protocol"})
    assert protocol.status_code == 200 and protocol.json().get("id")
    assert client.get(f"/medical/recovery/injury/{injury_id}", headers=owner).json()[0]["name"] == "Clinician recovery protocol"
    assert client.get(f"/medical/injury/{injury_id}", headers=other).status_code == 404
    assert client.post(f"/medical/injury/{injury_id}/resolve", headers=other).status_code == 404
    assert client.get(f"/medical/pt/injury/{injury_id}", headers=other).status_code == 404


def test_hardware_data_is_scoped_and_sync_does_not_fabricate_metrics():
    owner = register_and_login("hardware-owner@example.com")
    other = register_and_login("hardware-other@example.com")
    owner_id = int(client.get("/auth/me", headers=owner).json()["id"])
    response = client.post("/hardware/link", headers=owner, json={"user_id": 999999, "provider": "garmin", "access_token": "private-token"})
    assert response.status_code == 501
    db = SessionLocal()
    try:
        assert db.query(UserDevice).filter_by(user_id=owner_id, provider="garmin").count() == 0
        db.add(UserDevice(user_id=owner_id, provider="garmin", access_token="legacy-test-token", status="linked"))
        db.commit()
    finally:
        db.close()
    assert len(client.get("/hardware/me/devices", headers=owner).json()) == 1
    assert client.get(f"/hardware/{owner_id}/garmin/status", headers=other).status_code == 404
    assert client.post("/hardware/sync", headers=owner, json={"provider": "garmin"}).status_code == 501


def test_org_access_is_member_scoped_and_roles_are_persistent():
    owner = register_and_login("org-owner@example.com")
    outsider = register_and_login("org-outsider@example.com")
    created = client.post("/org/create", headers=owner, json={"name": "Private Org"})
    assert created.status_code == 200, created.text
    assert "id" in created.json(), created.text
    org_id = created.json()["id"]
    assert [row["id"] for row in client.get("/org/mine", headers=owner).json()] == [org_id]
    assert client.get(f"/org/{org_id}", headers=outsider).status_code == 404
    assert client.post(f"/org/{org_id}/tenant/create", headers=outsider, json={"name": "Nope"}).status_code == 404
    assert client.post(f"/org/{org_id}/tenant/create", headers=owner, json={"name": "Field Unit"}).status_code == 200
    assert len(client.get(f"/org/{org_id}/tenant/list", headers=owner).json()) == 1
    assert client.post(f"/org/{org_id}/members", headers=owner, json={"email": "org-outsider@example.com", "role": "member"}).status_code == 200
    assert client.get(f"/org/{org_id}", headers=outsider).status_code == 200
    assert client.post(f"/org/{org_id}/tenant/create", headers=outsider, json={"name": "Forbidden"}).status_code == 403
    members = client.get(f"/org/{org_id}/members", headers=owner)
    assert members.status_code == 200 and members.json()[0]["role"] == "owner"
    owner_member_id = next(row["id"] for row in members.json() if row["role"] == "owner")
    changed_owner = client.patch(f"/org/{org_id}/members/{owner_member_id}/role", headers=owner, json={"role": "member"})
    assert changed_owner.status_code == 400
    regular_member = next(row for row in members.json() if row["role"] == "member")
    changed_member = client.patch(f"/org/{org_id}/members/{regular_member['id']}/role", headers=owner, json={"role": "manager"})
    assert changed_member.status_code == 200 and changed_member.json()["role"] == "manager"
    db = SessionLocal()
    try:
        assert db.query(OrganizationMembership).filter_by(id=owner_member_id).one().role == "owner"
        assert db.query(OrganizationMembership).filter_by(id=regular_member["id"]).one().role == "manager"
    finally:
        db.close()


def test_ai_outputs_are_saved_and_isolated_per_authenticated_user():
    first = register_and_login("ai-first@example.com")
    second = register_and_login("ai-second@example.com")
    response = client.post("/ai/coach", headers=first, json={"user_data": {"fatigue": 6}, "message": "How hard should I train?"})
    assert response.status_code == 200, response.text
    assert response.json()["record_id"]
    own = client.get("/ai/records", headers=first)
    other = client.get("/ai/records", headers=second)
    assert len(own.json()) == 1 and own.json()[0]["feature"] == "coach"
    assert other.json() == []


def test_password_reset_flow_invalidates_old_password(monkeypatch):
    monkeypatch.setenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "true")
    headers = register_and_login("password-reset@example.com")
    request = client.post("/auth/forgot-password", json={"email": "password-reset@example.com"})
    assert request.status_code == 200 and request.json().get("debug_token")
    reset = client.post("/auth/reset-password", json={"email": "password-reset@example.com", "token": request.json()["debug_token"], "new_password": "BetterPassword456!"})
    assert reset.status_code == 200, reset.text
    assert client.post("/auth/login", json={"email": "password-reset@example.com", "password": "GoodPass123!"}).status_code == 401
    assert client.post("/auth/login", json={"email": "password-reset@example.com", "password": "BetterPassword456!"}).status_code == 200


def test_pro_area_migrations_are_idempotent():
    run_migrations()
    run_migrations()

import os
import tempfile
from datetime import datetime, timedelta

import pytest

_db_file = os.path.join(tempfile.mkdtemp(), "admin_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_file}")
os.environ.setdefault("JWT_SECRET", "unit-test-secret-not-for-production")

from fastapi.testclient import TestClient  # noqa: E402

from app.auth.jwt_handler import create_access_token  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.daily_log import DailyLog  # noqa: E402
from app.models.login_log import LoginLog  # noqa: E402
from app.models.logs import AdminAuditLog  # noqa: E402
from app.models.messages import Message  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.workout_log import WorkoutLog  # noqa: E402

run_migrations()
client = TestClient(app)
PASSWORD = "Passw0rd!x"


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def make_user(email, admin=False):
    r = client.post("/auth/register", json={"name": email.split("@")[0], "email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    uid = r.json()["id"]
    if admin:
        with SessionLocal() as db:
            db.query(User).filter(User.id == uid).update({"is_admin": True})
            db.commit()
    return uid


def user_headers(email):
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return _bearer(r.json()["access_token"])


def admin_headers(email):
    r = client.post("/admin/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return _bearer(r.json()["access_token"])


@pytest.fixture(scope="module")
def admin():
    uid = make_user("root-admin@example.com", admin=True)
    return {"id": uid, "h": admin_headers("root-admin@example.com")}


@pytest.fixture(scope="module")
def regular():
    uid = make_user("regular-joe@example.com")
    return {"id": uid, "h": user_headers("regular-joe@example.com")}


ADMIN_GETS = [
    "/admin/me", "/admin/dashboard", "/admin/analytics", "/admin/announcements", "/admin/logs",
    "/admin/messages", "/admin/users", "/admin/users/1", "/admin/system/health",
    "/admin/actions/recent", "/admin/config",
]
ADMIN_MUTATIONS = [
    ("post", "/admin/announcements", {"title": "x", "body": "y"}),
    ("put", "/admin/announcements/1", {"title": "x"}),
    ("patch", "/admin/announcements/1/publish", None),
    ("delete", "/admin/announcements/1", None),
    ("patch", "/admin/messages/1/read", None),
    ("patch", "/admin/messages/1/resolve", None),
    ("delete", "/admin/messages/1", None),
    ("patch", "/admin/users/1/admin", None),
    ("put", "/admin/users/1/role", {"is_admin": True}),
    ("patch", "/admin/users/1/suspend", None),
    ("patch", "/admin/users/1/reset-streak", None),
    ("delete", "/admin/users/1", None),
    ("post", "/admin/config", {"appearance": {}}),
]


# ---------- authorization matrix ----------

@pytest.mark.parametrize("path", ADMIN_GETS)
def test_get_endpoints_reject_anonymous_and_non_admin(path, regular):
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.get(path, headers=regular["h"]).status_code == 403


@pytest.mark.parametrize("method,path,body", ADMIN_MUTATIONS)
def test_mutations_reject_anonymous_and_non_admin(method, path, body, regular):
    def call(url, **kw):
        return client.request(method.upper(), url, **kw)

    assert call(path, json=body).status_code == 401
    assert call(path, json=body, headers=regular["h"]).status_code == 403


def test_forged_admin_claim_for_non_admin_user_is_rejected(regular):
    token = create_access_token({"sub": str(regular["id"]), "email": "regular-joe@example.com", "is_admin": True})
    assert client.get("/admin/dashboard", headers=_bearer(token)).status_code == 403


@pytest.mark.parametrize("path", [p for p in ADMIN_GETS if p not in ("/admin/users/1",)])
def test_admin_can_read_everything(path, admin):
    assert client.get(path, headers=admin["h"]).status_code == 200


def test_admin_login_rules(admin, regular):
    assert client.post("/admin/login", json={"email": "regular-joe@example.com", "password": PASSWORD}).status_code == 403
    assert client.post("/admin/login", json={"email": "root-admin@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/admin/login", json={"email": "nobody@example.com", "password": PASSWORD}).status_code == 401
    me = client.get("/admin/me", headers=admin["h"]).json()
    assert me["email"] == "root-admin@example.com" and me["is_admin"] is True


def test_admin_login_accepts_case_insensitive_email_for_browser_input():
    make_user("browser-admin@example.com", admin=True)
    response = client.post(
        "/admin/login",
        json={"email": "Browser-Admin@Example.com", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    me = client.get("/admin/me", headers=_bearer(response.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "browser-admin@example.com"


def test_demoted_admin_token_stops_working():
    admin_id = make_user("temp-admin@example.com", admin=True)
    target_id = make_user("demotion-target@example.com")
    h = admin_headers("temp-admin@example.com")
    assert client.get("/admin/dashboard", headers=h).status_code == 200
    assert client.get("/users/", headers=h).status_code == 200
    with SessionLocal() as db:
        db.query(User).filter(User.email == "temp-admin@example.com").update({"is_admin": False})
        db.commit()
    assert client.get("/admin/dashboard", headers=h).status_code == 403
    assert client.get("/admin/me", headers=h).status_code == 403
    assert client.get("/users/", headers=h).status_code == 403
    assert client.get(f"/users/{target_id}", headers=h).status_code == 403
    assert client.put(f"/users/{target_id}", headers=h, json={"name": "Unauthorized"}).status_code == 403
    assert client.delete(f"/users/{target_id}", headers=h).status_code == 403
    assert client.get(f"/users/{admin_id}", headers=h).status_code == 200


# ---------- login recording & metrics from real rows ----------

def test_logins_are_recorded_and_audited(admin):
    with SessionLocal() as db:
        before = db.query(LoginLog).count()
        audits = db.query(AdminAuditLog).filter(AdminAuditLog.action == "admin.login").count()
    admin_headers("root-admin@example.com")
    user_headers("regular-joe@example.com")
    with SessionLocal() as db:
        assert db.query(LoginLog).count() == before + 2
        assert db.query(AdminAuditLog).filter(AdminAuditLog.action == "admin.login").count() == audits + 1


def test_failed_admin_login_is_logged_as_error(admin):
    client.post("/admin/login", json={"email": "root-admin@example.com", "password": "nope"})
    logs = client.get("/admin/logs?type=error", headers=admin["h"]).json()["logs"]
    assert any("admin.login_failed" in row["message"] for row in logs)
    assert all(row["type"] == "error" for row in logs)


def test_dashboard_and_analytics_reflect_seeded_rows(admin):
    d0 = client.get("/admin/dashboard", headers=admin["h"]).json()
    a0 = client.get("/admin/analytics", headers=admin["h"]).json()
    uid = make_user("metrics-user@example.com")
    now = datetime.utcnow()
    with SessionLocal() as db:
        db.add_all([
            WorkoutLog(user_id=uid, mode="manual", manual_name="Metric Zumba", duration_minutes=30, date=now),
            WorkoutLog(user_id=uid, mode="manual", manual_name="Metric Zumba", duration_minutes=30, date=now),
            WorkoutLog(user_id=uid, mode="manual", manual_name="Ancient", duration_minutes=30, date=now - timedelta(days=30)),
            DailyLog(user_id=uid, date=now),
            Message(name="m", email="metrics-user@example.com", subject="s", message="hello", is_read=False),
            Message(name="m", email="metrics-user@example.com", subject="s", message="done", is_read=True),
        ])
        db.commit()
    d1 = client.get("/admin/dashboard", headers=admin["h"]).json()
    a1 = client.get("/admin/analytics", headers=admin["h"]).json()

    assert d1["total_users"] == d0["total_users"] + 1
    assert d1["new_users_last_7_days"] == d0["new_users_last_7_days"] + 1
    assert d1["unread_messages"] == d0["unread_messages"] + 1
    assert d1["total_logs"] == d0["total_logs"] + 4
    for key in ("total_users", "new_users_last_7_days", "total_announcements", "unread_messages", "total_logs"):
        assert isinstance(d1[key], int)

    o0, o1 = a0["overview"], a1["overview"]
    assert o1["totalUsers"] == o0["totalUsers"] + 1
    assert o1["workoutsLogged7d"] == o0["workoutsLogged7d"] + 2
    assert o1["dailyLogs7d"] == o0["dailyLogs7d"] + 1
    assert o1["activeUsers7d"] == o0["activeUsers7d"] + 1
    top = {row["label"]: row["count"] for row in a1["top_workouts"]}
    assert top["Metric Zumba"] == 2 and "Ancient" not in top
    assert any(item["user"] == "metrics-user@example.com" for item in a1["recent_activity"])
    series = a1["daily_series"]
    assert len(series) == 7 and series[-1]["date"] == now.date().isoformat()
    assert series[-1]["workouts"] >= 2


def test_analytics_and_dashboard_shapes_match_frontend(admin):
    a = client.get("/admin/analytics", headers=admin["h"]).json()
    assert {"totalUsers", "activeUsers7d", "workoutsLogged7d", "dailyLogs7d"} <= set(a["overview"])
    assert isinstance(a["top_workouts"], list) and isinstance(a["recent_activity"], list)
    for item in a["recent_activity"]:
        assert {"id", "type", "detail", "user", "time"} <= set(item)
    health = client.get("/admin/system/health", headers=admin["h"]).json()
    assert {"api_status", "database_status", "uptime"} <= set(health)
    assert health["database_status"] == "ok"
    assert "errors_24h" not in health


def test_logs_shape_filter_and_real_rows(admin):
    uid = make_user("logs-user@example.com")
    with SessionLocal() as db:
        db.add(DailyLog(user_id=uid, date=datetime.utcnow()))
        db.commit()
    body = client.get("/admin/logs", headers=admin["h"]).json()
    assert isinstance(body["logs"], list)
    for row in body["logs"]:
        assert {"id", "type", "message", "timestamp"} <= set(row)
    daily = client.get("/admin/logs?type=daily", headers=admin["h"]).json()["logs"]
    assert daily and {r["type"] for r in daily} == {"daily"}
    assert any(r["user_email"] == "logs-user@example.com" for r in daily)
    stamps = [r["timestamp"] for r in body["logs"] if r["timestamp"]]
    assert stamps == sorted(stamps, reverse=True)
    assert client.get("/admin/logs?type=all", headers=admin["h"]).status_code == 200


# ---------- announcements ----------

def test_announcement_lifecycle_and_user_feed(admin, regular):
    h = admin["h"]
    assert client.post("/admin/announcements", headers=h, json={"title": " ", "body": "x"}).status_code == 400

    created = client.post("/admin/announcements", headers=h, json={"title": "Maintenance", "body": "Tonight 9pm"})
    assert created.status_code == 200
    ann = created.json()
    assert ann["title"] == "Maintenance" and ann["body"] == "Tonight 9pm" and ann["published"] is True

    draft = client.post("/admin/announcements", headers=h, json={"title": "Draft one", "body": "wip", "published": False}).json()
    assert draft["published"] is False

    feed = client.get("/announcements", headers=regular["h"]).json()
    titles = [a["title"] for a in feed]
    assert "Maintenance" in titles and "Draft one" not in titles
    assert client.get("/announcements").status_code == 401

    upd = client.put(f"/admin/announcements/{ann['id']}", headers=h, json={"title": "Maintenance v2", "body": "Moved to 10pm"})
    assert upd.status_code == 200 and upd.json()["title"] == "Maintenance v2" and upd.json()["updated_at"]

    pub = client.patch(f"/admin/announcements/{draft['id']}/publish", headers=h, json={"published": True})
    assert pub.json()["published"] is True and pub.json()["published_at"]
    assert "Draft one" in [a["title"] for a in client.get("/announcements", headers=regular["h"]).json()]

    unpub = client.patch(f"/admin/announcements/{ann['id']}/publish", headers=h)
    assert unpub.json()["published"] is False
    assert "Maintenance v2" not in [a["title"] for a in client.get("/announcements", headers=regular["h"]).json()]

    listing = client.get("/admin/announcements", headers=h).json()
    assert {ann["id"], draft["id"]} <= {a["id"] for a in listing}

    assert client.delete(f"/admin/announcements/{ann['id']}", headers=h).status_code == 200
    assert client.delete(f"/admin/announcements/{ann['id']}", headers=h).status_code == 404
    assert client.put(f"/admin/announcements/{ann['id']}", headers=h, json={"title": "x"}).status_code == 404

    actions = [a["action"] for a in client.get("/admin/actions/recent", headers=h).json()["actions"]]
    for expected in ("announcement.create", "announcement.update", "announcement.publish",
                     "announcement.unpublish", "announcement.delete"):
        assert expected in actions


# ---------- messages ----------

def test_user_message_and_admin_inbox(admin, regular):
    assert client.post("/messages", json={"message": "hi"}).status_code == 401
    assert client.post("/messages", headers=regular["h"], json={"message": "  "}).status_code == 400
    sent = client.post("/messages", headers=regular["h"], json={"subject": "Bug", "message": "Please help"})
    assert sent.status_code == 200
    mid = sent.json()["id"]

    inbox = client.get("/admin/messages", headers=admin["h"]).json()
    msg = next(m for m in inbox if m["id"] == mid)
    assert {"id", "name", "email", "message", "resolved", "created_at"} <= set(msg)
    assert msg["email"] == "regular-joe@example.com" and msg["resolved"] is False

    toggled = client.patch(f"/admin/messages/{mid}/resolve", headers=admin["h"]).json()
    assert toggled["message"]["resolved"] is True
    assert client.patch(f"/admin/messages/{mid}/resolve", headers=admin["h"]).json()["message"]["resolved"] is False
    assert client.patch(f"/admin/messages/{mid}/read", headers=admin["h"]).json()["message"]["is_read"] is True

    assert client.delete(f"/admin/messages/{mid}", headers=admin["h"]).status_code == 200
    assert client.delete(f"/admin/messages/{mid}", headers=admin["h"]).status_code == 404
    assert client.patch("/admin/messages/999999/resolve", headers=admin["h"]).status_code == 404


# ---------- user management ----------

def test_user_list_search_and_detail(admin):
    uid = make_user("zelda-searchable@example.com")
    user_headers("zelda-searchable@example.com")
    users = client.get("/admin/users", headers=admin["h"]).json()
    assert isinstance(users, list)
    assert {"id", "name", "email", "is_admin", "is_suspended", "created_at", "last_login"} <= set(users[0])
    assert "hashed_password" not in users[0]
    found = client.get("/admin/users?q=ZELDA-search", headers=admin["h"]).json()
    assert [u["email"] for u in found] == ["zelda-searchable@example.com"]
    assert found[0]["last_login"] is not None
    assert client.get("/admin/users?q=no-such-person-xyz", headers=admin["h"]).json() == []

    detail = client.get(f"/admin/users/{uid}", headers=admin["h"]).json()
    assert detail["email"] == "zelda-searchable@example.com" and detail["is_admin"] is False
    for sub in ("workouts", "daily", "messages", "logs"):
        r = client.get(f"/admin/users/{uid}/{sub}", headers=admin["h"])
        assert r.status_code == 200 and isinstance(r.json(), list)
    assert client.get("/admin/users/99999999", headers=admin["h"]).status_code == 404
    assert client.get("/admin/users/99999999/workouts", headers=admin["h"]).status_code == 404


def test_suspend_blocks_login_and_is_reversible(admin):
    uid = make_user("suspend-me@example.com")
    h = admin["h"]
    r = client.patch(f"/admin/users/{uid}/suspend", headers=h, json={"suspended": True})
    assert r.status_code == 200 and r.json()["user"]["is_suspended"] is True
    assert client.post("/auth/login", json={"email": "suspend-me@example.com", "password": PASSWORD}).status_code == 403
    r = client.patch(f"/admin/users/{uid}/suspend", headers=h)
    assert r.json()["user"]["is_suspended"] is False
    assert client.post("/auth/login", json={"email": "suspend-me@example.com", "password": PASSWORD}).status_code == 200


def test_role_changes_reset_streak_and_guards(admin):
    h = admin["h"]
    uid = make_user("promote-me@example.com")
    r = client.patch(f"/admin/users/{uid}/admin", headers=h)
    assert r.json()["user"]["is_admin"] is True
    assert client.get("/admin/dashboard", headers=admin_headers("promote-me@example.com")).status_code == 200
    r = client.put(f"/admin/users/{uid}/role", headers=h, json={"is_admin": False})
    assert r.json()["user"]["is_admin"] is False

    with SessionLocal() as db:
        db.query(User).filter(User.id == uid).update({"streak": 5})
        db.commit()
    assert client.patch(f"/admin/users/{uid}/reset-streak", headers=h).json()["user"]["streak"] == 0

    me = admin["id"]
    assert client.patch(f"/admin/users/{me}/suspend", headers=h).status_code == 400
    assert client.delete(f"/admin/users/{me}", headers=h).status_code == 400
    assert client.put(f"/admin/users/{me}/role", headers=h, json={"is_admin": False}).status_code == 400


def test_delete_user_removes_account_and_audits(admin):
    uid = make_user("delete-me@example.com")
    assert client.delete(f"/admin/users/{uid}", headers=admin["h"]).json() == {"status": "deleted", "id": uid}
    assert client.get(f"/admin/users/{uid}", headers=admin["h"]).status_code == 404
    assert client.delete(f"/admin/users/{uid}", headers=admin["h"]).status_code == 404


def test_last_admin_cannot_be_removed():
    with SessionLocal() as db:
        db.query(User).update({"is_admin": False})
        db.commit()
    a = make_user("only-admin@example.com", admin=True)
    b = make_user("second-admin@example.com", admin=True)
    ha = admin_headers("only-admin@example.com")
    assert client.put(f"/admin/users/{b}/role", headers=ha, json={"is_admin": False}).status_code == 200
    hb_user = make_user("third@example.com", admin=True)
    assert client.delete(f"/admin/users/{hb_user}", headers=ha).status_code == 200
    # a is now the only admin; self-guards still apply
    assert client.put(f"/admin/users/{a}/role", headers=ha, json={"is_admin": False}).status_code == 400


# ---------- audit log ----------

def test_admin_actions_are_audited_with_actor(admin):
    uid = make_user("audit-target@example.com")
    # Re-promote root admin in case an earlier test reset flags.
    with SessionLocal() as db:
        db.query(User).filter(User.id == admin["id"]).update({"is_admin": True})
        db.commit()
    h = admin_headers("root-admin@example.com")
    client.patch(f"/admin/users/{uid}/suspend", headers=h, json={"suspended": True})
    client.post("/admin/config", headers=h, json={"appearance": {"theme": "dark"}})
    with SessionLocal() as db:
        suspend = (
            db.query(AdminAuditLog)
            .filter(AdminAuditLog.action == "user.suspend", AdminAuditLog.target_id == str(uid))
            .one()
        )
        assert suspend.admin_email == "root-admin@example.com" and suspend.success is True
        assert db.query(AdminAuditLog).filter(AdminAuditLog.action == "config.update").count() >= 1
    recent = client.get("/admin/actions/recent", headers=h).json()["actions"]
    assert recent and {"id", "action", "admin", "timestamp"} <= set(recent[0])
    assert client.get("/admin/config", headers=h).json()["appearance"] == {"theme": "dark"}

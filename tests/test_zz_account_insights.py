import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

DB_PATH = Path(__file__).with_name("account_insights_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "local-test-secret-only"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)
PASSWORD = "Passw0rd!x"


def _account(prefix="acct"):
    email = f"{prefix}-{uuid4().hex[:10]}@example.com"
    client.post("/auth/register", json={"name": prefix, "email": email, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": "Bearer " + token}, email


def _iso(days_ago):
    return (datetime.utcnow() - timedelta(days=days_ago)).replace(microsecond=0).isoformat()


def test_endpoints_require_authentication():
    for method, path in [
        ("get", "/insights/streaks"),
        ("get", "/insights/achievements"),
        ("get", "/insights/summary"),
        ("get", "/account/export"),
        ("get", "/account/notifications"),
        ("put", "/account/notifications"),
        ("post", "/account/change-password"),
        ("delete", "/account"),
    ]:
        assert getattr(client, method)(path).status_code == 401, path


def test_new_user_gets_honest_zeros():
    headers, _ = _account()
    streaks = client.get("/insights/streaks", headers=headers).json()
    assert streaks["overall"]["current"] == 0 and streaks["overall"]["total_days"] == 0
    assert all(v["current"] == 0 and v["longest"] == 0 for v in streaks["sources"].values())
    achievements = client.get("/insights/achievements", headers=headers).json()
    assert achievements["unlocked"] == 0 and achievements["total"] > 0
    summary = client.get("/insights/summary", headers=headers).json()
    assert summary["training"]["total_sessions"] == 0
    assert summary["weight"]["latest_kg"] is None
    assert summary["nutrition"]["avg_calories"] == 0


def test_insights_computed_from_all_sources_and_isolated():
    headers, _ = _account("insights")
    other, _ = _account("insights-other")
    for ago in (0, 1, 2):
        r = client.post("/workouts/save", headers=headers, json={
            "mode": "manual", "duration_minutes": 30, "manual_name": "Free", "timestamp": _iso(ago)})
        assert r.status_code in (200, 201), r.text
    client.post("/hydration/", headers=headers, json={"amount_ml": 500, "date": _iso(0)})
    client.post("/weight/", headers=headers, json={"weight": 80, "date": _iso(5)})
    client.post("/weight/", headers=headers, json={"weight": 78.5, "date": _iso(0)})
    client.post("/nutrition/", headers=headers, json={"calories": 2000, "protein": 150})
    client.post("/user-data/journal", headers=headers, json={"data": {"text": "x", "timestamp": _iso(0)}})
    client.post("/sports/logs/", headers=headers, json={"sport": "boxing", "duration_minutes": 45})

    streaks = client.get("/insights/streaks", headers=headers).json()
    assert streaks["sources"]["workouts"]["current"] == 3
    assert streaks["sources"]["free_training"]["current"] == 3
    assert streaks["sources"]["water"]["current"] == 1
    assert streaks["sources"]["nutrition"]["current"] == 1
    assert streaks["sources"]["journal"]["current"] == 1
    assert streaks["sources"]["weight"]["current"] == 1
    assert streaks["overall"]["current"] == 3

    achievements = {a["id"]: a for a in client.get("/insights/achievements", headers=headers).json()["items"]}
    assert achievements["first-workout"]["unlocked"] and achievements["streak-3"]["unlocked"]
    assert not achievements["streak-7"]["unlocked"]

    summary = client.get("/insights/summary", headers=headers).json()
    assert summary["training"]["total_minutes"] >= 90
    assert summary["weight"]["change_kg"] == -1.5
    assert summary["nutrition"]["avg_calories"] == 2000
    assert summary["water"]["avg_ml_per_logged_day"] == 500

    isolated = client.get("/insights/summary", headers=other).json()
    assert isolated["training"]["total_sessions"] == 0 and isolated["weight"]["entries"] == 0


def test_nutrition_consumption_persists_and_meal_plan_generation_does_not_log():
    headers, _ = _account("nutri")
    other, _ = _account("nutri-other")
    assert client.post("/nutrition/", headers=headers, json={"calories": 500, "protein": 40}).status_code == 200
    assert len(client.get("/nutrition/", headers=headers).json()) == 1
    assert client.get("/nutrition/", headers=other).json() == []
    assert client.post("/nutrition/", json={"calories": 1}).status_code == 401
    generated = client.post("/nutrition-coach/meal-plans/generate", headers=headers, json={})
    assert generated.status_code != 401, generated.text
    assert len(client.get("/nutrition/", headers=headers).json()) == 1
    assert client.get("/insights/summary", headers=headers).json()["nutrition"]["days_logged_30"] == 1


def test_change_password():
    headers, email = _account("pw")
    bad = client.post("/account/change-password", headers=headers,
                      json={"current_password": "wrong-password", "new_password": "NewPassw0rd!!"})
    assert bad.status_code == 400
    short = client.post("/account/change-password", headers=headers,
                        json={"current_password": PASSWORD, "new_password": "short"})
    assert short.status_code == 422
    ok = client.post("/account/change-password", headers=headers,
                     json={"current_password": PASSWORD, "new_password": "NewPassw0rd!!"})
    assert ok.status_code == 200, ok.text
    assert client.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code != 200
    assert client.post("/auth/login", json={"email": email, "password": "NewPassw0rd!!"}).status_code == 200


def test_notification_preferences_persist_per_user():
    headers, _ = _account("notif")
    other, _ = _account("notif-other")
    first = client.get("/account/notifications", headers=headers).json()
    assert first["preferences"]["weekly_reports"] is False
    saved = client.put("/account/notifications", headers=headers, json={"weekly_reports": True}).json()
    assert saved["preferences"]["weekly_reports"] is True
    assert client.get("/account/notifications", headers=headers).json()["preferences"]["weekly_reports"] is True
    assert client.get("/account/notifications", headers=other).json()["preferences"]["weekly_reports"] is False
    if not os.getenv("SMTP_HOST"):
        assert saved["delivery_configured"] is False and saved["delivery_note"]
        assert client.post("/account/notifications/test", headers=headers).json()["sent"] is False


def test_export_contains_only_own_data_and_delete_requires_confirmation():
    headers, email = _account("export")
    other, other_email = _account("export-other")
    client.post("/hydration/", headers=headers, json={"amount_ml": 250, "date": _iso(0)})
    client.post("/hydration/", headers=other, json={"amount_ml": 999, "date": _iso(0)})
    client.post("/user-data/journal", headers=headers, json={"data": {"text": "mine"}})

    exported = client.get("/account/export", headers=headers).json()
    assert exported["account"]["email"] == email
    assert "hashed_password" not in str(exported)
    assert [r["amount_ml"] for r in exported["records"]["hydration_logs"]] == [250]
    assert len(exported["records"]["user_data_records"]) == 1

    def delete(body):
        return client.request("DELETE", "/account", headers=headers, json=body)

    assert delete({"confirm": "delete", "password": PASSWORD}).status_code == 400
    assert delete({"confirm": "DELETE", "password": "wrong-password"}).status_code == 400
    assert client.get("/account/export", headers=headers).status_code == 200
    assert delete({"confirm": "DELETE", "password": PASSWORD}).status_code == 200

    assert client.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code != 200
    assert client.post("/auth/login", json={"email": other_email, "password": PASSWORD}).status_code == 200
    remaining = client.get("/account/export", headers=other).json()["records"]
    assert [r["amount_ml"] for r in remaining["hydration_logs"]] == [999]

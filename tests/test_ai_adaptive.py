import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "ai_adaptive_test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)


def make_user(email):
    assert client.post("/auth/register", json={"name": email, "email": email, "password": "GoodPass123!"}).status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": "GoodPass123!"})
    return {"Authorization": "Bearer " + login.json()["access_token"]}


def test_adaptive_profile_requires_auth_and_is_per_user():
    assert client.get("/ai/profile").status_code == 401
    alice, bob = make_user("adapt-a@example.com"), make_user("adapt-b@example.com")
    assert client.get("/ai/profile", headers=alice).json() == {"profile": None}
    saved = client.put("/ai/profile", headers=alice, json={"difficulty": "hard", "preferredCategories": {"Strength": 4}})
    assert saved.status_code == 200, saved.text
    assert client.put("/ai/profile", headers=alice, json={"difficulty": "easy"}).status_code == 200
    assert client.get("/ai/profile", headers=alice).json()["profile"] == {"difficulty": "easy"}
    assert client.get("/ai/profile", headers=bob).json() == {"profile": None}
    assert all(r["feature"] != "adaptive-profile" for r in client.get("/ai/records", headers=alice).json())


def test_ai_uses_saved_profile_and_real_workout_history():
    user = make_user("adapt-c@example.com")
    before = client.post("/ai/weekly-plan", headers=user, json={}).json()
    assert before["result"]["adaptive_inputs"] == {}

    client.put("/ai/profile", headers=user, json={"difficulty": "hard", "preferredCategories": {"Strength": 5}})
    for _ in range(2):
        assert client.post("/workouts/save", headers=user, json={"mode": "manual", "duration_minutes": 30, "manual_name": "Lift"}).status_code == 200

    plan = client.post("/ai/weekly-plan", headers=user, json={}).json()
    used = plan["result"]["adaptive_inputs"]
    assert used["difficulty"] == "hard"
    assert used["preferred_category"] == "Strength"
    assert used["workouts_last_7_days"] == 2

    override = client.post("/ai/personalize", headers=user, json={"experience": "beginner", "fatigue": 0}).json()["result"]
    assert override["difficulty"] == "easy"
    coach = client.post("/ai/coach", headers=user, json={"user_data": {}, "message": "Plan?"}).json()
    assert "Estimated training difficulty: hard" in coach["coach_response"] and coach["adaptive_inputs"]["difficulty"] == "hard"


def test_invalid_stored_categories_are_not_adapted():
    user = make_user("adapt-invalid@example.com")
    client.put("/ai/profile", headers=user, json={"preferredCategories": {"undefined": 10, "null": 5, "Strength": 2}})
    coach = client.post("/ai/coach", headers=user, json={"user_data": {}, "message": "Plan?"}).json()
    assert coach["adaptive_inputs"]["preferred_category"] == "Strength"
    client.put("/ai/profile", headers=user, json={"preferredCategories": {"undefined": 10}})
    coach = client.post("/ai/coach", headers=user, json={"user_data": {}, "message": "Plan?"}).json()
    assert "preferred_category" not in coach["adaptive_inputs"]


def test_knee_pain_coaching_is_saved_and_returned():
    user = make_user("adapt-knee@example.com")
    response = client.post("/ai/coach", headers=user, json={
        "user_data": {"fatigue": 3, "sleep_hours": 7},
        "message": "right knee pain, give me a work out to work around this",
    })
    assert response.status_code == 200
    body = response.json()
    assert "knee pain" in body["coach_response"]
    assert "not clearance" in body["coach_response"]
    assert "recovered" not in body["coach_response"]
    records = client.get("/ai/records", headers=user).json()
    assert records[0]["id"] == body["record_id"]
    assert records[0]["result"]["coach_response"] == body["coach_response"]

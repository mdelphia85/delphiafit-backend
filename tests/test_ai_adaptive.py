import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "ai_adaptive_test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from app.auth.jwt_handler import create_access_token  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.ai_record import AIRecord  # noqa: E402

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


def test_ai_records_profiles_and_coaching_are_scoped_to_authenticated_account():
    alice = make_user("ai-scope-a@example.com")
    bob = make_user("ai-scope-b@example.com")
    bob_id = client.get("/auth/me", headers=bob).json()["id"]

    alice_coaching = client.post("/ai/coach", headers=alice, json={
        "user_data": {"user_id": bob_id, "fatigue": 4},
        "message": "Give me a workout.",
    })
    assert alice_coaching.status_code == 200, alice_coaching.text
    alice_profile = client.put("/ai/profile", headers=alice, json={"difficulty": "beginner"})
    assert alice_profile.status_code == 200
    assert alice_profile.json()["profile"] == {"difficulty": "beginner"}

    assert len(client.get("/ai/records", headers=alice).json()) == 1
    assert client.get("/ai/records", headers=bob).json() == []
    assert client.get("/ai/profile", headers=bob).json() == {"profile": None}
    assert client.put("/ai/profile", headers=bob, json={"difficulty": "advanced"}).status_code == 200
    assert client.get("/ai/profile", headers=alice).json()["profile"] == {"difficulty": "beginner"}
    assert len(client.get(f"/ai/records?user_id={bob_id}", headers=alice).json()) == 1
    assert client.get(f"/ai/profile?user_id={bob_id}", headers=alice).json()["profile"] == {"difficulty": "beginner"}


def test_ai_endpoints_reject_missing_invalid_and_expired_authentication():
    expired = {
        "Authorization": "Bearer " + create_access_token(
            {"sub": "1", "email": "expired@example.com"},
            expires_delta=timedelta(seconds=-1),
        )
    }
    invalid = {"Authorization": "Bearer not-a-valid-token"}
    coach_request = {"user_data": {}, "message": "Give me a workout."}

    for headers in ({}, invalid, expired):
        assert client.get("/ai/records", headers=headers).status_code == 401
        assert client.get("/ai/profile", headers=headers).status_code == 401
        assert client.put("/ai/profile", headers=headers, json={"difficulty": "easy"}).status_code == 401
        assert client.post("/ai/coach", headers=headers, json=coach_request).status_code == 401


def test_ai_coach_returns_generic_server_error_and_does_not_save_on_engine_failure(monkeypatch, caplog):
    user = make_user("ai-error@example.com")
    prompt = "private workout details"

    def fail_coaching(*_args, **_kwargs):
        raise RuntimeError(f"internal provider details: {prompt}")

    monkeypatch.setattr("app.routers.ai.ai.coach", fail_coaching)
    response = client.post("/ai/coach", headers=user, json={"user_data": {}, "message": prompt})

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to prepare coaching guidance."
    assert "internal provider details" not in response.text
    assert prompt not in caplog.text
    assert "RuntimeError" in caplog.text
    assert client.get("/ai/records", headers=user).json() == []


def test_ai_coach_idempotency_replays_result_and_allows_distinct_questions():
    user = make_user("ai-idempotent@example.com")
    headers = {**user, "Idempotency-Key": "logical-question-1"}
    payload = {"user_data": {"fatigue": 4}, "message": "Give me a workout."}

    first = client.post("/ai/coach", headers=headers, json=payload)
    retry = client.post("/ai/coach", headers=headers, json=payload)
    second_question = client.post(
        "/ai/coach",
        headers={**user, "Idempotency-Key": "logical-question-2"},
        json={"user_data": {"fatigue": 4}, "message": "How should I recover?"},
    )

    assert first.status_code == retry.status_code == second_question.status_code == 200
    assert retry.json() == first.json()
    assert second_question.json()["record_id"] != first.json()["record_id"]
    records = client.get("/ai/records", headers=user).json()
    assert len(records) == 2
    assert {record["input"]["message"] for record in records} == {
        "Give me a workout.",
        "How should I recover?",
    }


def test_ai_coach_rejects_reused_key_with_different_payload():
    user = make_user("ai-idempotency-conflict@example.com")
    headers = {**user, "Idempotency-Key": "reused-key"}
    first = client.post("/ai/coach", headers=headers, json={
        "user_data": {"fatigue": 4},
        "message": "Give me a workout.",
    })
    conflict = client.post("/ai/coach", headers=headers, json={
        "user_data": {"fatigue": 7},
        "message": "How should I recover?",
    })

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "Idempotency key was already used for a different request."
    assert len(client.get("/ai/records", headers=user).json()) == 1


def test_ai_coach_concurrent_conflicting_payloads_save_only_one_request(monkeypatch):
    user = make_user("ai-concurrent-idempotency-conflict@example.com")
    barrier = Barrier(2)

    def synchronized_coaching(*_args, **_kwargs):
        barrier.wait(timeout=10)
        return {"coach_response": "Concurrent guidance"}

    monkeypatch.setattr("app.routers.ai.ai.coach", synchronized_coaching)
    headers = {**user, "Idempotency-Key": "concurrent-conflicting-key"}
    payloads = [
        {"user_data": {}, "message": "Workout?"},
        {"user_data": {}, "message": "Recovery?"},
    ]

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(
            lambda payload: client.post("/ai/coach", headers=headers, json=payload),
            payloads,
        ))

    assert sorted(response.status_code for response in responses) == [200, 409]
    assert len(client.get("/ai/records", headers=user).json()) == 1


@pytest.mark.parametrize(
    ("path", "engine_method", "payload"),
    [
        ("/ai/personalize", "personalize", {}),
        ("/ai/smart-mode", "smart_mode_adjust", {}),
        ("/ai/weekly-plan", "generate_weekly_plan", {}),
        ("/ai/form-score", "score_form", {"keypoints": [], "reps": [], "exercise": "squat"}),
        ("/ai/velocity", "estimate_velocity", {"positions": [], "timestamps": [], "load": 0, "exercise": "squat"}),
    ],
)
def test_adjacent_ai_endpoints_hide_internal_errors_and_rollback(
    monkeypatch, caplog, path, engine_method, payload
):
    user = make_user(f"ai-safe-error-{engine_method}@example.com")
    marker = "INTERNAL-EXCEPTION-MARKER"

    def fail(*_args, **_kwargs):
        raise RuntimeError(marker)

    monkeypatch.setattr(f"app.routers.ai.ai.{engine_method}", fail)
    response = client.post(path, headers=user, json=payload)

    assert response.status_code == 500
    assert marker not in response.text
    assert marker not in caplog.text
    assert "RuntimeError" in caplog.text
    assert client.get("/ai/records", headers=user).json() == []


def test_ai_profile_save_rolls_back_and_hides_database_error(monkeypatch, caplog):
    user = make_user("ai-profile-save-error@example.com")
    marker = "DATABASE-EXCEPTION-MARKER"

    def fail_commit(*_args, **_kwargs):
        raise RuntimeError(marker)

    with monkeypatch.context() as patch:
        patch.setattr("sqlalchemy.orm.Session.commit", fail_commit)
        response = client.put("/ai/profile", headers=user, json={"difficulty": "beginner"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to save your coaching profile."
    assert marker not in response.text
    assert marker not in caplog.text
    assert "RuntimeError" in caplog.text
    assert client.get("/ai/profile", headers=user).json() == {"profile": None}


@pytest.mark.parametrize(
    ("method", "path", "payload", "headers", "expected_detail"),
    [
        ("get", "/ai/records", None, {}, "Unable to load your coaching history."),
        ("get", "/ai/profile", None, {}, "Unable to load your coaching profile."),
        ("put", "/ai/profile", {"difficulty": "beginner"}, {}, "Unable to save your coaching profile."),
        (
            "post",
            "/ai/coach",
            {"user_data": {}, "message": "Test prompt"},
            {"Idempotency-Key": "preflight-query-key"},
            "Unable to prepare coaching guidance.",
        ),
    ],
)
def test_ai_preflight_query_failures_hide_exception_markers_from_responses_and_logs(
    monkeypatch, caplog, method, path, payload, headers, expected_detail
):
    unique_id = uuid.uuid4().hex
    user = make_user(f"ai-query-error-{path.rsplit('/', 1)[-1]}-{unique_id}@example.com")
    marker = f"AI-QUERY-FAILURE-{path.strip('/').replace('/', '-')}-{unique_id}"
    headers = {
        key: f"{value}-{unique_id}" if key == "Idempotency-Key" else value
        for key, value in headers.items()
    }
    original_query = Session.query

    def fail_ai_record_query(session, *entities, **kwargs):
        if entities and entities[0] is AIRecord:
            raise RuntimeError(marker)
        return original_query(session, *entities, **kwargs)

    monkeypatch.setattr(Session, "query", fail_ai_record_query)
    request = getattr(client, method)
    response = request(path, headers={**user, **headers}, json=payload) if payload is not None else request(
        path, headers={**user, **headers}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == expected_detail
    assert marker not in response.text
    assert marker not in caplog.text
    assert "RuntimeError" in caplog.text
    monkeypatch.setattr(Session, "query", original_query)
    assert client.get("/ai/records", headers=user).json() == []


def test_ai_coach_concurrent_requests_with_same_key_save_one_record(monkeypatch):
    user = make_user("ai-concurrent-idempotency@example.com")
    barrier = Barrier(2)

    def synchronized_coaching(*_args, **_kwargs):
        barrier.wait(timeout=10)
        return {"coach_response": "Concurrent guidance"}

    monkeypatch.setattr("app.routers.ai.ai.coach", synchronized_coaching)
    headers = {**user, "Idempotency-Key": "concurrent-question"}
    payload = {"user_data": {}, "message": "Workout?"}

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(
            lambda _: client.post("/ai/coach", headers=headers, json=payload),
            range(2),
        ))

    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert len(client.get("/ai/records", headers=user).json()) == 1


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


def test_one_logged_workout_does_not_infer_beginner_training_experience():
    user = make_user("adapt-no-infer-" + uuid.uuid4().hex[:8] + "@example.com")
    logged = client.post(
        "/workouts/save",
        headers=user,
        json={"mode": "manual", "duration_minutes": 30, "manual_name": "Gym session"},
    )
    assert logged.status_code == 200, logged.text

    result = client.post(
        "/ai/coach", headers=user,
        json={"user_data": {}, "message": "best workouts to build muscle"},
    )
    assert result.status_code == 200, result.text
    data = result.json()
    assert "hypertrophy" in data["coach_response"].lower()
    assert "Beginner bodyweight session" not in data["coach_response"]
    assert data["adaptive_inputs"]["workouts_logged"] == 1

    generic = client.post(
        "/ai/coach", headers=user,
        json={"user_data": {}, "message": "What is a useful workout?"},
    )
    assert generic.status_code == 200
    assert "Beginner bodyweight session" not in generic.json()["coach_response"]

    history = client.get("/ai/records", headers=user).json()
    assert any(row["result"]["coach_response"] == data["coach_response"] for row in history)

def test_conversational_coach_answers_unrelated_questions_and_uses_same_user_history(monkeypatch):
    from types import SimpleNamespace
    from app.services import conversational_coach

    monkeypatch.setenv("OPENAI_API_KEY", "mock-key-not-real")
    monkeypatch.setenv("DELPHIAFIT_AI_MODEL", "gpt-6-luna")
    captured = []

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "mock-key-not-real"
            self.responses = self

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def create(self, **kwargs):
            captured.append(kwargs)
            return SimpleNamespace(output_text=f"Helpful response to: {kwargs['input'][-1]['content']}")

    monkeypatch.setattr(conversational_coach, "OpenAI", FakeClient)
    first = make_user("ai-chat-" + uuid.uuid4().hex[:10] + "@example.com")
    second = make_user("ai-other-" + uuid.uuid4().hex[:10] + "@example.com")

    for question in ("How do I build more muscle?", "What is the capital of France?", "And what continent is that in?"):
        res = client.post("/ai/coach", headers=first, json={"user_data": {"fatigue": 3}, "message": question})
        assert res.status_code == 200, res.text
        assert res.json()["mode"] == "conversational"
        assert question in res.json()["coach_response"]

    assert captured[-1]["store"] is False
    assert captured[-1]["model"] == "gpt-6-luna"
    assert len(captured[0]["input"]) == 2
    assert len(captured[1]["input"]) == 4
    assert len(captured[2]["input"]) == 6
    assert "What is the capital of France?" in str(captured[2]["input"])
    assert "OPENAI_API_KEY" not in str(captured)

    answer = client.post("/ai/coach", headers=second, json={"user_data": {}, "message": "What is a CPU?"})
    assert answer.status_code == 200
    assert len(captured[-1]["input"]) == 2
    assert "capital of France" not in str(captured[-1]["input"])
    assert len(client.get("/ai/records", headers=first).json()) == 3
    assert len(client.get("/ai/records", headers=second).json()) == 1


def test_model_error_is_not_saved_or_exposed(monkeypatch):
    from app.services import conversational_coach

    monkeypatch.setenv("OPENAI_API_KEY", "mock-key-not-real")

    class BrokenClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        @property
        def responses(self):
            return self

        def create(self, **kwargs):
            raise RuntimeError("PRIVATE_PROVIDERTOKEN must never appear")

    monkeypatch.setattr(conversational_coach, "OpenAI", BrokenClient)
    account = make_user("ai-provider-error-" + uuid.uuid4().hex[:8] + "@example.com")
    response = client.post("/ai/coach", headers=account, json={"user_data": {}, "message": "Hello?"})
    assert response.status_code == 500
    assert "PRIVATE_PROVIDERTOKEN" not in response.text
    assert client.get("/ai/records", headers=account).json() == []


def test_empty_question_is_rejected_and_limited_mode_is_honestly_labeled(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    account = make_user("ai-limited-" + uuid.uuid4().hex[:10] + "@example.com")
    empty = client.post("/ai/coach", headers=account, json={"user_data": {}, "message": " "})
    assert empty.status_code == 422
    response = client.post("/ai/coach", headers=account, json={"user_data": {}, "message": "Can I build muscle?"})
    assert response.status_code == 200
    assert response.json()["mode"] == "limited"
    assert "muscle" in response.json()["coach_response"].lower()

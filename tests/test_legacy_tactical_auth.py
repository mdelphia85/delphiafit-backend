import os
import tempfile
import uuid

_db_file = os.path.join(tempfile.mkdtemp(), "legacy_tactical_auth.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402

from app.auth.jwt_handler import create_access_token, decode_access_token  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.coach import Coach  # noqa: E402

run_migrations()
client = TestClient(app)


def register_user(label):
    email = f"{label}-{uuid.uuid4().hex}@example.com"
    response = client.post("/auth/register", json={"name": label, "email": email, "password": "Passw0rd!x"})
    assert response.status_code == 200, response.text
    login = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return int(decode_access_token(token)["sub"]), {"Authorization": "Bearer " + token}


def create_coach(label):
    email = f"{label}-{uuid.uuid4().hex}@example.com"
    db = SessionLocal()
    try:
        coach = Coach(email=email, name=label, role="coach", is_active=True)
        db.add(coach)
        db.commit()
        db.refresh(coach)
        token = create_access_token({"sub": str(coach.id), "email": email, "actor_type": "coach", "role": coach.role})
        return coach.id, {"Authorization": "Bearer " + token}
    finally:
        db.close()


def test_scenario_runs_and_authoring_are_user_scoped():
    assert client.get("/scenario/list").status_code == 401
    assert client.post("/scenario/create", json={"name": "unauth", "category": "SAR"}).status_code == 401
    owner_id, owner = register_user("scenario-owner")
    other_id, other = register_user("scenario-other")

    scenario = client.post("/scenario/create", headers=owner, json={"name": "Private exercise", "category": "SAR"})
    assert scenario.status_code == 200, scenario.text
    scenario_id = scenario.json()["id"]
    assert "owner_user_id" not in scenario.json()
    assert scenario_id in [row["id"] for row in client.get("/scenario/list", headers=owner).json()]
    assert scenario_id not in [row["id"] for row in client.get("/scenario/list", headers=other).json()]
    assert client.get(f"/scenario/node/{scenario_id}", headers=other).status_code == 404
    assert client.post("/scenario/node", headers=other, json={"scenario_id": scenario_id, "title": "Nope", "node_type": "event"}).status_code == 404

    node = client.post("/scenario/node", headers=owner, json={"scenario_id": scenario_id, "title": "Arrival", "node_type": "event"})
    assert node.status_code == 200, node.text
    run = client.post("/scenario/run/start", headers=owner, json={"scenario_id": scenario_id, "user_id": other_id})
    assert run.status_code == 200 and run.json()["user_id"] == owner_id
    run_id = run.json()["id"]
    assert client.get(f"/scenario/step/{run_id}", headers=other).status_code == 404
    assert client.post("/scenario/run/{}/complete".format(run_id), headers=other, json={"score": 99}).status_code == 404
    assert client.post("/scenario/step", headers=other, json={"run_id": run_id, "node_id": node.json()["id"], "choice_text": "spoof"}).status_code == 404
    saved = client.post("/scenario/step", headers=owner, json={"run_id": run_id, "node_id": node.json()["id"], "choice_text": "Proceed"})
    assert saved.status_code == 200, saved.text
    assert len(client.get(f"/scenario/step/{run_id}", headers=owner).json()) == 1


def test_unit_apis_enforce_owner_and_member_roles():
    owner_id, owner = register_user("unit-owner")
    member_id, member = register_user("unit-member")
    outsider_id, outsider = register_user("unit-outsider")
    assert client.get("/unit/list").status_code == 401
    created = client.post("/unit/create", headers=owner, json={"name": "Rescue 1", "unit_type": "sar"})
    assert created.status_code == 200, created.text
    unit_id = created.json()["id"]
    assert "owner_user_id" not in created.json()
    assert client.get(f"/unit/{unit_id}", headers=outsider).status_code == 404
    added = client.post("/unit/member", headers=owner, json={"unit_id": unit_id, "user_id": member_id, "role": "medic"})
    assert added.status_code == 200, added.text
    assert client.get(f"/unit/{unit_id}", headers=member).status_code == 200
    assert client.get(f"/unit/member/{unit_id}", headers=member).status_code == 200
    assert client.post("/unit/capability", headers=member, json={"unit_id": unit_id, "capability": "rope", "score": 80}).status_code == 404
    assert client.post(f"/unit/{unit_id}/readiness", headers=member).status_code == 404
    assert client.post("/unit/member", headers=outsider, json={"unit_id": unit_id, "user_id": outsider_id, "role": "owner"}).status_code == 404
    assert [row["id"] for row in client.get("/unit/list", headers=member).json()] == [unit_id]


def test_instructor_routes_require_coach_role_and_scope_instructor_records():
    user_id, user = register_user("instructor-user")
    coach_id, coach = create_coach("instructor-coach")
    other_coach_id, other_coach = create_coach("other-instructor-coach")
    assert client.get("/instructor/list/fire").status_code == 401
    assert client.get("/instructor/list/fire", headers=user).status_code == 403
    instructor = client.post("/instructor/create", headers=coach, json={"user_id": user_id, "agency": "fire", "role": "lead instructor"})
    assert instructor.status_code == 200, instructor.text
    instructor_id = instructor.json()["id"]
    assert instructor.json()["user_id"] == coach_id
    assert client.get(f"/instructor/assign/{instructor_id}", headers=other_coach).status_code == 404
    assignment = client.post("/instructor/assign", headers=coach, json={"instructor_id": instructor_id, "target_type": "academy", "target_id": 9})
    assert assignment.status_code == 200, assignment.text
    assert len(client.get(f"/instructor/assign/{instructor_id}", headers=coach).json()) == 1
    feedback = client.post("/instructor/feedback", headers=coach, json={"instructor_id": instructor_id, "user_id": user_id, "category": "fitness", "feedback": "Good progress"})
    assert feedback.status_code == 200, feedback.text
    assert len(client.get(f"/instructor/feedback/{user_id}", headers=coach).json()) == 1
    assert client.get(f"/instructor/feedback/{user_id}", headers=other_coach).json() == []


def test_certification_catalog_and_user_records_are_scoped():
    user_id, user = register_user("cert-user")
    other_id, other = register_user("cert-other")
    coach_id, coach = create_coach("cert-coach")
    assert client.get("/certification/list").status_code == 200
    assert client.post("/certification/create", headers=user, json={"name": "Unauthorized", "category": "fire"}).status_code == 403
    cert = client.post("/certification/create", headers=coach, json={"name": "Fire I", "category": "fire"})
    assert cert.status_code == 200, cert.text
    cert_id = cert.json()["id"]
    requirement = client.post("/certification/requirement", headers=coach, json={"certification_id": cert_id, "requirement_type": "physical", "target_id": 1})
    assert requirement.status_code == 200, requirement.text
    issued = client.post("/certification/record", headers=coach, json={"user_id": user_id, "certification_id": cert_id, "score": 91, "passed": True})
    assert issued.status_code == 200, issued.text
    assert len(client.get(f"/certification/record/{user_id}", headers=user).json()) == 1
    assert client.get(f"/certification/record/{user_id}", headers=other).status_code == 404
    assert client.post("/certification/record", json={"user_id": user_id, "certification_id": cert_id}).status_code == 401


def test_academy_catalog_is_public_but_progress_and_grading_are_authorized():
    user_id, user = register_user("academy-user")
    other_id, other = register_user("academy-other")
    _, coach = create_coach("academy-coach")
    assert client.get("/academy/program/list").status_code == 200
    assert client.post("/academy/program", headers=user, json={"name": "Unauthorized", "category": "fire"}).status_code == 403
    program = client.post("/academy/program", headers=coach, json={"name": "Fire Academy", "category": "fire"})
    assert program.status_code == 200, program.text
    program_id = program.json()["id"]
    module = client.post("/academy/module", headers=coach, json={"program_id": program_id, "name": "Fitness", "module_type": "physical"})
    assert module.status_code == 200, module.text
    enrollment = client.post("/academy/cadet/enroll", headers=user, json={"user_id": other_id, "program_id": program_id})
    assert enrollment.status_code == 200 and enrollment.json()["user_id"] == user_id
    cadet_id = enrollment.json()["id"]
    assert client.get(f"/academy/cadet/{program_id}", headers=user).status_code == 403
    assert client.get(f"/academy/evaluation/{cadet_id}", headers=other).status_code == 404
    assert client.post("/academy/evaluation", headers=user, json={"cadet_id": cadet_id, "module_id": module.json()["id"], "passed": True}).status_code == 403
    grade = client.post("/academy/evaluation", headers=coach, json={"cadet_id": cadet_id, "module_id": module.json()["id"], "passed": True})
    assert grade.status_code == 200, grade.text
    assert len(client.get(f"/academy/evaluation/{cadet_id}", headers=user).json()) == 1


def test_remaining_unprotected_debug_and_prep_endpoints_reject_anonymous_users():
    assert client.get("/test").status_code == 404  # debug router is not mounted in app.main
    paths = ["/sof/pipeline/list", "/swat/pipeline/list"]
    for path in paths:
        assert client.get(path).status_code == 401, path

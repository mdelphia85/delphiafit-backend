import os
import tempfile

import pytest

_db_file = os.path.join(tempfile.mkdtemp(), "tactical_progress_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402

from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)


def register_and_login(email):
    client.post("/auth/register", json={"name": email, "email": email, "password": "Passw0rd!x"})
    response = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_progress_requires_authentication_and_isolated_between_users():
    assert client.get("/tactical/progress/k9-operations").status_code == 401
    first = register_and_login("progress-first@example.com")
    second = register_and_login("progress-second@example.com")
    original = {"drills": [{"key": "scent", "completed": True}]}

    saved = client.put("/tactical/progress/k9-operations", headers=first, json={"data": original})
    assert saved.status_code == 200, saved.text
    assert client.get("/tactical/progress/k9-operations", headers=first).json()["data"] == original
    assert client.get("/tactical/progress/k9-operations", headers=second).json()["data"] is None

    settings = {"display": "compact"}
    assert client.put("/tactical/progress/k9-operations", headers=first, json={"item_key": "settings", "data": settings}).status_code == 200
    assert client.get("/tactical/progress/k9-operations?item_key=settings", headers=first).json()["data"] == settings
    assert client.get("/tactical/progress/k9-operations?item_key=settings", headers=second).json()["data"] is None

    changed = {"drills": [{"key": "scent", "completed": False}]}
    updated = client.put("/tactical/progress/k9-operations", headers=first, json={"data": changed})
    assert updated.status_code == 200
    assert client.get("/tactical/progress/k9-operations", headers=first).json()["data"] == changed
    assert client.get("/tactical/progress/k9-operations", headers=second).json()["data"] is None


def test_progress_rejects_invalid_module_keys():
    headers = register_and_login("progress-invalid@example.com")
    response = client.get("/tactical/progress/Not%20Valid", headers=headers)
    assert response.status_code == 422


def test_tactical_drill_completion_and_ownership():
    owner = register_and_login("drill-owner@example.com")
    other = register_and_login("drill-other@example.com")
    created = client.post("/tactical/firefighters/log", headers=owner, json={
        "category": "SCBA Endurance", "name": "Account-owned drill", "duration": "30"
    })
    assert created.status_code == 200, created.text
    drill_id = created.json()["id"]
    assert created.json()["completed"] is False

    completed = client.put(f"/tactical/firefighters/log/{drill_id}", headers=owner, json={"completed": True})
    assert completed.status_code == 200 and completed.json()["completed"] is True
    assert client.get("/tactical/firefighters/logs", headers=owner).json()[0]["completed"] is True
    assert client.get("/tactical/firefighters/logs", headers=other).json() == []
    assert client.put(f"/tactical/firefighters/log/{drill_id}", headers=other, json={"completed": False}).status_code == 404
    assert client.delete(f"/tactical/firefighters/log/{drill_id}", headers=other).status_code == 404


def test_mission_replay_requires_auth_and_scopes_all_replay_data():
    assert client.get("/mission_replay/list").status_code == 401
    assert client.post("/mission_replay/start", json={"mission_type": "training", "mission_id": 1}).status_code == 401
    owner = register_and_login("replay-owner@example.com")
    other = register_and_login("replay-other@example.com")

    created = client.post("/mission_replay/start", headers=owner, json={
        "mission_type": "training", "mission_id": 11, "user_id": 999999
    })
    assert created.status_code == 200, created.text
    replay_id = created.json()["id"]
    assert created.json()["user_id"] != 999999
    assert [row["id"] for row in client.get("/mission_replay/list", headers=owner).json()] == [replay_id]
    assert client.get("/mission_replay/list", headers=other).json() == []
    assert client.get(f"/mission_replay/{replay_id}", headers=other).status_code == 404
    assert client.post(f"/mission_replay/{replay_id}/complete", headers=other, json={"score": 80}).status_code == 404
    assert client.post("/mission_replay/step", headers=other, json={"replay_id": replay_id, "action_type": "move"}).status_code == 404
    assert client.get(f"/mission_replay/step/{replay_id}", headers=other).status_code == 404
    assert client.post("/mission_replay/annotation", headers=other, json={"replay_id": replay_id, "category": "review", "note": "private"}).status_code == 404

    step = client.post("/mission_replay/step", headers=owner, json={"replay_id": replay_id, "action_type": "check-in", "description": "Arrived"})
    assert step.status_code == 200, step.text
    assert len(client.get(f"/mission_replay/step/{replay_id}", headers=owner).json()) == 1
    annotation = client.post("/mission_replay/annotation", headers=owner, json={"replay_id": replay_id, "category": "review", "note": "Personal note", "instructor_id": 999999})
    assert annotation.status_code == 200 and annotation.json()["instructor_id"] != 999999
    completed = client.post(f"/mission_replay/{replay_id}/complete", headers=owner, json={"score": 87})
    assert completed.status_code == 200 and completed.json()["completed"] is True
    assert client.get("/mission_replay/list", headers=owner).json()[0]["score"] == 87


def test_tactical_operation_routes_require_authentication():
    paths = [
        "/k9/list", "/sar/operation/list", "/disaster/operation/list",
        "/maritime/operation/list", "/aviation/operation/list", "/hazmat/operation/list",
        "/wildland/operation/list", "/loadout/list", "/sof/pipeline/list", "/swat/pipeline/list",
    ]
    for path in paths:
        assert client.get(path).status_code == 401, path
    for path, body in [
        ("/k9/create", {"name": "unauth"}),
        ("/sar/operation", {"operation_name": "unauth", "operation_type": "urban"}),
        ("/disaster/operation", {"name": "unauth", "type": "flood"}),
        ("/maritime/operation", {"name": "unauth", "operation_type": "rescue"}),
        ("/aviation/operation", {"name": "unauth", "operation_type": "SAR"}),
        ("/hazmat/operation", {"name": "unauth", "incident_type": "chemical"}),
        ("/wildland/operation", {"name": "unauth", "fire_type": "forest"}),
        ("/loadout/create", {"name": "unauth", "category": "general"}),
        ("/sof/pipeline", {"name": "unauth", "branch": "army"}),
        ("/swat/pipeline", {"name": "unauth", "agency": "police"}),
    ]:
        assert client.post(path, json=body).status_code == 401, path


def test_k9_units_deployments_are_private_to_the_owner():
    owner = register_and_login("k9-owner@example.com")
    other = register_and_login("k9-other@example.com")
    created = client.post("/k9/create", headers=owner, json={"name": "Rex", "specialty": "tracking"})
    assert created.status_code == 200, created.text
    k9_id = created.json()["id"]
    assert client.get("/k9/list", headers=owner).json()[0]["id"] == k9_id
    assert client.get("/k9/list", headers=other).json() == []
    assert client.post("/k9/deploy", headers=other, json={"k9_id": k9_id, "handler_id": 9999, "mission_type": "SAR"}).status_code == 404
    deployed = client.post("/k9/deploy", headers=owner, json={"k9_id": k9_id, "handler_id": 9999, "mission_type": "SAR", "success": True})
    assert deployed.status_code == 200 and deployed.json()["handler_id"] != 9999
    assert len(client.get(f"/k9/history/{k9_id}", headers=owner).json()) == 1
    assert client.get(f"/k9/history/{k9_id}", headers=other).status_code == 404


def test_incident_operations_and_child_activity_are_owner_scoped():
    owner = register_and_login("incident-owner@example.com")
    other = register_and_login("incident-other@example.com")
    cases = [
        ("sar", "/sar/operation", {"operation_name": "SAR test", "operation_type": "urban"}, "/sar/team", {"team_name": "Sweep team"}, "/sar/operation/{}"),
        ("disaster", "/disaster/operation", {"name": "Flood test", "type": "flood"}, "/disaster/resource", {"resource_type": "Rescue team", "quantity": 1}, "/disaster/operation/{}"),
        ("maritime", "/maritime/operation", {"name": "Sea test", "operation_type": "rescue"}, "/maritime/incident", {"incident_type": "Readiness log"}, "/maritime/operation/{}"),
        ("aviation", "/aviation/operation", {"name": "Flight test", "operation_type": "SAR"}, "/aviation/event", {"event_type": "Readiness log"}, "/aviation/operation/{}"),
        ("hazmat", "/hazmat/operation", {"name": "Hazmat test", "incident_type": "chemical"}, "/hazmat/exposure", {"exposure_type": "Readiness log"}, "/hazmat/operation/{}"),
        ("wildland", "/wildland/operation", {"name": "Fire test", "fire_type": "forest"}, "/wildland/event", {"event_type": "Readiness log"}, "/wildland/operation/{}"),
    ]
    for module, create_path, create_body, activity_path, activity_body, detail_path in cases:
        created = client.post(create_path, headers=owner, json={**create_body, "commander_id": 999999, "incident_commander_id": 999999, "mission_commander_id": 999999})
        assert created.status_code == 200, (module, created.text)
        operation_id = created.json()["id"]
        assert [row["id"] for row in client.get(f"/{module}/operation/list", headers=owner).json()] == [operation_id]
        assert client.get(f"/{module}/operation/list", headers=other).json() == []
        assert client.get(detail_path.format(operation_id), headers=other).status_code == 404
        assert client.post(activity_path, headers=other, json={**activity_body, "operation_id": operation_id}).status_code == 404
        assert client.post(activity_path, headers=owner, json={**activity_body, "operation_id": operation_id}).status_code == 200


def test_sar_team_history_requires_auth_and_checks_operation_owner():
    assert client.get("/sar/team/999999").status_code == 401
    owner = register_and_login("sar-team-owner@example.com")
    other = register_and_login("sar-team-other@example.com")
    operation = client.post("/sar/operation", headers=owner, json={"operation_name": "River search", "operation_type": "water"})
    assert operation.status_code == 200, operation.text
    operation_id = operation.json()["id"]
    assert client.get(f"/sar/team/{operation_id}", headers=other).status_code == 404
    assert client.get(f"/sar/team/{operation_id}", headers=owner).json() == []
    added = client.post("/sar/team", headers=owner, json={"operation_id": operation_id, "team_name": "North bank"})
    assert added.status_code == 200, added.text
    assert [row["team_name"] for row in client.get(f"/sar/team/{operation_id}", headers=owner).json()] == ["North bank"]
    assert client.get(f"/sar/team/{operation_id}", headers=other).status_code == 404


def test_loadouts_are_private_and_item_updates_are_scoped():
    owner = register_and_login("loadout-owner@example.com")
    other = register_and_login("loadout-other@example.com")
    created = client.post("/loadout/create", headers=owner, json={"user_id": 999999, "name": "Ruck", "category": "military"})
    assert created.status_code == 200, created.text
    loadout_id = created.json()["id"]
    assert created.json()["user_id"] != 999999
    assert client.get("/loadout/list", headers=owner).json()[0]["id"] == loadout_id
    assert client.get("/loadout/list", headers=other).json() == []
    assert client.get(f"/loadout/{loadout_id}", headers=other).status_code == 404
    assert client.post("/loadout/item", headers=other, json={"loadout_id": loadout_id, "name": "Boots", "weight": 2}).status_code == 404
    item = client.post("/loadout/item", headers=owner, json={"loadout_id": loadout_id, "name": "Boots", "weight": 2, "quantity": 2})
    assert item.status_code == 200, item.text
    assert len(client.get(f"/loadout/item/{loadout_id}", headers=owner).json()) == 1
    assert client.get(f"/loadout/item/{loadout_id}", headers=other).status_code == 404


def test_sof_and_swat_candidate_evaluations_are_private():
    owner = register_and_login("prep-owner@example.com")
    other = register_and_login("prep-other@example.com")

    sof_pipeline = client.post("/sof/pipeline", headers=owner, json={"name": "Test SF", "branch": "army"}).json()
    assert sof_pipeline["owner_user_id"] != None
    sof_event = client.post("/sof/event", headers=owner, json={"pipeline_id": sof_pipeline["id"], "name": "Run", "event_type": "physical"})
    assert sof_event.status_code == 200
    candidate = client.post("/sof/candidate", headers=owner, json={"user_id": 999999, "pipeline_id": sof_pipeline["id"]})
    assert candidate.status_code == 200 and candidate.json()["user_id"] != 999999
    candidate_id = candidate.json()["id"]
    assert client.get(f"/sof/candidate/{sof_pipeline['id']}", headers=other).status_code == 404
    assert client.post("/sof/evaluation", headers=other, json={"candidate_id": candidate_id, "event_id": sof_event.json()["id"], "passed": True}).status_code == 404
    assert client.post("/sof/evaluation", headers=owner, json={"candidate_id": candidate_id, "event_id": sof_event.json()["id"], "passed": True}).status_code == 200
    assert client.get(f"/sof/evaluation/{candidate_id}", headers=other).status_code == 404

    swat_pipeline = client.post("/swat/pipeline", headers=owner, json={"name": "Test SWAT", "agency": "police"}).json()
    swat_drill = client.post("/swat/drill", headers=owner, json={"pipeline_id": swat_pipeline["id"], "name": "Run", "drill_type": "physical"})
    assert swat_drill.status_code == 200
    operator = client.post("/swat/operator", headers=owner, json={"user_id": 999999, "pipeline_id": swat_pipeline["id"]})
    assert operator.status_code == 200 and operator.json()["user_id"] != 999999
    operator_id = operator.json()["id"]
    assert client.get(f"/swat/operator/{swat_pipeline['id']}", headers=other).status_code == 404
    assert client.post("/swat/evaluation", headers=other, json={"operator_id": operator_id, "drill_id": swat_drill.json()["id"]}).status_code == 404
    assert client.post("/swat/evaluation", headers=owner, json={"operator_id": operator_id, "drill_id": swat_drill.json()["id"], "passed": True}).status_code == 200
    assert client.get(f"/swat/evaluation/{operator_id}", headers=other).status_code == 404

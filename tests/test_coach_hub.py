import os
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

_db_file = os.path.join(tempfile.mkdtemp(), "coach_hub_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

from app.auth.hashing import hash_password  # noqa: E402
from app.database.connection import SessionLocal, engine  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.coach import Coach  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.weight import WeightLog  # noqa: E402
from app.models.workout_log import WorkoutLog  # noqa: E402

run_migrations()
http = TestClient(app)
PASSWORD = "Passw0rd!xyz"


def uniq(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def bearer(token):
    return {"Authorization": "Bearer " + token}


def make_coach(email=None):
    email = email or uniq("coach")
    db = SessionLocal()
    try:
        coach = Coach(email=email, name="Coach " + email[:5], role="coach", is_active=True, hashed_password=hash_password(PASSWORD))
        db.add(coach)
        db.commit()
        db.refresh(coach)
        coach_id = coach.id
    finally:
        db.close()
    r = http.post("/coach/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"id": coach_id, "email": email, "headers": bearer(r.json()["access_token"])}


def make_team(coach, name="Varsity"):
    r = http.post("/staff/teams", headers=coach["headers"], json={"name": name, "sport": "soccer"})
    assert r.status_code == 201, r.text
    return r.json()


def make_client(coach, team_id=None, name="Client One"):
    """Invite + accept through the real endpoints; returns client dict with user headers."""
    email = uniq("client")
    body = {"email": email}
    if team_id:
        body["team_id"] = team_id
    r = http.post("/staff/clients/invite", headers=coach["headers"], json=body)
    assert r.status_code == 200, r.text
    token = r.json()["invite_token"]
    r = http.post("/staff/invitations/accept", json={"invitation_token": token, "name": name, "password": PASSWORD})
    assert r.status_code == 200, r.text
    r = http.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"id": r.json() and http_client_id(coach, email), "email": email, "headers": bearer(r.json()["access_token"])}


def http_client_id(coach, email):
    clients = http.get("/staff/clients", headers=coach["headers"]).json()["clients"]
    return next(c["id"] for c in clients if c["email"] == email)


def user_id(email):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first().id
    finally:
        db.close()


# ---------- authentication / authorization ----------

COACH_ENDPOINTS = [
    ("get", "/staff/clients"),
    ("get", "/staff/plans"),
    ("get", "/staff/teams"),
    ("get", "/staff/drills"),
    ("get", "/staff/invitations"),
    ("get", "/staff/messages/threads"),
    ("get", "/coach/team"),
    ("get", "/team/1"),
    ("post", "/invite/create"),
]


@pytest.mark.parametrize("method,path", COACH_ENDPOINTS)
def test_unauthenticated_gets_401(method, path):
    r = getattr(http, method)(path, **({"json": {"email": "a@b.co"}} if method == "post" else {}))
    assert r.status_code == 401


@pytest.mark.parametrize("method,path", COACH_ENDPOINTS)
def test_user_token_gets_403_on_coach_routes(method, path):
    coach = make_coach()
    client = make_client(coach)
    r = getattr(http, method)(path, headers=client["headers"], **({"json": {"email": "a@b.co"}} if method == "post" else {}))
    assert r.status_code == 403


def test_coach_token_cannot_act_as_user():
    coach = make_coach()
    r = http.get("/weight/", headers=coach["headers"])
    assert r.status_code == 403


def test_client_endpoints_reject_coach_and_anonymous():
    coach = make_coach()
    assert http.get("/staff/my/messages").status_code == 401
    assert http.get("/staff/my/messages", headers=coach["headers"]).status_code == 403
    assert http.get("/staff/my/plans", headers=coach["headers"]).status_code == 403


def test_user_without_coach_gets_404_on_my_messages():
    email = uniq("solo")
    http.post("/auth/register", json={"name": "Solo", "email": email, "password": PASSWORD})
    token = http.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    assert http.get("/staff/my/messages", headers=bearer(token)).status_code == 404


# ---------- login / invite / password reset ----------

def test_coach_login_rejects_bad_password():
    coach = make_coach()
    assert http.post("/coach/login", json={"email": coach["email"], "password": "wrong-password"}).status_code == 401


def test_password_reset_flow(monkeypatch):
    monkeypatch.setenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "true")
    coach = make_coach()
    r = http.post("/coach/password/forgot", json={"email": coach["email"]})
    token = r.json()["debug_token"]
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": "bad", "new_password": "NewPassw0rd!!"}).status_code == 400
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "short"}).status_code == 400
    r = http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "NewPassw0rd!!"})
    assert r.status_code == 200
    assert http.post("/coach/login", json={"email": coach["email"], "password": PASSWORD}).status_code == 401
    assert http.post("/coach/login", json={"email": coach["email"], "password": "NewPassw0rd!!"}).status_code == 200
    # token is single use
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "Another0ne!!!"}).status_code == 400


def test_coach_invitation_flow_gives_team_access():
    owner = make_coach()
    team = make_team(owner)
    client = make_client(owner, team["id"])
    assistant_email = uniq("assistant")
    r = http.post(f"/staff/teams/{team['id']}/coach-invitations", headers=owner["headers"], json={"email": assistant_email, "role": "assistant_coach"})
    assert r.status_code == 201, r.text
    token = r.json()["invite_token"]

    lookup = http.get("/staff/invitations/lookup", params={"token": token})
    assert lookup.json() == {"email": assistant_email, "role": "coach"}
    # a coach invite cannot be accepted on the client endpoint
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "Asst", "password": PASSWORD}).status_code == 400

    r = http.post("/coach/invitations/accept", json={"invitation_token": token, "name": "Assistant", "password": PASSWORD})
    assert r.status_code == 200, r.text
    assert http.get("/staff/invitations/lookup", params={"token": token}).status_code == 404  # single use

    login = http.post("/coach/login", json={"email": assistant_email, "password": PASSWORD})
    assert login.status_code == 200 and login.json()["team_id"] == team["id"]
    headers = bearer(login.json()["access_token"])
    clients = http.get("/staff/clients", headers=headers).json()["clients"]
    assert [c["id"] for c in clients] == [client["id"]]
    # assistants are not team owners
    assert http.put(f"/staff/teams/{team['id']}", headers=headers, json={"name": "Renamed"}).status_code == 403
    assert http.post(f"/staff/teams/{team['id']}/coach-invitations", headers=headers, json={"email": uniq("x")}).status_code == 403


def test_client_cannot_be_invited_as_coach_and_roles_validated():
    owner = make_coach()
    team = make_team(owner)
    r = http.post(f"/staff/teams/{team['id']}/coach-invitations", headers=owner["headers"], json={"email": uniq("c"), "role": "client"})
    assert r.status_code == 400


def test_client_invitation_flow_and_lookup():
    coach = make_coach()
    email = uniq("newclient")
    r = http.post("/staff/clients/invite", headers=coach["headers"], json={"email": email})
    assert r.status_code == 200
    token = r.json()["invite_token"]
    assert http.get("/staff/invitations/lookup", params={"token": token}).json()["role"] == "client"
    pending = http.get("/staff/invitations", headers=coach["headers"]).json()["invitations"]
    assert [(i["email"], i["accepted"]) for i in pending] == [(email, False)]
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "New Client", "password": "short"}).status_code == 400
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "New Client", "password": PASSWORD}).status_code == 200
    clients = http.get("/staff/clients", headers=coach["headers"]).json()["clients"]
    assert [c["email"] for c in clients] == [email]
    assert http.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    # duplicate invite for an active client is rejected
    assert http.post("/staff/clients/invite", headers=coach["headers"], json={"email": email}).status_code == 400


def test_pending_invitation_can_be_revoked_only_by_owner():
    a, b = make_coach(), make_coach()
    r = http.post("/staff/clients/invite", headers=a["headers"], json={"email": uniq("p")})
    invite_id = r.json()["invite_id"]
    assert http.delete(f"/staff/invitations/{invite_id}", headers=b["headers"]).status_code == 403
    assert http.delete(f"/staff/invitations/{invite_id}", headers=a["headers"]).status_code == 200
    assert http.get("/staff/invitations", headers=a["headers"]).json()["invitations"] == []
    assert http.post("/invite/revoke", headers=b["headers"], json={"invite_id": invite_id}).status_code == 404


def test_legacy_invite_router_is_authenticated_and_owner_scoped():
    owner, other = make_coach(), make_coach()
    team = make_team(owner)
    body = {"team_id": team["id"], "email": uniq("legacy"), "role": "assistant_coach"}
    assert http.post("/invite/create", headers=other["headers"], json=body).status_code == 403
    assert http.post("/invite/create", headers=owner["headers"], json={**body, "coach_id": other["id"]}).status_code == 403
    assert http.post("/invite/create", headers=owner["headers"], json=body).status_code == 200


# ---------- client management ----------

def test_client_list_progress_and_removal_are_distinct_and_isolated():
    a, b = make_coach(), make_coach()
    client = make_client(a, name="Alice Athlete")
    cid = client["id"]

    assert [c["id"] for c in http.get("/staff/clients", headers=a["headers"]).json()["clients"]] == [cid]
    assert http.get("/staff/clients", headers=b["headers"]).json()["clients"] == []

    # progress is read-only and does not remove the client
    assert http.get(f"/staff/clients/{cid}/progress", headers=a["headers"]).status_code == 200
    assert len(http.get("/staff/clients", headers=a["headers"]).json()["clients"]) == 1

    # other coach is blocked from every client-scoped route
    assert http.get(f"/staff/clients/{cid}/progress", headers=b["headers"]).status_code == 403
    assert http.delete(f"/staff/clients/{cid}", headers=b["headers"]).status_code == 403
    assert http.get(f"/staff/messages/{cid}", headers=b["headers"]).status_code == 403
    assert http.post(f"/staff/messages/{cid}", headers=b["headers"], json={"body": "hi"}).status_code == 403
    assert http.get(f"/staff/clients/{cid}/plans", headers=b["headers"]).status_code == 403
    assert http.post(f"/staff/clients/{cid}/team", headers=b["headers"], json={"team_id": None}).status_code == 403
    assert http.get("/staff/clients/999999/progress", headers=a["headers"]).status_code == 404

    assert http.delete(f"/staff/clients/{cid}", headers=a["headers"]).status_code == 200
    assert http.get("/staff/clients", headers=a["headers"]).json()["clients"] == []
    assert http.get(f"/staff/clients/{cid}/progress", headers=a["headers"]).status_code == 404


def test_client_progress_returns_real_data():
    coach = make_coach()
    client = make_client(coach)
    uid = user_id(client["email"])
    now = datetime.utcnow()
    db = SessionLocal()
    try:
        db.add_all([
            WeightLog(user_id=uid, weight_kg=90.0, date=now - timedelta(days=20)),
            WeightLog(user_id=uid, weight_kg=87.5, date=now - timedelta(days=1)),
            WorkoutLog(user_id=uid, mode="manual", manual_name="Hill sprints", duration_minutes=40, date=now - timedelta(days=1)),
            WorkoutLog(user_id=uid, mode="manual", manual_name="Long run", duration_minutes=60, date=now - timedelta(days=12)),
        ])
        db.commit()
    finally:
        db.close()

    data = http.get(f"/staff/clients/{client['id']}/progress", headers=coach["headers"]).json()
    assert data["has_account"] is True
    assert [w["weight_kg"] for w in data["weights"]] == [90.0, 87.5]
    assert data["summary"]["weight_change_kg"] == -2.5
    assert data["summary"]["workouts_7d"] == 1 and data["summary"]["workouts_30d"] == 2
    assert data["summary"]["minutes_30d"] == 100
    assert data["workouts"][0]["name"] == "Hill sprints"

    row = http.get("/coach/team", headers=coach["headers"]).json()["clients"][0]
    assert row["workouts_7d"] == 1 and row["progress"] == round(1 / 7 * 100)


def test_progress_for_client_without_activity_is_empty_not_fabricated():
    coach = make_coach()
    client = make_client(coach)
    data = http.get(f"/staff/clients/{client['id']}/progress", headers=coach["headers"]).json()
    assert data["weights"] == [] and data["workouts"] == []
    assert data["summary"]["latest_weight_kg"] is None
    row = http.get("/coach/team", headers=coach["headers"]).json()["clients"][0]
    assert row["progress"] == 0 and row["program"] == "No active program"


# ---------- plans ----------

PLAN = {"name": "8-Week Strength", "plan_type": "workout", "duration_weeks": 8, "difficulty": "Intermediate", "items": ["Squat 5x5", "Bench 5x5", " "]}


def test_plan_crud_persists_and_validates():
    coach = make_coach()
    assert http.post("/staff/plans", headers=coach["headers"], json={**PLAN, "name": "x"}).status_code == 422
    r = http.post("/staff/plans", headers=coach["headers"], json=PLAN)
    assert r.status_code == 201
    plan = r.json()
    assert plan["items"] == ["Squat 5x5", "Bench 5x5"] and plan["duration_weeks"] == 8 and plan["version"] == 1

    r = http.put(f"/staff/plans/{plan['id']}", headers=coach["headers"], json={**PLAN, "name": "12-Week Strength", "duration_weeks": 12})
    assert r.json()["version"] == 2
    listed = http.get("/staff/plans", headers=coach["headers"]).json()["plans"]
    assert [(p["name"], p["duration_weeks"]) for p in listed] == [("12-Week Strength", 12)]

    assert http.delete(f"/staff/plans/{plan['id']}", headers=coach["headers"]).status_code == 200
    assert http.get("/staff/plans", headers=coach["headers"]).json()["plans"] == []
    assert http.put(f"/staff/plans/{plan['id']}", headers=coach["headers"], json=PLAN).status_code == 404


def test_plans_are_private_to_their_coach():
    a, b = make_coach(), make_coach()
    plan = http.post("/staff/plans", headers=a["headers"], json=PLAN).json()
    assert http.get("/staff/plans", headers=b["headers"]).json()["plans"] == []
    assert http.put(f"/staff/plans/{plan['id']}", headers=b["headers"], json=PLAN).status_code == 403
    assert http.delete(f"/staff/plans/{plan['id']}", headers=b["headers"]).status_code == 403
    client_of_b = make_client(b)
    r = http.post(f"/staff/plans/{plan['id']}/assignments", headers=b["headers"], json={"client_id": client_of_b["id"]})
    assert r.status_code == 403
    # cannot attach a plan to someone else's team
    team_a = make_team(a)
    assert http.post("/staff/plans", headers=b["headers"], json={**PLAN, "team_id": team_a["id"]}).status_code == 403


def test_assign_plan_to_client_and_team_visible_to_client():
    coach = make_coach()
    team = make_team(coach)
    c1 = make_client(coach, team["id"], name="Team One")
    c2 = make_client(coach, team["id"], name="Team Two")
    solo = make_client(coach, name="Solo")
    http.post(f"/staff/clients/{solo['id']}/team", headers=coach["headers"], json={"team_id": None})
    plan = http.post("/staff/plans", headers=coach["headers"], json=PLAN).json()
    url = f"/staff/plans/{plan['id']}/assignments"

    assert http.post(url, headers=coach["headers"], json={}).status_code == 400
    assert http.post(url, headers=coach["headers"], json={"client_id": solo["id"], "team_id": team["id"]}).status_code == 400

    assert http.post(url, headers=coach["headers"], json={"client_id": solo["id"], "notes": "Start Monday"}).status_code == 200
    r = http.post(url, headers=coach["headers"], json={"team_id": team["id"]})
    assert sorted(r.json()["assigned_client_ids"]) == sorted([c1["id"], c2["id"]])
    # idempotent
    http.post(url, headers=coach["headers"], json={"client_id": solo["id"]})

    mine = http.get("/staff/my/plans", headers=c1["headers"]).json()["plans"]
    assert [p["name"] for p in mine] == ["8-Week Strength"] and mine[0]["items"] == ["Squat 5x5", "Bench 5x5"]
    assert http.get("/staff/plans", headers=coach["headers"]).json()["plans"][0]["assigned_clients"] == 3
    assert len(http.get(f"/staff/clients/{solo['id']}/plans", headers=coach["headers"]).json()["plans"]) == 1

    row = next(c for c in http.get("/coach/team", headers=coach["headers"]).json()["clients"] if c["id"] == c1["id"])
    assert row["program"] == "8-Week Strength"

    assert http.delete(f"{url}/{c1['id']}", headers=coach["headers"]).status_code == 200
    assert http.get("/staff/my/plans", headers=c1["headers"]).json()["plans"] == []
    assert http.delete(f"{url}/{c1['id']}", headers=coach["headers"]).status_code == 404

    # deleting a plan removes it from clients
    http.delete(f"/staff/plans/{plan['id']}", headers=coach["headers"])
    assert http.get("/staff/my/plans", headers=c2["headers"]).json()["plans"] == []


def test_assign_to_empty_team_is_rejected():
    coach = make_coach()
    team = make_team(coach)
    plan = http.post("/staff/plans", headers=coach["headers"], json=PLAN).json()
    assert http.post(f"/staff/plans/{plan['id']}/assignments", headers=coach["headers"], json={"team_id": team["id"]}).status_code == 400


# ---------- teams ----------

def test_team_assignment_roster_and_isolation():
    a, b = make_coach(), make_coach()
    team = make_team(a, "Alpha")
    solo = make_client(a)
    assert http.post(f"/staff/clients/{solo['id']}/team", headers=a["headers"], json={"team_id": team["id"]}).json()["team_id"] == team["id"]
    roster = http.get(f"/staff/teams/{team['id']}/roster", headers=a["headers"]).json()
    assert [c["id"] for c in roster["clients"]] == [solo["id"]] and roster["team"]["client_count"] == 1

    assert http.get(f"/staff/teams/{team['id']}/roster", headers=b["headers"]).status_code == 403
    assert http.get("/staff/teams", headers=b["headers"]).json()["teams"] == []
    assert http.post(f"/staff/clients/{solo['id']}/team", headers=a["headers"], json={"team_id": make_team(b)["id"]}).status_code == 403
    assert http.get(f"/staff/teams/999999/roster", headers=a["headers"]).status_code == 404

    assert http.post(f"/staff/clients/{solo['id']}/team", headers=a["headers"], json={"team_id": None}).json()["team_id"] is None
    assert http.put(f"/staff/teams/{team['id']}", headers=a["headers"], json={"name": "Alpha 2"}).json()["name"] == "Alpha 2"
    assert http.put(f"/staff/teams/{team['id']}", headers=b["headers"], json={"name": "Hijack"}).status_code == 403
    assert http.delete(f"/staff/teams/{team['id']}", headers=b["headers"]).status_code == 403
    assert http.delete(f"/staff/teams/{team['id']}", headers=a["headers"]).status_code == 200
    assert http.get("/staff/teams", headers=a["headers"]).json()["teams"] == []


def test_dashboard_lists_only_own_teams_and_rejects_foreign_team():
    a, b = make_coach(), make_coach()
    team_a = make_team(a)
    make_client(a, team_a["id"])
    data = http.get("/coach/team", headers=a["headers"]).json()
    assert data["team_id"] == team_a["id"] and data["stats"]["totalClients"] == 1
    assert http.get(f"/coach/team?team_id={team_a['id']}", headers=b["headers"]).status_code == 403
    assert http.get("/coach/team", headers=b["headers"]).json()["clients"] == []


def test_legacy_team_router_requires_ownership():
    a, b = make_coach(), make_coach()
    team = make_team(a)
    assert http.get(f"/team/{team['id']}", headers=b["headers"]).status_code == 403
    assert http.get(f"/team/{team['id']}/roster", headers=b["headers"]).status_code == 403
    assert http.get(f"/team/coach/{a['id']}", headers=b["headers"]).status_code == 403
    assert http.post("/team/create", headers=b["headers"], json={"coach_id": a["id"], "name": "Stolen"}).status_code == 403
    assert http.put(f"/team/{team['id']}/update", headers=b["headers"], json={"updates": {"name": "x"}}).status_code == 403
    assert http.get(f"/team/{team['id']}", headers=a["headers"]).status_code == 200
    # coach_id cannot be reassigned through the generic update
    r = http.put(f"/team/{team['id']}/update", headers=a["headers"], json={"updates": {"coach_id": b["id"], "name": "Renamed"}})
    assert r.status_code == 200 and r.json()["coach_id"] == a["id"] and r.json()["name"] == "Renamed"


# ---------- messaging ----------

def test_messaging_roundtrip_persistence_and_read_state():
    coach = make_coach()
    client = make_client(coach, name="Msg Client")
    cid = client["id"]

    assert http.post(f"/staff/messages/{cid}", headers=coach["headers"], json={"body": "   "}).status_code in (400, 422)
    assert http.post(f"/staff/messages/{cid}", headers=coach["headers"], json={"body": "Welcome aboard"}).status_code == 201

    mine = http.get("/staff/my/messages", headers=client["headers"]).json()
    assert mine["unread"] == 1 and mine["coach"]["id"] == coach["id"]
    assert [(m["sender"], m["body"]) for m in mine["messages"]] == [("coach", "Welcome aboard")]
    assert http.post("/staff/my/messages/read", headers=client["headers"]).json()["marked_read"] == 1
    assert http.get("/staff/my/messages", headers=client["headers"]).json()["unread"] == 0

    assert http.post("/staff/my/messages", headers=client["headers"], json={"body": "Thanks coach!"}).status_code == 201
    threads = http.get("/staff/messages/threads", headers=coach["headers"]).json()
    assert threads["unread_total"] == 1
    assert threads["threads"][0]["last_message"] == "Thanks coach!" and threads["threads"][0]["unread"] == 1
    assert http.get("/coach/team", headers=coach["headers"]).json()["stats"]["messagesUnread"] == 1

    thread = http.get(f"/staff/messages/{cid}", headers=coach["headers"]).json()
    assert [m["sender"] for m in thread["messages"]] == ["coach", "client"]
    assert http.post(f"/staff/messages/{cid}/read", headers=coach["headers"]).json()["marked_read"] == 1
    assert http.get("/staff/messages/threads", headers=coach["headers"]).json()["unread_total"] == 0


def test_messages_are_isolated_between_coaches_and_clients():
    a, b = make_coach(), make_coach()
    ca, cb = make_client(a), make_client(b)
    http.post(f"/staff/messages/{ca['id']}", headers=a["headers"], json={"body": "secret for A's client"})
    http.post(f"/staff/messages/{cb['id']}", headers=b["headers"], json={"body": "for B's client"})
    assert [m["body"] for m in http.get("/staff/my/messages", headers=cb["headers"]).json()["messages"]] == ["for B's client"]
    threads_b = http.get("/staff/messages/threads", headers=b["headers"]).json()["threads"]
    assert [t["client_id"] for t in threads_b] == [cb["id"]]


def test_team_broadcast():
    coach, other = make_coach(), make_coach()
    team = make_team(coach)
    c1, c2 = make_client(coach, team["id"]), make_client(coach, team["id"])
    outsider = make_client(coach)
    http.post(f"/staff/clients/{outsider['id']}/team", headers=coach["headers"], json={"team_id": None})
    r = http.post("/staff/messages/broadcast", headers=coach["headers"], json={"team_id": team["id"], "body": "Practice at 6"})
    assert r.json()["sent_to"] == 2
    for c in (c1, c2):
        assert http.get("/staff/my/messages", headers=c["headers"]).json()["messages"][0]["body"] == "Practice at 6"
    assert http.get("/staff/my/messages", headers=outsider["headers"]).json()["messages"] == []
    assert http.post("/staff/messages/broadcast", headers=other["headers"], json={"team_id": team["id"], "body": "x"}).status_code == 403


# ---------- drills ----------

def test_drill_library_is_per_coach():
    a, b = make_coach(), make_coach()
    r = http.post("/staff/drills", headers=a["headers"], json={"name": "Box Jumps", "category": "Strength", "difficulty": "hard"})
    assert r.status_code == 201
    drill = r.json()
    assert [d["name"] for d in http.get("/staff/drills", headers=a["headers"]).json()["drills"]] == ["Box Jumps"]
    assert http.get("/staff/drills", headers=b["headers"]).json()["drills"] == []
    assert http.put(f"/staff/drills/{drill['id']}", headers=b["headers"], json={"name": "Hijacked"}).status_code == 403
    assert http.put(f"/staff/drills/{drill['id']}", headers=a["headers"], json={"name": "Box Jumps 2", "category": "Strength"}).json()["name"] == "Box Jumps 2"
    assert http.delete(f"/staff/drills/{drill['id']}", headers=b["headers"]).status_code == 403
    assert http.delete(f"/staff/drills/{drill['id']}", headers=a["headers"]).status_code == 200
    assert http.get("/staff/drills", headers=a["headers"]).json()["drills"] == []


# ---------- migrations ----------

def test_coach_hub_migration_is_idempotent_and_additive():
    run_migrations()
    run_migrations()
    tables = set(inspect(engine).get_table_names())
    assert {"coach_messages", "plan_assignments", "plans", "clients", "coaches"} <= tables

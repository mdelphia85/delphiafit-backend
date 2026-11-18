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
from app.auth.jwt_handler import create_access_token  # noqa: E402
from app.crud.coach import CoachCRUD  # noqa: E402
from app.database.connection import SessionLocal, engine  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.coach import Coach  # noqa: E402
from app.models.coach_team_membership import CoachTeamMembership  # noqa: E402
from app.models.invite import Invite  # noqa: E402
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


def make_admin_headers():
    email = uniq("coach-admin")
    registered = http.post("/auth/register", json={"name": "Coach Admin", "email": email, "password": PASSWORD})
    assert registered.status_code == 200, registered.text
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.is_admin = True
        db.commit()
    response = http.post("/admin/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return bearer(response.json()["access_token"])


def assert_no_credential_fields(value):
    sensitive_fields = {
        "hashed_password",
        "password",
        "password_reset_token_hash",
        "password_reset_expires_at",
        "token_version",
        "token",
        "token_hash",
        "token_digest",
        "secret",
        "secret_token",
        "reset_token",
        "access_token",
        "invitation_token",
        "invite_token",
    }
    if isinstance(value, dict):
        assert sensitive_fields.isdisjoint(value)
        for nested in value.values():
            assert_no_credential_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_credential_fields(nested)


def make_team(coach, name="Varsity"):
    r = http.post("/staff/teams", headers=coach["headers"], json={"name": name, "sport": "soccer"})
    assert r.status_code == 201, r.text
    return r.json()


def invitation_token(invite_id):
    with SessionLocal() as db:
        return db.query(Invite).filter(Invite.id == invite_id).one().token


def make_client(coach, team_id=None, name="Client One"):
    """Invite + accept through the real endpoints; returns client dict with user headers."""
    email = uniq("client")
    body = {"email": email}
    if team_id:
        body["team_id"] = team_id
    r = http.post("/staff/clients/invite", headers=coach["headers"], json=body)
    assert r.status_code == 200, r.text
    token = invitation_token(r.json()["invite_id"])
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
    sent = []
    monkeypatch.setattr("app.routers.coach.send_coach_password_reset", lambda email, token: sent.append((email, token)) or True)
    monkeypatch.setenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "true")
    coach = make_coach()
    old_headers = coach["headers"]
    r = http.post("/coach/password/forgot", json={"email": coach["email"]})
    missing = http.post("/coach/password/forgot", json={"email": uniq("unknown-coach")})
    assert r.json() == missing.json()
    assert "debug_token" not in r.json()
    token = sent[0][1]
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": "bad", "new_password": "NewPassw0rd!!"}).status_code == 400
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "short"}).status_code == 400
    r = http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "NewPassw0rd!!"})
    assert r.status_code == 200
    assert http.get("/staff/clients", headers=old_headers).status_code == 401
    assert http.post("/coach/login", json={"email": coach["email"], "password": PASSWORD}).status_code == 401
    fresh = http.post("/coach/login", json={"email": coach["email"], "password": "NewPassw0rd!!"})
    assert fresh.status_code == 200
    fresh_headers = bearer(fresh.json()["access_token"])
    assert http.get("/staff/clients", headers=fresh_headers).status_code == 200
    assert http.post("/coach/password/forgot", json={"email": coach["email"]}).status_code == 200
    second_token = sent[1][1]
    assert http.post("/coach/password/reset", json={
        "email": coach["email"],
        "token": second_token,
        "new_password": "Another0ne!!!",
    }).status_code == 200
    assert http.get("/staff/clients", headers=fresh_headers).status_code == 401
    # token is single use
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": token, "new_password": "Another0ne!!!"}).status_code == 400
    assert http.post("/coach/login", json={"email": coach["email"], "password": "Another0ne!!!"}).status_code == 200


def test_coach_tokens_without_a_version_claim_are_rejected():
    coach = make_coach()
    legacy = create_access_token({
        "sub": str(coach["id"]),
        "email": coach["email"],
        "actor_type": "coach",
        "role": "coach",
    })
    assert http.get("/staff/clients", headers=bearer(legacy)).status_code == 401


def test_coach_tokens_with_stale_or_forged_versions_are_rejected():
    coach = make_coach()
    with SessionLocal() as db:
        row = db.query(Coach).filter(Coach.id == coach["id"]).one()
        current_version = row.token_version
        row.token_version += 1
        db.commit()
    stale = create_access_token({
        "sub": str(coach["id"]),
        "email": coach["email"],
        "actor_type": "coach",
        "role": "coach",
        "token_version": current_version,
    })
    assert http.get("/staff/clients", headers=bearer(stale)).status_code == 401


def test_coach_deactivation_and_reactivation_never_revive_old_sessions():
    admin = make_admin_headers()
    coach = make_coach()
    unaffected = make_coach()
    old_headers = coach["headers"]
    unaffected_headers = unaffected["headers"]

    assert http.get("/staff/clients", headers=old_headers).status_code == 200
    assert http.get("/staff/clients", headers=unaffected_headers).status_code == 200

    deactivated = http.delete(f"/coach/{coach['id']}/deactivate", headers=admin)
    assert deactivated.status_code == 200, deactivated.text
    assert_no_credential_fields(deactivated.json())
    assert http.get("/staff/clients", headers=old_headers).status_code == 401
    assert http.get("/staff/clients", headers=unaffected_headers).status_code == 200

    reactivated = http.put(
        f"/coach/{coach['id']}/update",
        headers=admin,
        json={"updates": {"is_active": True}},
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["is_active"] is True
    assert_no_credential_fields(reactivated.json())
    assert http.get("/staff/clients", headers=old_headers).status_code == 401

    fresh_login = http.post("/coach/login", json={"email": coach["email"], "password": PASSWORD})
    assert fresh_login.status_code == 200, fresh_login.text
    fresh_headers = bearer(fresh_login.json()["access_token"])
    assert http.get("/staff/clients", headers=fresh_headers).status_code == 200

    assert http.delete(f"/coach/{coach['id']}/deactivate", headers=admin).status_code == 200
    assert http.put(
        f"/coach/{coach['id']}/update",
        headers=admin,
        json={"updates": {"is_active": True}},
    ).status_code == 200
    assert http.get("/staff/clients", headers=old_headers).status_code == 401
    assert http.get("/staff/clients", headers=fresh_headers).status_code == 401
    assert http.get("/staff/clients", headers=unaffected_headers).status_code == 200

    newest_login = http.post("/coach/login", json={"email": coach["email"], "password": PASSWORD})
    assert newest_login.status_code == 200
    assert http.get("/staff/clients", headers=bearer(newest_login.json()["access_token"])).status_code == 200


def test_failed_coach_deactivation_rolls_back_active_state_and_token_version(monkeypatch):
    coach = make_coach()
    with SessionLocal() as db:
        row = db.query(Coach).filter(Coach.id == coach["id"]).one()
        original_version = row.token_version

        def fail_commit():
            raise RuntimeError("synthetic coach deactivation failure")

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="synthetic coach deactivation failure"):
            CoachCRUD().deactivate_coach(db, coach["id"])

        db.expire_all()
        row = db.query(Coach).filter(Coach.id == coach["id"]).one()
        assert row.is_active is True
        assert row.token_version == original_version

    assert http.get("/staff/clients", headers=coach["headers"]).status_code == 200


def test_admin_coach_responses_exclude_credentials_and_require_admin():
    admin = make_admin_headers()
    created = http.post(
        "/coach/create",
        headers=admin,
        json={"email": uniq("admin-created-coach"), "name": "New Coach", "role": "coach"},
    )
    assert created.status_code == 200, created.text
    assert_no_credential_fields(created.json())

    regular_email = uniq("regular")
    assert http.post(
        "/auth/register",
        json={"name": "Regular User", "email": regular_email, "password": PASSWORD},
    ).status_code == 200
    regular_token = http.post(
        "/auth/login",
        json={"email": regular_email, "password": PASSWORD},
    ).json()["access_token"]
    regular = bearer(regular_token)

    coach = make_coach()
    team = make_team(coach)
    make_client(coach, team["id"])

    updated = http.put(
        f"/coach/{coach['id']}/update",
        headers=admin,
        json={"updates": {"name": "Updated Coach Name"}},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Updated Coach Name"
    assert_no_credential_fields(updated.json())

    for path in (
        f"/coach/{coach['id']}",
        f"/coach/email/{coach['email']}",
        f"/coach/{coach['id']}/teams",
        f"/coach/{coach['id']}/clients",
    ):
        response = http.get(path, headers=admin)
        assert response.status_code == 200, response.text
        assert_no_credential_fields(response.json())
        assert http.get(path).status_code == 401
        assert http.get(path, headers=regular).status_code == 403

    denied_update = http.put(
        f"/coach/{coach['id']}/update",
        headers=regular,
        json={"updates": {"name": "Unauthorized"}},
    )
    assert denied_update.status_code == 403
    assert http.put(
        f"/coach/{coach['id']}/update",
        json={"updates": {"name": "Unauthorized"}},
    ).status_code == 401
    assert http.delete(f"/coach/{coach['id']}/deactivate", headers=regular).status_code == 403
    assert http.delete(f"/coach/{coach['id']}/deactivate").status_code == 401


def test_coach_password_reset_rejects_expired_token(monkeypatch):
    sent = []
    monkeypatch.setattr("app.routers.coach.send_coach_password_reset", lambda email, token: sent.append((email, token)) or True)
    coach = make_coach()
    assert http.post("/coach/password/forgot", json={"email": coach["email"]}).status_code == 200
    with SessionLocal() as db:
        row = db.query(Coach).filter(Coach.id == coach["id"]).one()
        row.password_reset_expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    assert http.post("/coach/password/reset", json={"email": coach["email"], "token": sent[0][1], "new_password": "Another0ne!!!"}).status_code == 400


def test_coach_invitation_flow_gives_team_access(monkeypatch):
    monkeypatch.setattr("app.routers.coach_hub.send_coach_invitation", lambda email, token: True)
    owner = make_coach()
    team = make_team(owner)
    client = make_client(owner, team["id"])
    assistant_email = uniq("assistant")
    r = http.post(f"/staff/teams/{team['id']}/coach-invitations", headers=owner["headers"], json={"email": assistant_email, "role": "assistant_coach"})
    assert r.status_code == 201, r.text
    assert "invite_token" not in r.json()
    invite_id = r.json()["invite_id"]
    token = invitation_token(invite_id)

    lookup = http.post("/staff/invitations/lookup", json={"token": token})
    assert lookup.json() == {"email": assistant_email, "role": "coach", "existing_coach": False}
    # a coach invite cannot be accepted on the client endpoint
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "Asst", "password": PASSWORD}).status_code == 400

    r = http.post("/coach/invitations/accept", json={"invitation_token": token, "name": "Assistant", "password": PASSWORD})
    assert r.status_code == 200, r.text
    assert http.post("/staff/invitations/lookup", json={"token": token}).status_code == 404  # single use

    login = http.post("/coach/login", json={"email": assistant_email, "password": PASSWORD})
    assert login.status_code == 200 and login.json()["team_id"] == team["id"]
    headers = bearer(login.json()["access_token"])
    clients = http.get("/staff/clients", headers=headers).json()["clients"]
    assert [c["id"] for c in clients] == [client["id"]]
    # assistants are not team owners
    assert http.put(f"/staff/teams/{team['id']}", headers=headers, json={"name": "Renamed"}).status_code == 403
    assert http.post(f"/staff/teams/{team['id']}/coach-invitations", headers=headers, json={"email": uniq("x")}).status_code == 403
    assert http.post("/coach/invite/accept", json={"token": token, "name": "Assistant"}).status_code == 400


def test_existing_coach_invitation_requires_recipient_and_preserves_credentials(monkeypatch):
    monkeypatch.setattr("app.routers.coach_hub.send_coach_invitation", lambda email, token: True)
    owner = make_coach()
    team = make_team(owner)
    invited_coach = make_coach()
    old_headers = invited_coach["headers"]

    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": invited_coach["email"], "role": "assistant_coach"},
    )
    assert invitation.status_code == 201, invitation.text
    assert "invite_token" not in invitation.json()
    token = invitation_token(invitation.json()["invite_id"])

    lookup = http.post("/staff/invitations/lookup", json={"token": token})
    assert lookup.json()["existing_coach"] is True
    owner_attempt = http.post(
        "/coach/invitations/accept",
        headers=owner["headers"],
        json={"invitation_token": token, "name": "Taken Over", "password": "InvitationPass456!"},
    )
    assert owner_attempt.status_code == 403
    assert invitation_token(invitation.json()["invite_id"]) == token
    assert http.get("/staff/clients", headers=old_headers).status_code == 200
    assert http.post("/coach/login", json={"email": invited_coach["email"], "password": PASSWORD}).status_code == 200
    with SessionLocal() as db:
        row = db.query(Coach).filter(Coach.id == invited_coach["id"]).one()
        original_hash = row.hashed_password
        original_version = row.token_version
        original_role = row.role
        row_id = row.id

    intended_accept = http.post(
        "/coach/invitations/accept",
        headers=old_headers,
        json={"invitation_token": token},
    )
    assert intended_accept.status_code == 200, intended_accept.text
    assert http.get("/staff/clients", headers=old_headers).status_code == 200
    assert http.post("/coach/login", json={"email": invited_coach["email"], "password": PASSWORD}).status_code == 200
    with SessionLocal() as db:
        row = db.query(Coach).filter(Coach.id == row_id).one()
        assert row.hashed_password == original_hash
        assert row.token_version == original_version
        assert row.role == original_role
        membership = db.query(CoachTeamMembership).filter_by(coach_id=row_id, team_id=team["id"]).one()
        assert membership.role == "assistant_coach"


def test_existing_coach_invitation_rejects_password_change_and_unrelated_recipient():
    owner, intended, unrelated = make_coach(), make_coach(), make_coach()
    team = make_team(owner)
    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": intended["email"], "role": "assistant_coach"},
    )
    token = invitation_token(invitation.json()["invite_id"])
    assert http.post("/coach/invitations/accept", json={"invitation_token": token}).status_code == 401
    owner_attempt = http.post(
        "/coach/invitations/accept",
        headers=unrelated["headers"],
        json={"invitation_token": token},
    )
    assert owner_attempt.status_code == 403
    password_attempt = http.post(
        "/coach/invitations/accept",
        headers=intended["headers"],
        json={"invitation_token": token, "password": "InvitationPass456!"},
    )
    assert password_attempt.status_code == 400
    assert http.get("/staff/clients", headers=intended["headers"]).status_code == 200


def test_concurrent_existing_coach_invitation_acceptance_creates_one_membership():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    owner, intended = make_coach(), make_coach()
    team = make_team(owner)
    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": intended["email"], "role": "assistant_coach"},
    )
    token = invitation_token(invitation.json()["invite_id"])
    start = Barrier(2)

    def accept():
        start.wait()
        return http.post(
            "/coach/invitations/accept",
            headers=intended["headers"],
            json={"invitation_token": token},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: accept(), range(2)))

    assert sorted(result.status_code for result in results) == [200, 400]
    with SessionLocal() as db:
        assert db.query(CoachTeamMembership).filter_by(coach_id=intended["id"], team_id=team["id"]).count() == 1
        assert db.query(Invite).filter_by(id=invitation.json()["invite_id"], accepted=True).count() == 1


def test_new_coach_invitation_registration_requires_password_and_is_single_use(monkeypatch):
    monkeypatch.setattr("app.routers.coach_hub.send_coach_invitation", lambda email, token: True)
    owner = make_coach()
    team = make_team(owner)
    email = uniq("new-invited-coach")
    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": email, "role": "assistant_coach"},
    )
    token = invitation_token(invitation.json()["invite_id"])
    assert http.post(
        "/coach/invitations/accept",
        json={"invitation_token": token, "name": "New Coach"},
    ).status_code == 400
    accepted = http.post(
        "/coach/invitations/accept",
        json={"invitation_token": token, "name": "New Coach", "password": PASSWORD},
    )
    assert accepted.status_code == 200, accepted.text
    assert http.post(
        "/coach/invitations/accept",
        json={"invitation_token": token, "name": "New Coach", "password": PASSWORD},
    ).status_code == 400
    assert http.post("/coach/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_coach_invitation_acceptance_rejects_legacy_query_lookup_and_does_not_log_token(caplog):
    owner = make_coach()
    team = make_team(owner)
    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": uniq("lookup-marker"), "role": "assistant_coach"},
    )
    token = invitation_token(invitation.json()["invite_id"])
    assert http.get("/staff/invitations/lookup", params={"token": token}).status_code == 405
    result = http.post("/staff/invitations/lookup", json={"token": token})
    assert result.status_code == 200
    assert token not in result.text
    assert token not in caplog.text


def test_sensitive_query_values_are_removed_before_asgi_access_logging():
    import asyncio
    from starlette.responses import Response

    from app.main import redact_sensitive_query_strings

    marker = "synthetic-access-log-marker"

    class Request:
        scope = {"query_string": f"token={marker}&page=2".encode()}

    async def call_next(request):
        assert request.scope["query_string"] == b""
        return Response()

    asyncio.run(redact_sensitive_query_strings(Request(), call_next))


def test_coach_invitation_existing_account_preserves_original_password_after_unauthorized_attempt(monkeypatch):
    monkeypatch.setattr("app.routers.coach_hub.send_coach_invitation", lambda email, token: True)
    owner = make_coach()
    invited_coach = make_coach()
    team = make_team(owner)
    invitation = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": invited_coach["email"], "role": "assistant_coach"},
    )
    token = invitation_token(invitation.json()["invite_id"])
    denied = http.post(
        "/coach/invitations/accept",
        headers=owner["headers"],
        json={"invitation_token": token, "name": "Unauthorized", "password": "InvitationPass456!"},
    )
    assert denied.status_code == 403
    assert http.post("/coach/login", json={"email": invited_coach["email"], "password": PASSWORD}).status_code == 200


def test_client_invitation_flow_and_lookup():
    coach = make_coach()
    email = uniq("newclient")
    r = http.post("/staff/clients/invite", headers=coach["headers"], json={"email": email})
    assert r.status_code == 200
    assert "invite_token" not in r.json()
    token = invitation_token(r.json()["invite_id"])
    assert http.post("/staff/invitations/lookup", json={"token": token}).json()["role"] == "client"
    pending = http.get("/staff/invitations", headers=coach["headers"]).json()["invitations"]
    assert [(i["email"], i["accepted"]) for i in pending] == [(email, False)]
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "New Client", "password": "short"}).status_code == 400
    assert http.post("/staff/invitations/accept", json={"invitation_token": token, "name": "New Client", "password": PASSWORD}).status_code == 200
    clients = http.get("/staff/clients", headers=coach["headers"]).json()["clients"]
    assert [c["email"] for c in clients] == [email]
    assert http.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    assert http.post("/staff/clients/invite", headers=coach["headers"], json={"email": email}).status_code == 400


def test_pending_invitation_can_be_revoked_only_by_owner():
    a, b = make_coach(), make_coach()
    r = http.post("/staff/clients/invite", headers=a["headers"], json={"email": uniq("p")})
    invite_id = r.json()["invite_id"]
    assert http.delete(f"/staff/invitations/{invite_id}", headers=b["headers"]).status_code == 403
    assert http.delete(f"/staff/invitations/{invite_id}", headers=a["headers"]).status_code == 200
    assert http.get("/staff/invitations", headers=a["headers"]).json()["invitations"] == []
    assert http.post("/invite/revoke", headers=b["headers"], json={"invite_id": invite_id}).status_code == 404


def test_team_invitation_listing_exposes_metadata_only_and_preserves_invitation_flows(monkeypatch, caplog):
    monkeypatch.setattr("app.routers.coach_hub.send_coach_invitation", lambda email, token: True)
    monkeypatch.setattr("app.routers.staff.send_client_invitation", lambda email, token: True)

    owner = make_coach()
    unrelated = make_coach()
    team = make_team(owner)

    assistant_email = uniq("team-assistant")
    assistant_invite = http.post(
        f"/staff/teams/{team['id']}/coach-invitations",
        headers=owner["headers"],
        json={"email": assistant_email, "role": "assistant_coach"},
    )
    assert assistant_invite.status_code == 201, assistant_invite.text
    assistant_token = invitation_token(assistant_invite.json()["invite_id"])
    accepted_assistant = http.post(
        "/coach/invitations/accept",
        json={
            "invitation_token": assistant_token,
            "name": "Team Assistant",
            "password": "AssistantPass456!",
        },
    )
    assert accepted_assistant.status_code == 200, accepted_assistant.text
    assistant_login = http.post(
        "/coach/login",
        json={"email": assistant_email, "password": "AssistantPass456!"},
    )
    assert assistant_login.status_code == 200
    assistant = {"id": accepted_assistant.json()["coach_id"], "headers": bearer(assistant_login.json()["access_token"])}

    client_email = uniq("team-invite-client")
    client_invite = http.post(
        "/staff/clients/invite",
        headers=owner["headers"],
        json={"email": client_email, "team_id": team["id"]},
    )
    assert client_invite.status_code == 200, client_invite.text
    client_token = invitation_token(client_invite.json()["invite_id"])
    client_invite_id = client_invite.json()["invite_id"]

    listings = (
        http.get(f"/team/{team['id']}/invites", headers=assistant["headers"]),
        http.get(f"/invite/team/{team['id']}", headers=assistant["headers"]),
        http.get(f"/invite/coach/{owner['id']}", headers=owner["headers"]),
        http.get(f"/invite/{client_invite_id}", headers=owner["headers"]),
        http.get("/staff/invitations", headers=owner["headers"]),
    )
    for response in listings:
        assert response.status_code == 200, response.text
        assert_no_credential_fields(response.json())
        assert assistant_token not in response.text
        assert client_token not in response.text

    team_invites = listings[0].json()
    assert {invite["email"] for invite in team_invites} >= {assistant_email, client_email}
    assert all(
        set(invite) == {"id", "email", "role", "team_id", "accepted", "expires_at", "created_at"}
        for invite in team_invites
    )
    assistant_view = http.get(f"/team/{team['id']}/invites", headers=assistant["headers"])
    assert assistant_view.json() == team_invites

    assert http.get(f"/team/{team['id']}/invites").status_code == 401
    assert http.get(f"/team/{team['id']}/invites", headers=unrelated["headers"]).status_code == 403
    assert http.get(f"/invite/team/{team['id']}").status_code == 401
    assert http.get(f"/invite/team/{team['id']}", headers=unrelated["headers"]).status_code == 403
    assert http.get(f"/invite/coach/{owner['id']}", headers=unrelated["headers"]).status_code == 403
    assert http.get(f"/invite/{client_invite_id}", headers=unrelated["headers"]).status_code == 403
    ordinary_email = uniq("ordinary-invite-user")
    assert http.post(
        "/auth/register",
        json={"name": "Ordinary User", "email": ordinary_email, "password": PASSWORD},
    ).status_code == 200
    ordinary_login = http.post("/auth/login", json={"email": ordinary_email, "password": PASSWORD})
    assert ordinary_login.status_code == 200
    ordinary_headers = bearer(ordinary_login.json()["access_token"])
    assert http.get(f"/team/{team['id']}/invites", headers=ordinary_headers).status_code == 403
    assert http.get(f"/invite/team/{team['id']}", headers=ordinary_headers).status_code == 403
    assert http.get(f"/invite/coach/{owner['id']}", headers=ordinary_headers).status_code == 403
    assert http.get(f"/invite/{client_invite_id}", headers=ordinary_headers).status_code == 403
    assert http.get("/staff/invitations", headers=ordinary_headers).status_code == 403
    assert http.post(
        "/invite/create",
        headers=ordinary_headers,
        json={"team_id": team["id"], "email": uniq("unauthorized-invite")},
    ).status_code == 403

    accepted_client = http.post(
        "/staff/invitations/accept",
        json={"invitation_token": client_token, "name": "Invited Client", "password": PASSWORD},
    )
    assert accepted_client.status_code == 200, accepted_client.text
    assert accepted_client.json()["client_id"]
    assert http.post(
        "/staff/invitations/accept",
        json={"invitation_token": client_token, "name": "Invited Client", "password": PASSWORD},
    ).status_code == 400

    expired_invite = http.post(
        "/staff/clients/invite",
        headers=owner["headers"],
        json={"email": uniq("expired-invite"), "team_id": team["id"]},
    )
    assert expired_invite.status_code == 200
    expired_token = invitation_token(expired_invite.json()["invite_id"])
    with SessionLocal() as db:
        row = db.query(Invite).filter(Invite.id == expired_invite.json()["invite_id"]).one()
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    expired_response = http.post(
        "/staff/invitations/accept",
        json={"invitation_token": expired_token, "name": "Expired Client", "password": PASSWORD},
    )
    assert expired_response.status_code == 400
    assert expired_token not in expired_response.text
    assert http.post("/staff/invitations/lookup", json={"token": expired_token}).status_code == 404

    revoked_invite = http.post(
        "/staff/clients/invite",
        headers=owner["headers"],
        json={"email": uniq("revoked-invite"), "team_id": team["id"]},
    )
    assert revoked_invite.status_code == 200
    revoked_token = invitation_token(revoked_invite.json()["invite_id"])
    revoked = http.delete(
        f"/staff/invitations/{revoked_invite.json()['invite_id']}",
        headers=owner["headers"],
    )
    assert revoked.status_code == 200, revoked.text
    revoked_response = http.post(
        "/staff/invitations/accept",
        json={"invitation_token": revoked_token, "name": "Revoked Client", "password": PASSWORD},
    )
    assert revoked_response.status_code == 400
    assert revoked_token not in revoked_response.text
    assert http.post("/staff/invitations/lookup", json={"token": revoked_token}).status_code == 404
    assert expired_token not in caplog.text
    assert revoked_token not in caplog.text


def test_legacy_invite_router_is_authenticated_owner_scoped_and_token_free(monkeypatch):
    monkeypatch.setattr("app.routers.invite.send_coach_invitation", lambda email, token: True)
    owner, other = make_coach(), make_coach()
    team = make_team(owner)
    body = {"team_id": team["id"], "email": uniq("legacy"), "role": "assistant_coach"}
    assert http.post("/invite/create", headers=other["headers"], json=body).status_code == 403
    assert http.post("/invite/create", headers=owner["headers"], json={**body, "coach_id": other["id"]}).status_code == 403
    created = http.post("/invite/create", headers=owner["headers"], json=body)
    assert created.status_code == 200
    assert "token" not in created.json()
    invite_id = created.json()["invite_id"]
    original_token = invitation_token(invite_id)
    resent = http.post("/invite/resend", headers=owner["headers"], json={"invite_id": invite_id})
    assert resent.status_code == 200
    assert "new_token" not in resent.json()
    new_token = invitation_token(invite_id)
    assert new_token != original_token
    assert http.post("/staff/invitations/lookup", json={"token": original_token}).status_code == 404
    assert http.post("/staff/invitations/lookup", json={"token": new_token}).status_code == 200


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

import os
import socket
import threading
import time
import tempfile
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "pro_area_test.db")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from app.database.migrate import run_migrations
from app.main import app, get_cors_origins, normalize_staging_frontend_origin
from app.database.connection import SessionLocal
from app.crud.user import update_user
from app.models.injury import Injury
from app.models.login_log import LoginLog
from app.models.org_membership import OrganizationMembership
from app.models.hardware import UserDevice
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services import email_delivery

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


def test_staging_cors_is_explicit_normalized_and_preserves_auth(monkeypatch):
    staging_origin = "https://Staging.DelphiaFit.example:443/"
    monkeypatch.setenv("STAGING_FRONTEND_ORIGIN", staging_origin)
    allowed_origins = get_cors_origins()
    assert "https://delphiafit.com" in allowed_origins
    assert "https://www.delphiafit.com" in allowed_origins
    assert "https://delphiafit-web.vercel.app" in allowed_origins
    assert "https://staging.delphiafit.example" in allowed_origins

    cors_app = CORSMiddleware(
        app,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    with TestClient(cors_app) as cors_client:
        for origin in ("https://delphiafit.com", "https://staging.delphiafit.example"):
            preflight = cors_client.options(
                "/ai/records",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "authorization",
                },
            )
            assert preflight.status_code == 200
            assert preflight.headers["access-control-allow-origin"] == origin
            assert preflight.headers["access-control-allow-credentials"] == "true"

        rejected_preflight = cors_client.options(
            "/ai/records",
            headers={
                "Origin": "https://unknown.example",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert rejected_preflight.status_code == 400
        assert "access-control-allow-origin" not in rejected_preflight.headers

        unauthorized = cors_client.get(
            "/ai/records",
            headers={"Origin": "https://staging.delphiafit.example"},
        )
        assert unauthorized.status_code == 401
        assert unauthorized.headers["access-control-allow-origin"] == "https://staging.delphiafit.example"

        session = register_and_login("staging-cors-auth@example.com")
        authenticated = cors_client.get(
            "/ai/records",
            headers={**session, "Origin": "https://staging.delphiafit.example"},
        )
        assert authenticated.status_code == 200
        assert authenticated.headers["access-control-allow-origin"] == "https://staging.delphiafit.example"

        unknown_origin_request = cors_client.get(
            "/ai/records",
            headers={**session, "Origin": "https://unknown.example"},
        )
        assert unknown_origin_request.status_code == 200
        assert "access-control-allow-origin" not in unknown_origin_request.headers


@pytest.mark.parametrize(
    "origin",
    [
        "http://staging.example",
        "https://*.example.com",
        "https://user:password@staging.example",
        "https://staging.example/path",
        "https://staging.example?token=secret",
        "https://staging.example#fragment",
        "https://bad host.example",
    ],
)
def test_staging_cors_rejects_non_origin_configuration(origin):
    with pytest.raises(RuntimeError):
        normalize_staging_frontend_origin(origin)


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
    sent = []
    monkeypatch.setattr("app.routers.auth.send_user_password_reset", lambda email, token: sent.append((email, token)) or True)
    monkeypatch.setenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "true")
    email = "password-reset@example.com"
    old_session = register_and_login(email)
    request = client.post("/auth/forgot-password", json={"email": email})
    unknown_request = client.post("/auth/forgot-password", json={"email": "unknown-password-reset@example.com"})
    assert request.status_code == unknown_request.status_code == 200
    assert request.json() == unknown_request.json()
    assert "debug_token" not in request.json()
    reset = client.post("/auth/reset-password", json={"email": email, "token": sent[0][1], "new_password": "BetterPassword456!"})
    assert reset.status_code == 200, reset.text
    assert client.get("/ai/records", headers=old_session).status_code == 401
    assert client.post("/auth/reset-password", json={"email": email, "token": sent[0][1], "new_password": "AnotherPassword789!"}).status_code == 400
    assert client.post("/auth/login", json={"email": email, "password": "GoodPass123!"}).status_code == 401
    renewed = client.post("/auth/login", json={"email": email, "password": "BetterPassword456!"})
    assert renewed.status_code == 200
    renewed_headers = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    assert client.get("/ai/records", headers=renewed_headers).status_code == 200


def test_password_change_revokes_only_the_changed_account_sessions():
    changed = register_and_login("password-change-revoke@example.com")
    unaffected = register_and_login("password-change-unaffected@example.com")
    assert client.post(
        "/account/change-password",
        headers=changed,
        json={"current_password": "GoodPass123!", "new_password": "ChangedPassword456!"},
    ).status_code == 200

    assert client.get("/ai/records", headers=changed).status_code == 401
    assert client.get("/profile/get", headers=changed).status_code == 401
    assert client.get("/ai/records", headers=unaffected).status_code == 200
    renewed = client.post("/auth/login", json={
        "email": "password-change-revoke@example.com",
        "password": "ChangedPassword456!",
    })
    assert renewed.status_code == 200
    renewed_headers = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    assert client.get("/ai/records", headers=renewed_headers).status_code == 200


def test_stale_password_change_cannot_overwrite_intervening_change():
    original_session = register_and_login("stale-password-change@example.com")
    email = "stale-password-change@example.com"
    first_change = client.post(
        "/account/change-password",
        headers=original_session,
        json={"current_password": "GoodPass123!", "new_password": "FirstChange456!"},
    )
    assert first_change.status_code == 200, first_change.text

    intervening_login = client.post(
        "/auth/login",
        json={"email": email, "password": "FirstChange456!"},
    )
    assert intervening_login.status_code == 200
    intervening_session = {"Authorization": f"Bearer {intervening_login.json()['access_token']}"}

    stale_change = client.post(
        "/account/change-password",
        headers=original_session,
        json={"current_password": "GoodPass123!", "new_password": "StaleChange789!"},
    )
    assert stale_change.status_code == 401
    assert client.post(
        "/auth/login",
        json={"email": email, "password": "StaleChange789!"},
    ).status_code == 401
    assert client.post(
        "/auth/login",
        json={"email": email, "password": "FirstChange456!"},
    ).status_code == 200
    assert client.get("/ai/records", headers=intervening_session).status_code == 200


def test_password_change_commit_failure_rolls_back_credentials_and_token_version(monkeypatch, caplog):
    headers = register_and_login("password-change-rollback@example.com")
    user_id = client.get("/auth/me", headers=headers).json()["id"]
    with SessionLocal() as db:
        original_hash = db.query(User).filter(User.id == user_id).one().hashed_password
        original_version = db.query(User).filter(User.id == user_id).one().token_version

    marker = "PASSWORD-CHANGE-COMMIT-FAILURE"
    from sqlalchemy.orm import Session

    def fail_commit(_session):
        raise RuntimeError(marker)

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        response = client.post(
            "/account/change-password",
            headers=headers,
            json={"current_password": "GoodPass123!", "new_password": "RollbackPassword456!"},
        )

    assert response.status_code == 500
    assert marker not in response.text
    assert marker not in caplog.text
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).one()
        assert user.hashed_password == original_hash
        assert user.token_version == original_version
    assert client.post(
        "/auth/login",
        json={"email": "password-change-rollback@example.com", "password": "GoodPass123!"},
    ).status_code == 200
    assert client.get("/ai/records", headers=headers).status_code == 200


def test_authentication_database_exception_is_sanitized(monkeypatch, caplog):
    headers = register_and_login("auth-db-error@example.com")
    marker = "AUTH-DATABASE-SYNTHETIC-SECRET"
    from sqlalchemy.orm import Session

    original_query = Session.query

    def fail_user_lookup(session, *entities, **kwargs):
        if entities and entities[0] is User:
            raise RuntimeError(marker)
        return original_query(session, *entities, **kwargs)

    monkeypatch.setattr(Session, "query", fail_user_lookup)
    response = client.get("/ai/records", headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Authentication service temporarily unavailable"
    assert marker not in response.text
    assert marker not in caplog.text
    assert "user token validation" in caplog.text
    assert "RuntimeError" in caplog.text


def test_uvicorn_sanitizes_unhandled_authentication_exception(monkeypatch, caplog):
    headers = register_and_login("uvicorn-auth-error@example.com")
    marker = "UVICORN-AUTH-SYNTHETIC-SECRET"

    def fail_lookup(session, *entities, **kwargs):
        raise RuntimeError(marker)

    def fail_sanitizer(*_args, **_kwargs):
        raise RuntimeError(marker)

    from sqlalchemy.orm import Session
    import uvicorn

    monkeypatch.setattr(Session, "query", fail_lookup)
    monkeypatch.setattr(
        "app.auth.jwt_handler.authentication_database_error",
        fail_sanitizer,
    )
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen(128)
    port = server_socket.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=True))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [server_socket]}, daemon=True)
    thread.start()

    try:
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started, "Uvicorn did not start"
        from urllib.error import HTTPError
        from urllib.request import Request as URLRequest, urlopen

        request = URLRequest(
            f"http://127.0.0.1:{port}/ai/records",
            headers=headers,
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=5)
        response_body = error.value.read().decode("utf-8")
        assert error.value.code == 500
        assert "Internal server error" in response_body
        assert marker not in response_body
        assert marker not in caplog.text
        assert "Unhandled request failure" in caplog.text
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        server_socket.close()
    assert not thread.is_alive(), "Uvicorn server did not stop"


def test_legacy_user_password_update_revokes_session_and_rejects_other_accounts():
    own_session = register_and_login("legacy-password-update@example.com")
    other_session = register_and_login("legacy-password-update-other@example.com")
    user_id = client.get("/auth/me", headers=own_session).json()["id"]
    other_id = client.get("/auth/me", headers=other_session).json()["id"]

    denied = client.put(
        f"/users/{other_id}",
        headers=own_session,
        json={"password": "UnauthorizedPassword123!"},
    )
    assert denied.status_code == 403
    assert client.get("/ai/records", headers=other_session).status_code == 200

    changed = client.put(
        f"/users/{user_id}",
        headers=own_session,
        json={"password": "LegacyChangedPassword456!"},
    )
    assert changed.status_code == 200, changed.text
    assert client.get("/ai/records", headers=own_session).status_code == 401
    assert client.post("/auth/login", json={
        "email": "legacy-password-update@example.com",
        "password": "GoodPass123!",
    }).status_code == 401
    fresh_login = client.post("/auth/login", json={
        "email": "legacy-password-update@example.com",
        "password": "LegacyChangedPassword456!",
    })
    assert fresh_login.status_code == 200
    fresh_session = {"Authorization": f"Bearer {fresh_login.json()['access_token']}"}
    assert client.get("/ai/records", headers=fresh_session).status_code == 200


def test_legacy_user_password_update_rolls_back_credentials_and_token_version(monkeypatch):
    headers = register_and_login("legacy-password-rollback@example.com")
    user_id = client.get("/auth/me", headers=headers).json()["id"]

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).one()
        original_hash = user.hashed_password
        original_version = user.token_version

        def fail_commit():
            raise RuntimeError("synthetic commit failure")

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="synthetic commit failure"):
            update_user(db, user_id, UserUpdate(password="RollbackPassword456!"))

        db.expire_all()
        user = db.query(User).filter(User.id == user_id).one()
        assert user.hashed_password == original_hash
        assert user.token_version == original_version

    assert client.get("/ai/records", headers=headers).status_code == 200


def test_suspension_revokes_sessions_permanently_after_reinstatement():
    revoked_session = register_and_login("suspend-revoke@example.com")
    unaffected_session = register_and_login("suspend-unaffected@example.com")
    target_id = client.get("/auth/me", headers=revoked_session).json()["id"]
    register_and_login("revocation-admin@example.com")
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.email == "revocation-admin@example.com").one()
        admin_user.is_admin = True
        db.commit()
    admin_login = client.post("/admin/login", json={
        "email": "revocation-admin@example.com",
        "password": "GoodPass123!",
    })
    assert admin_login.status_code == 200, admin_login.text
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    suspended = client.patch(
        f"/admin/users/{target_id}/suspend",
        headers=admin_headers,
        json={"suspended": True},
    )
    assert suspended.status_code == 200, suspended.text
    assert client.get("/ai/records", headers=revoked_session).status_code == 401
    assert client.get("/profile/get", headers=revoked_session).status_code == 401
    assert client.get("/ai/records", headers=unaffected_session).status_code == 200

    reinstated = client.patch(
        f"/admin/users/{target_id}/suspend",
        headers=admin_headers,
        json={"suspended": False},
    )
    assert reinstated.status_code == 200, reinstated.text
    assert client.get("/ai/records", headers=revoked_session).status_code == 401
    fresh_login = client.post("/auth/login", json={
        "email": "suspend-revoke@example.com",
        "password": "GoodPass123!",
    })
    assert fresh_login.status_code == 200
    fresh_headers = {"Authorization": f"Bearer {fresh_login.json()['access_token']}"}
    assert client.get("/ai/records", headers=fresh_headers).status_code == 200


def test_password_recovery_email_links_keep_credentials_in_fragment(monkeypatch):
    sent = []
    monkeypatch.setattr(email_delivery, "_send_email", lambda address, subject, body: sent.append(body) or True)
    monkeypatch.setenv("FRONTEND_URL", "https://www.delphiafit.com")
    email_delivery.send_user_password_reset("athlete+test@example.com", "user-token")
    email_delivery.send_coach_password_reset("coach+test@example.com", "coach-token")

    user_url = next(line for line in sent[0].splitlines() if line.startswith("https://"))
    coach_url = next(line for line in sent[1].splitlines() if line.startswith("https://"))
    assert urlparse(user_url).path == "/reset-password"
    assert urlparse(user_url).query == ""
    assert parse_qs(urlparse(user_url).fragment) == {"email": ["athlete+test@example.com"], "token": ["user-token"]}
    assert urlparse(coach_url).path == "/coach/password-reset"
    assert urlparse(coach_url).query == ""
    assert parse_qs(urlparse(coach_url).fragment) == {"email": ["coach+test@example.com"], "token": ["coach-token"]}


def test_user_password_reset_rejects_expired_token(monkeypatch):
    sent = []
    monkeypatch.setattr("app.routers.auth.send_user_password_reset", lambda email, token: sent.append((email, token)) or True)
    email = "expired-reset@example.com"
    register_and_login(email)
    assert client.post("/auth/forgot-password", json={"email": email}).status_code == 200
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.password_reset_expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    assert client.post("/auth/reset-password", json={"email": email, "token": sent[0][1], "new_password": "BetterPassword456!"}).status_code == 400


def test_profile_date_of_birth_round_trips_as_iso_date():
    email = "profile-dob@example.com"
    headers = register_and_login(email)
    response = client.post("/profile/update", headers=headers, json={"dob": "1992-03-04"})
    assert response.status_code == 200, response.text
    assert response.json()["dob"] == "1992-03-04"

    renewed = client.post("/auth/login", json={"email": email, "password": "GoodPass123!"})
    assert renewed.status_code == 200
    refreshed_session = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    loaded = client.get("/profile/get", headers=refreshed_session)
    assert loaded.status_code == 200
    assert loaded.json()["dob"] == "1992-03-04"
    assert client.post("/profile/update", headers=headers, json={"dob": "2027-01-01"}).status_code == 422
    assert client.post("/profile/update", headers=headers, json={"dob": "03/04/1992"}).status_code == 422


def test_profile_date_of_birth_can_be_cleared():
    headers = register_and_login("profile-dob-clear@example.com")
    assert client.post("/profile/update", headers=headers, json={"dob": "1992-03-04"}).status_code == 200
    cleared = client.post("/profile/update", headers=headers, json={"dob": ""})
    assert cleared.status_code == 200
    assert cleared.json()["dob"] is None


def test_pro_area_migrations_are_idempotent():
    run_migrations()
    run_migrations()

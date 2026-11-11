"""Trainer/client authorization and opt-in workflows remain separate from Coach Hub."""
import os
import tempfile
import uuid

_db_path = os.path.join(tempfile.mkdtemp(), "trainer_access.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["JWT_SECRET"] = "trainer-tests-only-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

from app.auth.jwt_handler import create_access_token  # noqa: E402
from app.database.connection import SessionLocal, engine  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.trainer import TrainerClientLink  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.workout_log import WorkoutLog  # noqa: E402
from app.routers import trainer as trainer_router  # noqa: E402

run_migrations()
http = TestClient(app)


def make_user(*, admin=False):
    email = f"trainer-test-{uuid.uuid4().hex}@example.com"
    with SessionLocal() as db:
        row = User(name="Tester " + email[:6], email=email, hashed_password="test-hash", is_admin=admin)
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "email": row.email, "name": row.name, "admin": admin}


def auth(user, *, as_coach=False):
    data = {
        "sub": str(user["id"]),
        "email": user["email"],
        "actor_type": "coach" if as_coach else "user",
        "token_version": 0,
    }
    if user["admin"]:
        data["is_admin"] = True
    return {"Authorization": "Bearer " + create_access_token(data)}


def grant(user, admin, enabled=True):
    return http.put(f"/admin/users/{user['id']}/trainer", json={"enabled": enabled}, headers=auth(admin))


def test_migration_creates_trainer_tables_idempotently():
    run_migrations()
    tables = set(inspect(engine).get_table_names())
    assert {"trainer_profiles", "trainer_client_links"} <= tables
    run_migrations()
    assert {"trainer_profiles", "trainer_client_links"} <= set(inspect(engine).get_table_names())


def test_only_owner_admin_may_grant_trainer_and_role_is_not_self_assigned():
    member = make_user()
    admin = make_user(admin=True)
    assert http.get("/trainer/me", headers=auth(member)).json() == {"is_trainer": False}
    assert http.get("/trainer/clients", headers=auth(member)).status_code == 403
    assert http.put(f"/admin/users/{member['id']}/trainer", json={"enabled": True}, headers=auth(member)).status_code == 403
    assert http.get("/trainer/me", headers=auth(member, as_coach=True)).status_code == 403

    assert grant(member, admin).status_code == 200
    assert http.get("/trainer/me", headers=auth(member)).json() == {"is_trainer": True}
    details = http.get(f"/admin/users/{member['id']}", headers=auth(admin))
    assert details.status_code == 200
    assert details.json()["is_trainer"] is True
    listing = http.get("/admin/users", headers=auth(admin))
    assert listing.status_code == 200
    assert any(row["id"] == member["id"] and row["is_trainer"] for row in listing.json())
    assert grant(member, admin, enabled=False).status_code == 200
    assert http.get("/trainer/me", headers=auth(member)).json() == {"is_trainer": False}
    details = http.get(f"/admin/users/{member['id']}", headers=auth(admin))
    assert details.json()["is_trainer"] is False


def test_client_consent_required_and_trainer_data_scoped(monkeypatch):
    monkeypatch.setattr(trainer_router, "send_trainer_invitation", lambda email, name: False)
    admin = make_user(admin=True)
    trainer = make_user()
    other_trainer = make_user()
    client = make_user()
    outsider = make_user()
    assert grant(trainer, admin).status_code == 200
    assert grant(other_trainer, admin).status_code == 200

    with SessionLocal() as db:
        db.add(WorkoutLog(user_id=client["id"], mode="manual", duration_minutes=30, manual_name="Client strength"))
        db.commit()

    response = http.post("/trainer/clients/invite", json={"email": client["email"]}, headers=auth(trainer))
    assert response.status_code == 201
    assert response.json()["status"] == "pending"

    # Pending invitations must not expose the client's workout history.
    assert http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(trainer)).status_code == 404
    assert http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(other_trainer)).status_code == 404
    assert http.get("/trainer/clients", headers=auth(outsider)).status_code == 403
    invitations = http.get("/trainer/invitations", headers=auth(client)).json()["invitations"]
    assert len(invitations) == 1
    invite_id = invitations[0]["id"]

    assert http.post(f"/trainer/invitations/{invite_id}/accept", headers=auth(outsider)).status_code == 404
    assert http.post(f"/trainer/invitations/{invite_id}/accept", headers=auth(client)).status_code == 200
    assert http.post(f"/trainer/invitations/{invite_id}/accept", headers=auth(client)).status_code == 404

    active = http.get("/trainer/clients", headers=auth(trainer)).json()["clients"]
    assert any(c["id"] == client["id"] and c["status"] == "active" for c in active)
    result = http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(trainer))
    assert result.status_code == 200
    assert result.json()["workouts"][0]["name"] == "Client strength"
    assert http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(other_trainer)).status_code == 404

    linked = http.get("/trainer/my-trainers", headers=auth(client)).json()["trainers"]
    assert len(linked) == 1 and linked[0]["id"] == trainer["id"]
    assert http.delete(f"/trainer/my-trainers/{trainer['id']}", headers=auth(outsider)).status_code == 404
    assert http.delete(f"/trainer/my-trainers/{trainer['id']}", headers=auth(client)).status_code == 200
    assert http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(trainer)).status_code == 404


def test_invitation_decline_and_uninvited_user_rejected(monkeypatch):
    monkeypatch.setattr(trainer_router, "send_trainer_invitation", lambda email, name: False)
    admin = make_user(admin=True)
    trainer = make_user()
    client = make_user()
    assert grant(trainer, admin).status_code == 200
    response = http.post("/trainer/clients/invite", json={"email": client["email"]}, headers=auth(trainer))
    assert response.status_code == 201
    with SessionLocal() as db:
        link = db.query(TrainerClientLink).filter_by(
            trainer_user_id=trainer["id"], client_user_id=client["id"]
        ).one()
        invitation_id = link.id
    assert http.post(f"/trainer/invitations/{invitation_id}/decline", headers=auth(client)).status_code == 200
    assert http.get("/trainer/invitations", headers=auth(client)).json()["invitations"] == []
    assert http.get(f"/trainer/clients/{client['id']}/progress", headers=auth(trainer)).status_code == 404

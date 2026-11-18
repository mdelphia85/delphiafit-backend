import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.database import migrate
from app.database.connection import Base
from app.models.coach import Coach
from app.models.instructor import Instructor
from app.models.user import User
from sqlalchemy.orm import Session


def test_empty_database_creates_coach_hub_after_foreign_key_dependencies(monkeypatch, tmp_path):
    database = tmp_path / "empty.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)

    migrate.run_migrations()

    tables = set(inspect(test_engine).get_table_names())
    assert {
        "coaches", "clients", "plans", "coach_messages", "plan_assignments",
        "academy_programs", "academy_progress", "competitions", "competition_registrations",
        "federations", "federation_memberships", "ai_records",
    } <= tables
    assert "uq_ai_records_user_id_idempotency_key" in {
        index["name"] for index in inspect(test_engine).get_indexes("ai_records")
    }
    assert {"coaches", "clients", "plans"} <= set(Base.metadata.tables)
    test_engine.dispose()


def test_coach_hub_migration_is_idempotent_and_preserves_existing_rows(monkeypatch, tmp_path):
    database = tmp_path / "existing.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)

    migrate.run_migrations()
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO users (name, email, hashed_password, streak, is_suspended) VALUES (?, ?, ?, ?, ?)",
            ("Existing", "existing@example.com", "already-hashed", 0, False),
        )
    migrate.run_migrations()

    with test_engine.connect() as connection:
        row = connection.exec_driver_sql("SELECT name, email FROM users").one()
    assert row == ("Existing", "existing@example.com")
    test_engine.dispose()


def test_user_token_version_migration_preserves_accounts_and_defaults_existing_sessions(monkeypatch, tmp_path):
    database = tmp_path / "legacy-users.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)

    with test_engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, email VARCHAR NOT NULL, "
            "hashed_password VARCHAR NOT NULL, streak INTEGER DEFAULT 0)"
        ))
        connection.execute(text(
            "INSERT INTO users (id, name, email, hashed_password, streak) "
            "VALUES (9, 'Existing user', 'preserve@example.com', 'existing-hash', 4)"
        ))

    migrate.migrate_users()
    migrate.migrate_users()

    with test_engine.connect() as connection:
        row = connection.execute(text(
            "SELECT id, email, hashed_password, streak, token_version FROM users WHERE id = 9"
        )).one()
    assert row == (9, "preserve@example.com", "existing-hash", 4, 0)
    test_engine.dispose()


def test_coach_token_version_migration_preserves_coaches_and_defaults_existing_sessions(monkeypatch, tmp_path):
    database = tmp_path / "legacy-coaches.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)

    with test_engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE coaches (id INTEGER PRIMARY KEY, email VARCHAR NOT NULL, name VARCHAR NOT NULL, "
            "role VARCHAR, is_active BOOLEAN)"
        ))
        connection.execute(text(
            "INSERT INTO coaches (id, email, name, role, is_active) "
            "VALUES (12, 'preserve-coach@example.com', 'Existing coach', 'coach', TRUE)"
        ))

    migrate.migrate_coaches()
    migrate.migrate_coaches()

    with test_engine.connect() as connection:
        row = connection.execute(text(
            "SELECT id, email, name, token_version FROM coaches WHERE id = 12"
        )).one()
    assert row == (12, "preserve-coach@example.com", "Existing coach", 0)
    test_engine.dispose()


def test_legacy_instructor_ownership_is_backfilled_only_by_matching_account_email(monkeypatch, tmp_path):
    database = tmp_path / "legacy.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)
    Base.metadata.create_all(bind=test_engine)

    with Session(test_engine) as db:
        db.add_all([
            User(id=1, name="Legacy user", email="legacy@example.com", hashed_password="hash"),
            User(id=2, name="Linked user", email="linked@example.com", hashed_password="hash"),
            Coach(id=1, name="Different coach", email="different@example.com", role="coach", is_active=True),
            Coach(id=5, name="Linked coach", email="linked@example.com", role="coach", is_active=True),
            Instructor(id=1, user_id=1, agency="fire", role="legacy user"),
            Instructor(id=2, user_id=2, agency="fire", role="linked coach"),
        ])
        db.commit()

    migrate.migrate_instructor_owners()
    with Session(test_engine) as db:
        assert db.query(Instructor).filter_by(id=1).one().owner_coach_id is None
        assert db.query(Instructor).filter_by(id=2).one().owner_coach_id == 5
    test_engine.dispose()


def test_ai_idempotency_migration_adds_unique_index_and_preserves_existing_records(monkeypatch, tmp_path):
    database = tmp_path / "legacy-ai-records.db"
    test_engine = create_engine(f"sqlite:///{database}")
    monkeypatch.setattr(migrate, "engine", test_engine)

    with test_engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE ai_records ("
            "id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, feature VARCHAR NOT NULL, "
            "input_json TEXT NOT NULL, result_json TEXT NOT NULL, created_at TIMESTAMP NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO ai_records (id, user_id, feature, input_json, result_json, created_at) "
            "VALUES (1, 7, 'coach', '{}', '{\"coach_response\":\"existing\"}', CURRENT_TIMESTAMP)"
        ))

    migrate.migrate_ai_idempotency()
    migrate.migrate_ai_idempotency()

    with test_engine.begin() as connection:
        row = connection.execute(text(
            "SELECT user_id, feature, result_json, idempotency_key FROM ai_records WHERE id = 1"
        )).one()
        connection.execute(text(
            "INSERT INTO ai_records (user_id, feature, input_json, result_json, created_at, idempotency_key) "
            "VALUES (7, 'coach', '{}', '{}', CURRENT_TIMESTAMP, 'request-key')"
        ))
        connection.execute(text(
            "INSERT INTO ai_records (user_id, feature, input_json, result_json, created_at, idempotency_key) "
            "VALUES (8, 'coach', '{}', '{}', CURRENT_TIMESTAMP, 'request-key')"
        ))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(text(
                "INSERT INTO ai_records (user_id, feature, input_json, result_json, created_at, idempotency_key) "
                "VALUES (7, 'coach', '{}', '{}', CURRENT_TIMESTAMP, 'request-key')"
            ))

    assert row == (7, "coach", '{"coach_response":"existing"}', None)
    test_engine.dispose()

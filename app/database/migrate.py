"""Small idempotent schema migration runner for DelphiaFit.

This project predates a formal migration framework. Railway runs this module as a
pre-deploy command so existing production tables can be upgraded before the new
application process starts. New tables are then created from SQLAlchemy metadata.
"""

from sqlalchemy import inspect, text

from app import models as _models  # noqa: F401 - registers all model metadata
from app.database.connection import Base, engine


WORKOUT_COLUMNS = {
    "mode": "VARCHAR",
    "manual_name": "VARCHAR",
    "manual_notes": "VARCHAR",
    "weight_unit": "VARCHAR",
    "weight_value": "INTEGER",
    "plan_json": "JSON",
    "block_durations_json": "JSON",
    "equipment_json": "JSON",
}


def migrate_workout_logs() -> None:
    """Upgrade the legacy workout_logs table to the V2 shape when it exists."""
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "workout_logs" not in inspector.get_table_names():
            return

        existing = {column["name"] for column in inspector.get_columns("workout_logs")}
        for name, sql_type in WORKOUT_COLUMNS.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE workout_logs ADD COLUMN {name} {sql_type}"))

        # Existing V1 rows were all structured workouts.
        conn.execute(text("UPDATE workout_logs SET mode = 'structured' WHERE mode IS NULL"))

        if engine.dialect.name == "postgresql":
            # V2 supports manual workouts, so workout_type must be optional.
            conn.execute(text("ALTER TABLE workout_logs ALTER COLUMN workout_type DROP NOT NULL"))
            conn.execute(text("ALTER TABLE workout_logs ALTER COLUMN mode SET NOT NULL"))



def migrate_users() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "users" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "streak" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0"))
        conn.execute(text("UPDATE users SET streak = 0 WHERE streak IS NULL"))
        if "password_reset_token_hash" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token_hash VARCHAR"))
        if "password_reset_expires_at" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP"))
        if engine.dialect.name == "postgresql":
            conn.execute(text("ALTER TABLE users ALTER COLUMN streak SET DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN streak SET NOT NULL"))


def migrate_coaches() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "coaches" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("coaches")}
        additions = {
            "hashed_password": "VARCHAR",
            "password_reset_token_hash": "VARCHAR",
            "password_reset_expires_at": "TIMESTAMP",
        }
        for name, sql_type in additions.items():
            if name not in columns:
                conn.execute(text(f"ALTER TABLE coaches ADD COLUMN {name} {sql_type}"))


def migrate_daily_logs() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "daily_logs" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("daily_logs")}
        for name in ("protein", "water", "calories", "meals", "workouts", "supplements"):
            if name not in columns:
                conn.execute(text(f"ALTER TABLE daily_logs ADD COLUMN {name} FLOAT DEFAULT 0"))


def migrate_personal_records() -> None:
    """Add the optional notes field introduced by the repaired PR API contract."""
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "personal_records" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("personal_records")}
        if "notes" not in columns:
            conn.execute(text("ALTER TABLE personal_records ADD COLUMN notes VARCHAR"))



def migrate_tactical_drills() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "tactical_drills" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("tactical_drills")}
        if "user_id" not in columns:
            conn.execute(text("ALTER TABLE tactical_drills ADD COLUMN user_id INTEGER"))


def run_migrations() -> None:
    migrate_workout_logs()
    migrate_users()
    migrate_coaches()
    migrate_daily_logs()
    migrate_personal_records()
    migrate_tactical_drills()
    # Creates all new V2 tables without dropping or replacing existing data.
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    run_migrations()
    print(f"Database migration complete ({len(Base.metadata.tables)} registered tables).")

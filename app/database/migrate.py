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
        if "completed" not in columns:
            conn.execute(text("ALTER TABLE tactical_drills ADD COLUMN completed BOOLEAN NOT NULL DEFAULT FALSE"))


def migrate_user_profiles() -> None:
    """Add nullable nutrition inputs to user_profiles without touching existing data."""
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "user_profiles" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("user_profiles")}
        for name in ("sex", "activity_level"):
            if name not in columns:
                conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {name} VARCHAR"))


def migrate_coach_hub() -> None:
    """Create the Coach Hub tables (messages, plan assignments) if they are missing.

    Purely additive: existing tables and rows are never altered.
    """
    from app.models.coach_message import CoachMessage
    from app.models.plan_assignment import PlanAssignment

    for model in (CoachMessage, PlanAssignment):
        model.__table__.create(bind=engine, checkfirst=True)


def migrate_admin_system() -> None:
    """Additive columns for user suspension and announcement publishing."""
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if "users" in tables:
            columns = {c["name"] for c in inspector.get_columns("users")}
            if "is_suspended" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_suspended BOOLEAN NOT NULL DEFAULT FALSE"))
            if "suspended_at" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN suspended_at TIMESTAMP"))
        if "announcements" in tables:
            columns = {c["name"] for c in inspector.get_columns("announcements")}
            if "is_active" not in columns:
                # Existing announcements were visible immediately, so they stay published.
                conn.execute(text("ALTER TABLE announcements ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
            for name, sql_type in (("published_at", "TIMESTAMP"), ("updated_at", "TIMESTAMP"), ("created_by", "INTEGER")):
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE announcements ADD COLUMN {name} {sql_type}"))
            if "published_at" not in columns:
                conn.execute(text("UPDATE announcements SET published_at = created_at WHERE is_active AND published_at IS NULL"))


def migrate_org_memberships() -> None:
    """Create the additive organization ownership/role table if it is missing."""
    from app.models.org_membership import OrganizationMembership

    OrganizationMembership.__table__.create(bind=engine, checkfirst=True)


def migrate_ai_records() -> None:
    """Create the additive table used to persist authenticated rule-based AI outputs."""
    from app.models.ai_record import AIRecord

    AIRecord.__table__.create(bind=engine, checkfirst=True)



def migrate_community_area() -> None:
    """Create new community persistence tables and add nullable competition ownership."""
    from app.models.community_area import (
        AcademyProgress, CompetitionRegistration, FederationMembership, RecruitingProfile,
        ListingInterest, ChildProfile, ChildProgress, SocialFollow,
    )

    for model in (AcademyProgress, CompetitionRegistration, FederationMembership, RecruitingProfile,
                  ListingInterest, ChildProfile, ChildProgress, SocialFollow):
        model.__table__.create(bind=engine, checkfirst=True)
    with engine.begin() as conn:
        for table in ("competitions", "seasons"):
            if table in inspect(conn).get_table_names():
                columns = {column["name"] for column in inspect(conn).get_columns(table)}
                if "owner_id" not in columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN owner_id INTEGER"))




def migrate_tactical_owners() -> None:
    """Add explicit account ownership to tactical operation records."""
    tables = {
        "k9_units": "owner_user_id",
        "search_rescue_operations": "owner_user_id",
        "disaster_operations": "owner_user_id",
        "maritime_operations": "owner_user_id",
        "aviation_operations": "owner_user_id",
        "hazmat_operations": "owner_user_id",
        "wildland_operations": "owner_user_id",
    }
    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        for table, column in tables.items():
            if table not in existing_tables:
                continue
            columns = {item["name"] for item in inspector.get_columns(table)}
            if column not in columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER"))




def migrate_prep_pipeline_owners() -> None:
    """Add account owners to user-created SOF and SWAT preparation pipelines."""
    with engine.begin() as conn:
        inspector = inspect(conn)
        for table in ("sof_pipelines", "swat_pipelines"):
            if table not in inspector.get_table_names():
                continue
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "owner_user_id" not in columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN owner_user_id INTEGER"))


def run_migrations() -> None:
    migrate_workout_logs()
    migrate_users()
    migrate_coaches()
    migrate_daily_logs()
    migrate_personal_records()
    migrate_tactical_drills()
    migrate_user_profiles()
    migrate_admin_system()
    migrate_coach_hub()
    migrate_tactical_owners()
    migrate_prep_pipeline_owners()
    migrate_community_area()
    # Creates all new V2 tables without dropping or replacing existing data.
    Base.metadata.create_all(bind=engine)
    migrate_org_memberships()
    migrate_ai_records()


if __name__ == "__main__":
    run_migrations()
    print(f"Database migration complete ({len(Base.metadata.tables)} registered tables).")

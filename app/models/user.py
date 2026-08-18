from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    streak = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    password_reset_token_hash = Column(String, nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # ---------------------------------------------------------
    # Social + Community Relationships
    # ---------------------------------------------------------

    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    challenges = relationship("Challenge", back_populates="user", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="user", cascade="all, delete-orphan")

    # Leaderboards will reference User but do not require a
    # relationship here unless you want direct back_populates.
    # If needed later:
    # leaderboard_entries = relationship("LeaderboardEntry", back_populates="user")
    # User-owned V2 records. Cascades keep account deletion referentially valid.
    periodization_blocks = relationship("PeriodizationBlock", cascade="all, delete-orphan")
    strength_metrics = relationship("StrengthMetric", cascade="all, delete-orphan")
    meals = relationship("Meal", cascade="all, delete-orphan")
    goals = relationship("Goal", cascade="all, delete-orphan")
    rep_logs = relationship("RepLog", cascade="all, delete-orphan")
    macro_plans = relationship("MacroPlan", cascade="all, delete-orphan")
    personal_records = relationship("PersonalRecord", cascade="all, delete-orphan")
    progress_snapshots = relationship("ProgressSnapshot", cascade="all, delete-orphan")
    recovery_logs = relationship("RecoveryLog", cascade="all, delete-orphan")
    nutrition_logs = relationship("NutritionLog", cascade="all, delete-orphan")
    recipes = relationship("Recipe", cascade="all, delete-orphan")


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ---------------------------------------------------------
    # Social + Community Relationships
    # ---------------------------------------------------------

    achievements = relationship("Achievement", back_populates="user")
    streaks = relationship("Streak", back_populates="user")
    challenges = relationship("Challenge", back_populates="user")
    group_memberships = relationship("GroupMember", back_populates="user")
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    reactions = relationship("Reaction", back_populates="user")

    # Leaderboards will reference User but do not require a
    # relationship here unless you want direct back_populates.
    # If needed later:
    # leaderboard_entries = relationship("LeaderboardEntry", back_populates="user")

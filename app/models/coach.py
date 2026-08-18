from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base   # ← FIXED


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    organization = Column(String, nullable=True)
    role = Column(String, default="coach")  # head_coach, assistant, recruiter, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teams = relationship("Team", back_populates="coach")
    invites = relationship("Invite", back_populates="coach")

    # NEW relationships required for Phase 4
    clients = relationship("Client", back_populates="coach")
    plans = relationship("Plan", back_populates="coach")
    drills = relationship("Drill", back_populates="coach")
    schedules = relationship("Schedule", back_populates="coach")
    recruits = relationship("Recruit", back_populates="coach")

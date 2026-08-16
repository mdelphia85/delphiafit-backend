from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)

    name = Column(String, nullable=False)
    sport = Column(String, nullable=True)           # football, soccer, basketball, etc.
    level = Column(String, nullable=True)           # varsity, JV, U18, club, etc.
    organization = Column(String, nullable=True)    # school, club, academy
    season = Column(String, nullable=True)          # fall, spring, year-round

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coach = relationship("Coach", back_populates="teams")
    clients = relationship("Client", back_populates="team")

    schedules = relationship("Schedule", back_populates="team")
    recruits = relationship("Recruit", back_populates="team")
    invites = relationship("Invite", back_populates="team")

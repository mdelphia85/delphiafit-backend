from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=True)        # athlete position (RB, WR, GK, etc.)
    level = Column(String, nullable=True)           # varsity, JV, U18, etc.
    status = Column(String, default="active")       # active, injured, suspended, etc.

    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    coach = relationship("Coach", back_populates="clients")
    team = relationship("Team", back_populates="clients")

    plans = relationship("Plan", back_populates="client")
    schedules = relationship("Schedule", back_populates="client")
    recruits = relationship("Recruit", back_populates="client")

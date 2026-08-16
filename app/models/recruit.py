from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Recruit(Base):
    __tablename__ = "recruits"

    id = Column(Integer, primary_key=True, index=True)

    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    # client_id becomes non-null once the recruit officially joins

    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    position = Column(String, nullable=True)        # WR, RB, GK, etc.
    level = Column(String, nullable=True)           # U18, varsity, club, etc.

    status = Column(String, default="contacted")
    # contacted, evaluating, interested, offer_sent, committed, declined

    evaluation_score = Column(Integer, nullable=True)
    # 1–100 rating assigned by coach

    notes = Column(Text, nullable=True)
    # scouting notes, strengths, weaknesses, etc.

    last_contacted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coach = relationship("Coach", back_populates="recruits")
    team = relationship("Team", back_populates="recruits")
    client = relationship("Client", back_populates="recruits")

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.database.connection import Base


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)

    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    email = Column(String, nullable=False)
    role = Column(String, default="client")  
    # client, assistant_coach, recruiter, analyst, etc.

    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coach = relationship("Coach", back_populates="invites")
    team = relationship("Team", back_populates="invites")

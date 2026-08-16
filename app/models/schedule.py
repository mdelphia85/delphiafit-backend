from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)

    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    session_type = Column(String, default="practice")
    # practice, workout, meeting, film, rehab, assessment, etc.

    location = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    recurring = Column(Boolean, default=False)
    recurring_rule = Column(String, nullable=True)
    # e.g., "weekly", "biweekly", "monthly"

    attendance_required = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coach = relationship("Coach", back_populates="schedules")
    team = relationship("Team", back_populates="schedules")
    client = relationship("Client", back_populates="schedules")

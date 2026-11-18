from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)

    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    plan_type = Column(String, default="workout")  
    # workout, practice, drill_plan, development_plan, rehab_plan, etc.

    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    # JSON-like text block for plan structure (frontend parses)
    content = Column(Text, nullable=True)
    # Example:
    # {
    #   "warmup": [...],
    #   "main_sets": [...],
    #   "conditioning": [...],
    #   "cooldown": [...]
    # }

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coach = relationship("Coach", back_populates="plans")
    client = relationship("Client", back_populates="plans")
    team = relationship("Team", back_populates="plans")

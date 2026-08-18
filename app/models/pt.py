from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class PTPlan(Base):
    __tablename__ = "pt_plans"

    id = Column(Integer, primary_key=True, index=True)

    injury_id = Column(Integer, ForeignKey("injuries.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frequency_per_week = Column(Integer, default=3)
    duration_weeks = Column(Integer, default=4)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    injury = relationship("Injury", back_populates="pt_plans")

from sqlalchemy import Column, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class RecoveryProgress(Base):
    __tablename__ = "recovery_progress"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("recovery_stages.id"), nullable=False)
    user_id = Column(Integer, nullable=False)

    completed = Column(Boolean, default=False)
    clinician_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    stage = relationship("RecoveryStage", back_populates="progress")

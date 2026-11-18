from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class RecoveryProtocol(Base):
    __tablename__ = "recovery_protocols"

    id = Column(Integer, primary_key=True, index=True)
    injury_id = Column(Integer, ForeignKey("injuries.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    stages = relationship("RecoveryStage", back_populates="protocol")

    injury = relationship("Injury", back_populates="recovery_protocols")

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Injury(Base):
    __tablename__ = "injuries"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # sprain, fracture, strain, concussion, etc.
    severity = Column(String, nullable=False)  # mild, moderate, severe
    description = Column(Text, nullable=True)

    occurred_at = Column(DateTime, nullable=False)
    resolved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    pt_plans = relationship("PTPlan", back_populates="injury")
    recovery_protocols = relationship("RecoveryProtocol", back_populates="injury")

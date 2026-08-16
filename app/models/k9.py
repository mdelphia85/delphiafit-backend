from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class K9(Base):
    __tablename__ = "k9_units"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    breed = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    agency = Column(String, nullable=True)

    specialty = Column(String, nullable=True)  # tracking, detection, patrol, SAR
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    deployments = relationship("K9Deployment", back_populates="k9")


class K9Deployment(Base):
    __tablename__ = "k9_deployments"

    id = Column(Integer, primary_key=True, index=True)

    k9_id = Column(Integer, ForeignKey("k9_units.id"), nullable=False)
    handler_id = Column(Integer, nullable=False)

    mission_type = Column(String, nullable=False)  # tracking, detection, SAR, patrol
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    k9 = relationship("K9", back_populates="deployments")

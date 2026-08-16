from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class HazmatOperation(Base):
    __tablename__ = "hazmat_operations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)  # chemical, biological, radiological, nuclear, hazmat
    location = Column(String, nullable=True)
    threat_level = Column(String, nullable=True)    # low, moderate, high, critical
    status = Column(String, default="active")       # active, contained, completed, aborted

    incident_commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    zones = relationship("HazmatZone", back_populates="operation")
    exposures = relationship("HazmatExposure", back_populates="operation")
    resources = relationship("HazmatResource", back_populates="operation")


class HazmatZone(Base):
    __tablename__ = "hazmat_zones"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("hazmat_operations.id"), nullable=False)
    zone_type = Column(String, nullable=False)      # hot, warm, cold
    description = Column(Text, nullable=True)
    status = Column(String, default="active")       # active, cleared, restricted

    operation = relationship("HazmatOperation", back_populates="zones")


class HazmatResource(Base):
    __tablename__ = "hazmat_resources"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("hazmat_operations.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # PPE, decon unit, monitor, team, vehicle
    quantity = Column(Integer, default=1)
    assigned_zone = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    operation = relationship("HazmatOperation", back_populates="resources")


class HazmatExposure(Base):
    __tablename__ = "hazmat_exposures"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("hazmat_operations.id"), nullable=False)
    responder_id = Column(Integer, nullable=False)
    exposure_type = Column(String, nullable=False)  # chemical, biological, radiological
    severity = Column(String, nullable=True)        # mild, moderate, severe, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    operation = relationship("HazmatOperation", back_populates="exposures")

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class WildlandOperation(Base):
    __tablename__ = "wildland_operations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    fire_type = Column(String, nullable=False)  # brush, forest, grass, interface
    location = Column(String, nullable=True)
    containment = Column(Float, default=0.0)     # percent containment
    status = Column(String, default="active")    # active, contained, controlled, completed

    incident_commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    divisions = relationship("WildlandDivision", back_populates="operation")
    resources = relationship("WildlandResource", back_populates="operation")
    events = relationship("WildlandEvent", back_populates="operation")


class WildlandDivision(Base):
    __tablename__ = "wildland_divisions"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("wildland_operations.id"), nullable=False)
    name = Column(String, nullable=False)  # Division A, Division Z, etc.
    status = Column(String, default="active")  # active, cleared, inaccessible
    notes = Column(Text, nullable=True)

    operation = relationship("WildlandOperation", back_populates="divisions")


class WildlandResource(Base):
    __tablename__ = "wildland_resources"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("wildland_operations.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # engine, crew, dozer, tender, helo, air tanker
    quantity = Column(Integer, default=1)
    assigned_division = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    operation = relationship("WildlandOperation", back_populates="resources")


class WildlandEvent(Base):
    __tablename__ = "wildland_events"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("wildland_operations.id"), nullable=False)
    event_type = Column(String, nullable=False)  # spot_fire, slopover, wind_shift, injury, structure_loss
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=True)     # minor, moderate, severe, critical
    timestamp = Column(DateTime, default=datetime.utcnow)

    operation = relationship("WildlandOperation", back_populates="events")

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class MaritimeOperation(Base):
    __tablename__ = "maritime_operations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)  # rescue, interdiction, boarding, dive, patrol
    vessel = Column(String, nullable=True)
    location = Column(String, nullable=True)
    sea_state = Column(String, nullable=True)  # calm, moderate, rough, severe
    status = Column(String, default="active")  # active, completed, aborted

    commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    crew = relationship("MaritimeCrew", back_populates="operation")
    incidents = relationship("MaritimeIncident", back_populates="operation")


class MaritimeCrew(Base):
    __tablename__ = "maritime_crew"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("maritime_operations.id"), nullable=False)
    role = Column(String, nullable=False)  # coxswain, rescue swimmer, engineer, boarding officer
    member_name = Column(String, nullable=False)
    certification = Column(String, nullable=True)

    operation = relationship("MaritimeOperation", back_populates="crew")


class MaritimeIncident(Base):
    __tablename__ = "maritime_incidents"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("maritime_operations.id"), nullable=False)
    incident_type = Column(String, nullable=False)  # man_overboard, mechanical_failure, hazard, contact
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=True)  # minor, moderate, severe, critical
    timestamp = Column(DateTime, default=datetime.utcnow)

    operation = relationship("MaritimeOperation", back_populates="incidents")

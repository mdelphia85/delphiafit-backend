from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class AviationOperation(Base):
    __tablename__ = "aviation_operations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)  # medevac, SAR, patrol, insertion, extraction
    aircraft = Column(String, nullable=True)         # helo, fixed-wing, UAV, etc.
    location = Column(String, nullable=True)
    status = Column(String, default="active")        # active, completed, aborted

    mission_commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    crew = relationship("AviationCrew", back_populates="operation")
    events = relationship("AviationEvent", back_populates="operation")


class AviationCrew(Base):
    __tablename__ = "aviation_crew"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("aviation_operations.id"), nullable=False)
    role = Column(String, nullable=False)           # pilot, co-pilot, crew chief, medic, AO
    member_name = Column(String, nullable=False)
    certification = Column(String, nullable=True)

    operation = relationship("AviationOperation", back_populates="crew")


class AviationEvent(Base):
    __tablename__ = "aviation_events"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("aviation_operations.id"), nullable=False)
    event_type = Column(String, nullable=False)     # takeoff, landing, hoist, insertion, extraction, emergency
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=True)        # info, minor, major, critical
    timestamp = Column(DateTime, default=datetime.utcnow)

    operation = relationship("AviationOperation", back_populates="events")

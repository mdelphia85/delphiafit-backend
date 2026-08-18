from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class DisasterOperation(Base):
    __tablename__ = "disaster_operations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # flood, earthquake, hurricane, wildfire, tornado, etc.
    location = Column(String, nullable=True)
    severity = Column(String, nullable=True)  # minor, moderate, major, catastrophic
    status = Column(String, default="active")  # active, contained, completed, aborted

    incident_commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    sectors = relationship("DisasterSector", back_populates="operation")
    resources = relationship("DisasterResource", back_populates="operation")


class DisasterSector(Base):
    __tablename__ = "disaster_sectors"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("disaster_operations.id"), nullable=False)
    name = Column(String, nullable=False)  # north sector, downtown, riverfront, etc.
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, cleared, inaccessible

    operation = relationship("DisasterOperation", back_populates="sectors")


class DisasterResource(Base):
    __tablename__ = "disaster_resources"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("disaster_operations.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # USAR team, engine, medic unit, boat, helo, etc.
    quantity = Column(Integer, default=1)
    assigned_sector = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    operation = relationship("DisasterOperation", back_populates="resources")

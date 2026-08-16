from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class SearchRescue(Base):
    __tablename__ = "search_rescue_operations"

    id = Column(Integer, primary_key=True, index=True)

    operation_name = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)  # wilderness, urban, water, rope, collapsed
    location = Column(String, nullable=True)
    status = Column(String, default="active")  # active, completed, aborted

    commander_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    teams = relationship("SARTeam", back_populates="operation")
    victims = relationship("SARVictim", back_populates="operation")


class SARTeam(Base):
    __tablename__ = "sar_teams"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("search_rescue_operations.id"), nullable=False)
    team_name = Column(String, nullable=False)
    members = Column(Text, nullable=True)  # JSON list of names or IDs
    specialty = Column(String, nullable=True)  # rope, canine, medical, extraction

    operation = relationship("SearchRescue", back_populates="teams")


class SARVictim(Base):
    __tablename__ = "sar_victims"

    id = Column(Integer, primary_key=True, index=True)

    operation_id = Column(Integer, ForeignKey("search_rescue_operations.id"), nullable=False)
    name = Column(String, nullable=True)
    condition = Column(String, nullable=True)  # critical, stable, deceased
    found_at = Column(DateTime, nullable=True)
    extraction_time = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    operation = relationship("SearchRescue", back_populates="victims")

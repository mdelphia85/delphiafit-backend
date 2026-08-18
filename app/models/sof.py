from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class SOFPipeline(Base):
    __tablename__ = "sof_pipelines"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)          # SFAS, BUD/S, RASP, PJ/CCT, MARSOC
    branch = Column(String, nullable=False)        # army, navy, air_force, marines
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("SOFEvent", back_populates="pipeline")
    candidates = relationship("SOFCandidate", back_populates="pipeline")


class SOFEvent(Base):
    __tablename__ = "sof_events"

    id = Column(Integer, primary_key=True, index=True)

    pipeline_id = Column(Integer, ForeignKey("sof_pipelines.id"), nullable=False)
    name = Column(String, nullable=False)          # ruck, swim, land_nav, team_event, gate
    event_type = Column(String, nullable=False)    # physical, mental, team, selection_gate
    standard = Column(Float, nullable=True)        # required score/time
    description = Column(Text, nullable=True)

    pipeline = relationship("SOFPipeline", back_populates="events")
    evaluations = relationship("SOFEvaluation", back_populates="event")


class SOFCandidate(Base):
    __tablename__ = "sof_candidates"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    pipeline_id = Column(Integer, ForeignKey("sof_pipelines.id"), nullable=False)
    status = Column(String, default="active")      # active, dropped, selected, not_selected

    pipeline = relationship("SOFPipeline", back_populates="candidates")
    evaluations = relationship("SOFEvaluation", back_populates="candidate")


class SOFEvaluation(Base):
    __tablename__ = "sof_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    candidate_id = Column(Integer, ForeignKey("sof_candidates.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("sof_events.id"), nullable=False)

    score = Column(Float, nullable=True)
    passed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("SOFCandidate", back_populates="evaluations")
    event = relationship("SOFEvent", back_populates="evaluations")

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class MissionReplay(Base):
    __tablename__ = "mission_replays"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    mission_type = Column(String, nullable=False)      # swat, sof, academy, sar, hazmat, wildland, maritime, aviation
    mission_id = Column(Integer, nullable=False)        # ID of the mission or scenario
    score = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    steps = relationship("MissionStep", back_populates="replay")
    annotations = relationship("MissionAnnotation", back_populates="replay")


class MissionStep(Base):
    __tablename__ = "mission_steps"

    id = Column(Integer, primary_key=True, index=True)

    replay_id = Column(Integer, ForeignKey("mission_replays.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    action_type = Column(String, nullable=False)        # movement, decision, event, hazard, shot, rescue
    description = Column(Text, nullable=True)
    score_delta = Column(Float, default=0.0)

    replay = relationship("MissionReplay", back_populates="steps")


class MissionAnnotation(Base):
    __tablename__ = "mission_annotations"

    id = Column(Integer, primary_key=True, index=True)

    replay_id = Column(Integer, ForeignKey("mission_replays.id"), nullable=False)
    instructor_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    category = Column(String, nullable=False)           # tactics, safety, decision-making, performance
    note = Column(Text, nullable=False)

    replay = relationship("MissionReplay", back_populates="annotations")

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class SWATPipeline(Base):
    __tablename__ = "swat_pipelines"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)          # SWAT Prep, SRT Prep, HRT Prep
    agency = Column(String, nullable=False)        # police, sheriff, federal
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    drills = relationship("SWATDrill", back_populates="pipeline")
    operators = relationship("SWATOperator", back_populates="pipeline")


class SWATDrill(Base):
    __tablename__ = "swat_drills"

    id = Column(Integer, primary_key=True, index=True)

    pipeline_id = Column(Integer, ForeignKey("swat_pipelines.id"), nullable=False)
    name = Column(String, nullable=False)          # CQB, breaching, hostage rescue, marksmanship
    drill_type = Column(String, nullable=False)    # physical, tactical, shooting, scenario
    standard = Column(Float, nullable=True)        # required score/time
    description = Column(Text, nullable=True)

    pipeline = relationship("SWATPipeline", back_populates="drills")
    evaluations = relationship("SWATEvaluation", back_populates="drill")


class SWATOperator(Base):
    __tablename__ = "swat_operators"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    pipeline_id = Column(Integer, ForeignKey("swat_pipelines.id"), nullable=False)
    status = Column(String, default="active")      # active, dropped, selected, not_selected

    pipeline = relationship("SWATPipeline", back_populates="operators")
    evaluations = relationship("SWATEvaluation", back_populates="operator")


class SWATEvaluation(Base):
    __tablename__ = "swat_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    operator_id = Column(Integer, ForeignKey("swat_operators.id"), nullable=False)
    drill_id = Column(Integer, ForeignKey("swat_drills.id"), nullable=False)

    score = Column(Float, nullable=True)
    passed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    operator = relationship("SWATOperator", back_populates="evaluations")
    drill = relationship("SWATDrill", back_populates="evaluations")

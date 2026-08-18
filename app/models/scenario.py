from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    category = Column(String, nullable=False)      # cqb, disaster, sar, maritime, aviation, hazmat, wildland
    difficulty = Column(String, nullable=True)     # easy, moderate, hard, extreme
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    nodes = relationship("ScenarioNode", back_populates="scenario")
    runs = relationship("ScenarioRun", back_populates="scenario")


class ScenarioNode(Base):
    __tablename__ = "scenario_nodes"

    id = Column(Integer, primary_key=True, index=True)

    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    node_type = Column(String, nullable=False)     # decision, event, outcome
    difficulty = Column(String, nullable=True)

    scenario = relationship("Scenario", back_populates="nodes")
    branches = relationship("ScenarioBranch", back_populates="node")


class ScenarioBranch(Base):
    __tablename__ = "scenario_branches"

    id = Column(Integer, primary_key=True, index=True)

    node_id = Column(Integer, ForeignKey("scenario_nodes.id"), nullable=False)
    choice_text = Column(String, nullable=False)
    next_node_id = Column(Integer, nullable=True)
    consequence = Column(Text, nullable=True)
    score_change = Column(Float, default=0.0)

    node = relationship("ScenarioNode", back_populates="branches")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, index=True)

    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    score = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    scenario = relationship("Scenario", back_populates="runs")
    steps = relationship("ScenarioStep", back_populates="run")


class ScenarioStep(Base):
    __tablename__ = "scenario_steps"

    id = Column(Integer, primary_key=True, index=True)

    run_id = Column(Integer, ForeignKey("scenario_runs.id"), nullable=False)
    node_id = Column(Integer, nullable=False)
    choice_text = Column(String, nullable=True)
    score_delta = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    run = relationship("ScenarioRun", back_populates="steps")

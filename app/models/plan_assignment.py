from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database.connection import Base


class PlanAssignment(Base):
    """A plan assigned to a client by a coach (one active row per plan/client pair)."""

    __tablename__ = "plan_assignments"
    __table_args__ = (UniqueConstraint("plan_id", "client_id", name="uq_plan_assignment"),)

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    status = Column(String, default="active", nullable=False)  # active, completed, cancelled
    notes = Column(Text, nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

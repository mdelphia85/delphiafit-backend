from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.database.connection import Base


class CoachMessage(Base):
    """One message in a coach <-> client thread. A thread is (coach_id, client_id)."""

    __tablename__ = "coach_messages"
    __table_args__ = (Index("ix_coach_messages_thread", "coach_id", "client_id"),)

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sender = Column(String, nullable=False)  # "coach" or "client"
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)  # set when the recipient has read it

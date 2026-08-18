from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON

from app.database.connection import Base


class LiveClassAttendance(Base):
    __tablename__ = "live_class_attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    class_id = Column(Integer, nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LiveCoachingSession(Base):
    __tablename__ = "live_coaching_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    coach_id = Column(Integer, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OfflineSyncRecord(Base):
    __tablename__ = "offline_sync"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)

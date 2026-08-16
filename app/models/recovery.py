from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class RecoveryLog(Base):
    __tablename__ = "recovery_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sleep_hours = Column(Float, default=0.0)
    soreness_level = Column(Integer, default=0)  # 1–10 scale
    readiness_score = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

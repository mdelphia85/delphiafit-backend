from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class StrengthMetric(Base):
    __tablename__ = "strength_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # e.g. "bench_press_1RM"
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

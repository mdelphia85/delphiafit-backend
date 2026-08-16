from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from datetime import datetime
from app.database.connection import Base

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the workout
    user_id = Column(Integer, nullable=False)

    # Mode: "manual" or "structured"
    mode = Column(String, nullable=False)

    # Manual Mode fields
    manual_name = Column(String, nullable=True)
    manual_notes = Column(String, nullable=True)

    # Duration (manual or structured)
    duration_minutes = Column(Integer, nullable=False)

    # Structured Mode fields
    workout_type = Column(String, nullable=True)
    weight_unit = Column(String, nullable=True)
    weight_value = Column(Integer, nullable=True)

    # JSON fields for structured workouts
    plan_json = Column(JSON, nullable=True)            # warmup/main/finisher/cooldown
    block_durations_json = Column(JSON, nullable=True) # durations per block
    equipment_json = Column(JSON, nullable=True)       # list of equipment

    # Timestamp
    date = Column(DateTime, default=datetime.utcnow)

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime


class WorkoutLogCreate(BaseModel):
    mode: str
    duration_minutes: int

    manual_name: Optional[str] = None
    manual_notes: Optional[str] = None

    workout_type: Optional[str] = None
    weight_unit: Optional[str] = None
    weight_value: Optional[int] = None

    plan_json: Optional[Dict] = None
    block_durations_json: Optional[Dict] = None
    equipment_json: Optional[List[str]] = None
    timestamp: Optional[datetime] = None


class WorkoutLogUpdate(BaseModel):
    mode: Optional[str] = None
    duration_minutes: Optional[int] = None

    manual_name: Optional[str] = None
    manual_notes: Optional[str] = None

    workout_type: Optional[str] = None
    weight_unit: Optional[str] = None
    weight_value: Optional[int] = None

    plan_json: Optional[Dict] = None
    block_durations_json: Optional[Dict] = None
    equipment_json: Optional[List[str]] = None

    timestamp: Optional[datetime] = None


class WorkoutLog(BaseModel):
    id: int
    user_id: int
    mode: str
    duration_minutes: int

    manual_name: Optional[str] = None
    manual_notes: Optional[str] = None

    workout_type: Optional[str] = None
    weight_unit: Optional[str] = None
    weight_value: Optional[int] = None

    plan_json: Optional[Dict] = None
    block_durations_json: Optional[Dict] = None
    equipment_json: Optional[List[str]] = None

    date: datetime

    model_config = ConfigDict(from_attributes=True)

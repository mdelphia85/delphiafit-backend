from pydantic import BaseModel
from typing import Optional, List, Dict

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


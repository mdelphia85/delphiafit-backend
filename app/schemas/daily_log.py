from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DailyLogCreate(BaseModel):
    protein: float | None = None
    water: float | None = None
    calories: float | None = None
    meals: float | None = None
    workouts: float | None = None
    supplements: float | None = None
    mood: str | None = None
    energy: str | None = None
    date: datetime | None = None

class DailyLogUpdate(BaseModel):
    protein: float | None = None
    water: float | None = None
    calories: float | None = None
    meals: float | None = None
    workouts: float | None = None
    supplements: float | None = None
    mood: str | None = None
    energy: str | None = None
    date: datetime | None = None

class DailyLogRead(BaseModel):
    protein: float | None = None
    water: float | None = None
    calories: float | None = None
    meals: float | None = None
    workouts: float | None = None
    supplements: float | None = None
    id: int
    user_id: int
    mood: str | None = None
    energy: str | None = None
    date: datetime
    model_config = ConfigDict(from_attributes=True)

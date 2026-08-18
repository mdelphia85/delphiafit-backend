from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WeightLogCreate(BaseModel):
    weight: float
    body_fat: float | None = None
    date: datetime


class WeightLogUpdate(BaseModel):
    weight: float | None = None
    body_fat: float | None = None
    date: datetime | None = None


class WeightLogRead(BaseModel):
    id: int
    user_id: int
    weight: float
    body_fat: float | None = None
    date: datetime

    model_config = ConfigDict(from_attributes=True)

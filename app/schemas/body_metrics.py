from pydantic import BaseModel
from datetime import datetime


class BodyMetricBase(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    muscle_mass_kg: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    chest_cm: float | None = None
    date: datetime


class BodyMetricCreate(BodyMetricBase):
    user_id: int


class BodyMetricUpdate(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    muscle_mass_kg: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    chest_cm: float | None = None
    date: datetime | None = None


class BodyMetricRead(BodyMetricBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

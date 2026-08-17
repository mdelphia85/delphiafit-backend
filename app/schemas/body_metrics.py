from pydantic import BaseModel
from datetime import datetime


class BodyMetricsBase(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    muscle_mass_kg: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    chest_cm: float | None = None
    date: datetime


class BodyMetricsCreate(BodyMetricsBase):
    user_id: int


class BodyMetricsUpdate(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    muscle_mass_kg: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    chest_cm: float | None = None
    date: datetime | None = None


class BodyMetricsRead(BodyMetricsBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

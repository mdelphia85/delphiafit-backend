from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class RecoveryBase(BaseModel):
    sleep_hours: float
    soreness_level: int
    readiness_score: int
    notes: Optional[str] = None


class RecoveryCreate(RecoveryBase):
    pass


class RecoveryUpdate(BaseModel):
    sleep_hours: float | None = None
    soreness_level: int | None = None
    readiness_score: int | None = None
    notes: str | None = None
    recorded_at: datetime | None = None


class RecoveryRead(RecoveryBase):
    id: int
    user_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

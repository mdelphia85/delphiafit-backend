from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RecoveryBase(BaseModel):
    sleep_hours: float
    soreness_level: int
    readiness_score: int
    notes: Optional[str] = None

class RecoveryCreate(RecoveryBase):
    pass

class RecoveryRead(RecoveryBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from datetime import datetime

class ProgressSnapshotBase(BaseModel):
    metric: str
    value: float

class ProgressSnapshotCreate(ProgressSnapshotBase):
    pass

class ProgressSnapshotRead(ProgressSnapshotBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

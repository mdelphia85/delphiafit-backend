from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProgressSnapshotBase(BaseModel):
    metric: str
    value: float


class ProgressSnapshotCreate(ProgressSnapshotBase):
    pass


class ProgressSnapshotUpdate(BaseModel):
    metric: str | None = None
    value: float | None = None
    recorded_at: datetime | None = None


class ProgressSnapshotRead(ProgressSnapshotBase):
    id: int
    user_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

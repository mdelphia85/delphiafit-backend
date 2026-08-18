from pydantic import BaseModel, ConfigDict
from datetime import datetime


class HydrationLogBase(BaseModel):
    amount_ml: int
    date: datetime
    notes: str | None = None


class HydrationLogCreate(HydrationLogBase):
    pass


class HydrationLogUpdate(BaseModel):
    amount_ml: int | None = None
    date: datetime | None = None
    notes: str | None = None


class HydrationLogRead(HydrationLogBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

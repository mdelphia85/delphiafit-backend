from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SportsLogBase(BaseModel):
    sport: str
    duration_minutes: int
    date: datetime


class SportsLogCreate(SportsLogBase):
    pass


class SportsLogUpdate(BaseModel):
    sport: str | None = None
    duration_minutes: int | None = None
    date: datetime | None = None


class SportsLogRead(SportsLogBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class PeriodizationBlockBase(BaseModel):
    block_name: str
    focus: str
    start_date: datetime
    end_date: datetime


class PeriodizationBlockCreate(PeriodizationBlockBase):
    pass


class PeriodizationBlockUpdate(BaseModel):
    block_name: str | None = None
    focus: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class PeriodizationBlockRead(PeriodizationBlockBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

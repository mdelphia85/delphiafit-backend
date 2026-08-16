from pydantic import BaseModel
from datetime import datetime

class PeriodizationBlockBase(BaseModel):
    block_name: str
    focus: str
    start_date: datetime
    end_date: datetime

class PeriodizationBlockCreate(PeriodizationBlockBase):
    pass

class PeriodizationBlockRead(PeriodizationBlockBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

from pydantic import BaseModel
from datetime import datetime

class PersonalRecordBase(BaseModel):
    exercise_name: str
    pr_type: str
    value: float

class PersonalRecordCreate(PersonalRecordBase):
    pass

class PersonalRecordRead(PersonalRecordBase):
    id: int
    user_id: int
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True

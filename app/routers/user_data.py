from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_data_record import UserDataRecord
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/user-data", tags=["user-data"])
Collection = Literal["journal", "supplements", "settings", "challenges"]


class UserDataCreate(BaseModel):
    data: dict[str, Any]


class UserDataRead(BaseModel):
    id: int
    user_id: int
    collection: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


def _get_owned_record(db: Session, user_id: int, collection: str, record_id: int) -> UserDataRecord:
    record = db.query(UserDataRecord).filter_by(id=record_id, user_id=user_id, collection=collection).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.get("/{collection}", response_model=list[UserDataRead])
def list_records(collection: Collection, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return db.query(UserDataRecord).filter_by(user_id=user_id, collection=collection).order_by(UserDataRecord.created_at.desc(), UserDataRecord.id.desc()).all()


@router.post("/{collection}", response_model=UserDataRead, status_code=status.HTTP_201_CREATED)
def create_record(collection: Collection, payload: UserDataCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    record = UserDataRecord(user_id=user_id, collection=collection, data=payload.data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{collection}/{record_id}", response_model=UserDataRead)
def update_record(collection: Collection, record_id: int, payload: UserDataCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    record = _get_owned_record(db, user_id, collection, record_id)
    record.data = payload.data
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{collection}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(collection: Collection, record_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    record = _get_owned_record(db, user_id, collection, record_id)
    db.delete(record)
    db.commit()

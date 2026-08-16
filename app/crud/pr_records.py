from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.pr_records import PRRecord
from app.schemas.pr_records import PRRecordCreate, PRRecordUpdate


def create_pr_record(db: Session, data: PRRecordCreate) -> PRRecord:
    record = PRRecord(
        user_id=data.user_id,
        exercise=data.exercise,
        weight=data.weight,
        reps=data.reps,
        timestamp=data.timestamp or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_pr_record(db: Session, record_id: int) -> Optional[PRRecord]:
    return db.query(PRRecord).filter(PRRecord.id == record_id).first()


def get_pr_records_for_user(db: Session, user_id: int) -> List[PRRecord]:
    return (
        db.query(PRRecord)
        .filter(PRRecord.user_id == user_id)
        .order_by(PRRecord.timestamp.desc())
        .all()
    )


def update_pr_record(db: Session, record_id: int, data: PRRecordUpdate) -> Optional[PRRecord]:
    record = get_pr_record(db, record_id)
    if not record:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_pr_record(db: Session, record_id: int) -> bool:
    record = get_pr_record(db, record_id)
    if not record:
        return False

    db.delete(record)
    db.commit()
    return True

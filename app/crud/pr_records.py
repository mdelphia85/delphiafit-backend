from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.pr_records import PersonalRecord
from app.schemas.pr_records import PRRecordCreate, PRRecordUpdate


def create_pr(db: Session, user_id: int, data: PRRecordCreate) -> PersonalRecord:
    record = PersonalRecord(
        user_id=user_id,
        exercise_name=data.exercise_name,
        pr_type=data.pr_type,
        value=data.value,
        notes=data.notes,
        is_current=True,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_pr(db: Session, record_id: int) -> Optional[PersonalRecord]:
    return db.query(PersonalRecord).filter(PersonalRecord.id == record_id).first()


def get_prs(db: Session, user_id: int) -> List[PersonalRecord]:
    return (
        db.query(PersonalRecord)
        .filter(PersonalRecord.user_id == user_id)
        .order_by(PersonalRecord.created_at.desc())
        .all()
    )


def update_pr(db: Session, record_id: int, data: PRRecordUpdate) -> Optional[PersonalRecord]:
    record = get_pr(db, record_id)
    if not record:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_pr(db: Session, record_id: int) -> bool:
    record = get_pr(db, record_id)
    if not record:
        return False

    db.delete(record)
    db.commit()
    return True

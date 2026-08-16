from sqlalchemy.orm import Session
from app.models.pr_records import PersonalRecord
from app.schemas.pr_records import PersonalRecordCreate

def create_pr(db: Session, user_id: int, data: PersonalRecordCreate):
    pr = PersonalRecord(
        user_id=user_id,
        exercise_name=data.exercise_name,
        pr_type=data.pr_type,
        value=data.value
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr

def get_prs(db: Session, user_id: int):
    return db.query(PersonalRecord).filter(PersonalRecord.user_id == user_id).all()

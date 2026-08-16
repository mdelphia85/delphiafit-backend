from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.instructor import Instructor


def create_instructor(db: Session, data: dict) -> Instructor:
    inst = Instructor(**data)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def get_instructor(db: Session, instructor_id: int) -> Optional[Instructor]:
    return db.query(Instructor).filter(Instructor.id == instructor_id).first()


def get_instructors(db: Session) -> List[Instructor]:
    return db.query(Instructor).all()


def update_instructor(db: Session, instructor_id: int, data: dict) -> Optional[Instructor]:
    inst = get_instructor(db, instructor_id)
    if not inst:
        return None

    for field, value in data.items():
        setattr(inst, field, value)

    db.commit()
    db.refresh(inst)
    return inst


def delete_instructor(db: Session, instructor_id: int) -> bool:
    inst = get_instructor(db, instructor_id)
    if not inst:
        return False

    db.delete(inst)
    db.commit()
    return True

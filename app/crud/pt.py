from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.pt import PTPlan


def create_pt_plan(db: Session, data: dict) -> PTPlan:
    plan = PTPlan(**data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_pt_plan(db: Session, plan_id: int) -> Optional[PTPlan]:
    return db.query(PTPlan).filter(PTPlan.id == plan_id).first()


def get_pt_plans(db: Session) -> List[PTPlan]:
    return db.query(PTPlan).all()


def update_pt_plan(db: Session, plan_id: int, data: dict) -> Optional[PTPlan]:
    plan = get_pt_plan(db, plan_id)
    if not session:
        return None

    for field, value in data.items():
        setattr(session, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def delete_pt_plan(db: Session, plan_id: int) -> bool:
    plan = get_pt_plan(db, plan_id)
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True

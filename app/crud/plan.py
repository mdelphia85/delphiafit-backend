from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.plan import Plan


def create_plan(db: Session, data: dict) -> Plan:
    plan = Plan(**data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan(db: Session, plan_id: int) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_plans(db: Session) -> List[Plan]:
    return db.query(Plan).all()


def update_plan(db: Session, plan_id: int, data: dict) -> Optional[Plan]:
    plan = get_plan(db, plan_id)
    if not plan:
        return None

    for field, value in data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> bool:
    plan = get_plan(db, plan_id)
    if not plan:
        return False

    db.delete(plan)
    db.commit()
    return True

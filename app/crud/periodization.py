from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.periodization import PeriodizationPlan
from app.schemas.periodization import PeriodizationCreate, PeriodizationUpdate


def create_periodization_plan(db: Session, data: PeriodizationCreate) -> PeriodizationPlan:
    plan = PeriodizationPlan(
        user_id=data.user_id,
        phase=data.phase,
        duration_weeks=data.duration_weeks,
        focus=data.focus,
        notes=data.notes,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_periodization_plan(db: Session, plan_id: int) -> Optional[PeriodizationPlan]:
    return db.query(PeriodizationPlan).filter(PeriodizationPlan.id == plan_id).first()


def get_periodization_plans_for_user(db: Session, user_id: int) -> List[PeriodizationPlan]:
    return (
        db.query(PeriodizationPlan)
        .filter(PeriodizationPlan.user_id == user_id)
        .order_by(PeriodizationPlan.id.desc())
        .all()
    )


def update_periodization_plan(db: Session, plan_id: int, data: PeriodizationUpdate) -> Optional[PeriodizationPlan]:
    plan = get_periodization_plan(db, plan_id)
    if not plan:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def delete_periodization_plan(db: Session, plan_id: int) -> bool:
    plan = get_periodization_plan(db, plan_id)
    if not plan:
        return False

    db.delete(plan)
    db.commit()
    return True

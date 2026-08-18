from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.macros import MacroPlan
from app.schemas.macros import MacroPlanCreate, MacroPlanUpdate


def create_macro_plan(db: Session, user_id: int, data: MacroPlanCreate) -> MacroPlan:
    plan = MacroPlan(
        user_id=user_id,
        daily_calories=data.daily_calories,
        daily_protein=data.daily_protein,
        daily_carbs=data.daily_carbs,
        daily_fats=data.daily_fats,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_macro_plan(db: Session, plan_id: int) -> Optional[MacroPlan]:
    return db.query(MacroPlan).filter(MacroPlan.id == plan_id).first()


def get_macro_plans(db: Session, user_id: int) -> List[MacroPlan]:
    return (
        db.query(MacroPlan)
        .filter(MacroPlan.user_id == user_id)
        .order_by(MacroPlan.created_at.desc())
        .all()
    )


def update_macro_plan(db: Session, plan_id: int, data: MacroPlanUpdate) -> Optional[MacroPlan]:
    plan = get_macro_plan(db, plan_id)
    if not plan:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def delete_macro_plan(db: Session, plan_id: int) -> bool:
    plan = get_macro_plan(db, plan_id)
    if not plan:
        return False

    db.delete(plan)
    db.commit()
    return True

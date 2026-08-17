from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.goals import Goal
from app.schemas.goals import GoalCreate, GoalUpdate


def create_goal(db: Session, user_id: int, data: GoalCreate) -> Goal:
    goal = Goal(
        user_id=user_id,
        title=data.title,
        target_metric=data.target_metric,
        target_value=data.target_value,
        deadline=data.deadline,
        current_value=0.0,
        is_completed=False,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: int) -> Optional[Goal]:
    return db.query(Goal).filter(Goal.id == goal_id).first()


def get_goals(db: Session, user_id: int) -> List[Goal]:
    return (
        db.query(Goal)
        .filter(Goal.user_id == user_id)
        .order_by(Goal.created_at.desc())
        .all()
    )


def update_goal(db: Session, goal_id: int, data: GoalUpdate) -> Optional[Goal]:
    goal = get_goal(db, goal_id)
    if not goal:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(goal, field, value)

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: int) -> bool:
    goal = get_goal(db, goal_id)
    if not goal:
        return False

    db.delete(goal)
    db.commit()
    return True

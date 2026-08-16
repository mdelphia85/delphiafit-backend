from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.goals import Goal
from app.schemas.goals import GoalCreate, GoalUpdate


def create_goal(db: Session, data: GoalCreate) -> Goal:
    goal = Goal(
        user_id=data.user_id,
        title=data.title,
        description=data.description,
        target_date=data.target_date,
        completed=data.completed or False,
        created_at=datetime.utcnow(),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: int) -> Optional[Goal]:
    return db.query(Goal).filter(Goal.id == goal_id).first()


def get_goals_for_user(db: Session, user_id: int) -> List[Goal]:
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

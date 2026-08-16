from sqlalchemy.orm import Session
from app.models.goals import Goal
from app.schemas.goals import GoalCreate

def create_goal(db: Session, user_id: int, data: GoalCreate):
    goal = Goal(
        user_id=user_id,
        title=data.title,
        target_metric=data.target_metric,
        target_value=data.target_value,
        deadline=data.deadline
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal

def get_goals(db: Session, user_id: int):
    return db.query(Goal).filter(Goal.user_id == user_id).all()

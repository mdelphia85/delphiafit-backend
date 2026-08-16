from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.team import Team


def create_team(db: Session, data: dict) -> Team:
    team = Team(**data)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def get_team(db: Session, team_id: int) -> Optional[Team]:
    return db.query(Team).filter(Team.id == team_id).first()


def get_teams(db: Session) -> List[Team]:
    return db.query(Team).all()


def update_team(db: Session, team_id: int, data: dict) -> Optional[Team]:
    team = get_team(db, team_id)
    if not team:
        return None

    for field, value in data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)
    return team


def delete_team(db: Session, team_id: int) -> bool:
    team = get_team(db, team_id)
    if not team:
        return False

    db.delete(team)
    db.commit()
    return True

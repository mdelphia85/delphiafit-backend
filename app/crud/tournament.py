from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.tournament import Tournament


def create_tournament(db: Session, data: dict) -> Tournament:
    tournament = Tournament(**data)
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


def get_tournament(db: Session, tournament_id: int) -> Optional[Tournament]:
    return db.query(Tournament).filter(Tournament.id == tournament_id).first()


def get_tournaments(db: Session) -> List[Tournament]:
    return db.query(Tournament).all()


def update_tournament(db: Session, tournament_id: int, data: dict) -> Optional[Tournament]:
    tournament = get_tournament(db, tournament_id)
    if not tournament:
        return None

    for field, value in data.items():
        setattr(tournament, field, value)

    db.commit()
    db.refresh(tournament)
    return tournament


def delete_tournament(db: Session, tournament_id: int) -> bool:
    tournament = get_tournament(db, tournament_id)
    if not tournament:
        return False

    db.delete(tournament)
    db.commit()
    return True

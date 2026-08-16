from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.reactions import Reaction


def create_reaction(db: Session, data: dict) -> Reaction:
    reaction = Reaction(**data)
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def get_reaction(db: Session, reaction_id: int) -> Optional[Reaction]:
    return db.query(Reaction).filter(Reaction.id == reaction_id).first()


def get_reactions(db: Session) -> List[Reaction]:
    return db.query(Reaction).all()


def update_reaction(db: Session, reaction_id: int, data: dict) -> Optional[Reaction]:
    reaction = get_reaction(db, reaction_id)
    if not reaction:
        return None

    for field, value in data.items():
        setattr(reaction, field, value)

    db.commit()
    db.refresh(reaction)
    return reaction


def delete_reaction(db: Session, reaction_id: int) -> bool:
    reaction = get_reaction(db, reaction_id)
    if not reaction:
        return False

    db.delete(reaction)
    db.commit()
    return True

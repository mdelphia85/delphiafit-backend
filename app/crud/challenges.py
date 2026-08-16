from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.challenges import Challenge


def create_challenge(db: Session, data: dict) -> Challenge:
    challenge = Challenge(**data)
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def get_challenge(db: Session, challenge_id: int) -> Optional[Challenge]:
    return db.query(Challenge).filter(Challenge.id == challenge_id).first()


def get_challenges(db: Session) -> List[Challenge]:
    return db.query(Challenge).all()


def update_challenge(db: Session, challenge_id: int, data: dict) -> Optional[Challenge]:
    challenge = get_challenge(db, challenge_id)
    if not challenge:
        return None

    for field, value in data.items():
        setattr(challenge, field, value)

    db.commit()
    db.refresh(challenge)
    return challenge


def delete_challenge(db: Session, challenge_id: int) -> bool:
    challenge = get_challenge(db, challenge_id)
    if not challenge:
        return False

    db.delete(challenge)
    db.commit()
    return True

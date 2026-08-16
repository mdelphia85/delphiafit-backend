from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.invite import Invite


def create_invite(db: Session, data: dict) -> Invite:
    invite = Invite(**data)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invite(db: Session, invite_id: int) -> Optional[Invite]:
    return db.query(Invite).filter(Invite.id == invite_id).first()


def get_invites_for_user(db: Session, user_id: int) -> List[Invite]:
    return db.query(Invite).filter(Invite.user_id == user_id).all()


def update_invite(db: Session, invite_id: int, data: dict) -> Optional[Invite]:
    invite = get_invite(db, invite_id)
    if not invite:
        return None

    for field, value in data.items():
        setattr(invite, field, value)

    db.commit()
    db.refresh(invite)
    return invite


def delete_invite(db: Session, invite_id: int) -> bool:
    invite = get_invite(db, invite_id)
    if not invite:
        return False

    db.delete(invite)
    db.commit()
    return True

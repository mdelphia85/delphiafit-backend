from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.messages import Message


def create_message(db: Session, data: dict) -> Message:
    msg = Message(**data)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_message(db: Session, message_id: int) -> Optional[Message]:
    return db.query(Message).filter(Message.id == message_id).first()


def get_messages_for_user(db: Session, user_id: int) -> List[Message]:
    return db.query(Message).filter(Message.user_id == user_id).all()


def delete_message(db: Session, message_id: int) -> bool:
    msg = get_message(db, message_id)
    if not msg:
        return False

    db.delete(msg)
    db.commit()
    return True

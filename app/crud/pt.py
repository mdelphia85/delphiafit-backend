from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.pt import PTSession


def create_pt_session(db: Session, data: dict) -> PTSession:
    session = PTSession(**data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_pt_session(db: Session, session_id: int) -> Optional[PTSession]:
    return db.query(PTSession).filter(PTSession.id == session_id).first()


def get_pt_sessions(db: Session) -> List[PTSession]:
    return db.query(PTSession).all()


def update_pt_session(db: Session, session_id: int, data: dict) -> Optional[PTSession]:
    session = get_pt_session(db, session_id)
    if not session:
        return None

    for field, value in data.items():
        setattr(session, field, value)

    db.commit()
    db.refresh(session)
    return session


def delete_pt_session(db: Session, session_id: int) -> bool:
    session = get_pt_session(db, session_id)
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True

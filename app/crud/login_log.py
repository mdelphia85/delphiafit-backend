from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog


def create_login_log(db: Session, data: dict) -> LoginLog:
    log = LoginLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_login_log(db: Session, log_id: int) -> Optional[LoginLog]:
    return db.query(LoginLog).filter(LoginLog.id == log_id).first()


def get_login_logs_for_user(db: Session, user_id: int) -> List[LoginLog]:
    return db.query(LoginLog).filter(LoginLog.user_id == user_id).all()


def delete_login_log(db: Session, log_id: int) -> bool:
    log = get_login_log(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True

from typing import List
from sqlalchemy.orm import Session

from app.models.logs import Logs


def create_log(db: Session, data: dict) -> Logs:
    log = Logs(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs(db: Session) -> List[Logs]:
    return db.query(Logs).all()

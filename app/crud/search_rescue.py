from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.search_rescue import SearchRescue


def create_search_rescue(db: Session, data: dict) -> SearchRescue:
    sr = SearchRescue(**data)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


def get_search_rescue(db: Session, sr_id: int) -> Optional[SearchRescue]:
    return db.query(SearchRescue).filter(SearchRescue.id == sr_id).first()


def get_search_rescue_logs(db: Session) -> List[SearchRescue]:
    return db.query(SearchRescue).all()


def update_search_rescue(db: Session, sr_id: int, data: dict) -> Optional[SearchRescue]:
    sr = get_search_rescue(db, sr_id)
    if not sr:
        return None

    for field, value in data.items():
        setattr(sr, field, value)

    db.commit()
    db.refresh(sr)
    return sr


def delete_search_rescue(db: Session, sr_id: int) -> bool:
    sr = get_search_rescue(db, sr_id)
    if not sr:
        return False

    db.delete(sr)
    db.commit()
    return True

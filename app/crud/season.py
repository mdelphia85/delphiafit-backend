from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.season import Season


def create_season(db: Session, data: dict) -> Season:
    season = Season(**data)
    db.add(season)
    db.commit()
    db.refresh(season)
    return season


def get_season(db: Session, season_id: int) -> Optional[Season]:
    return db.query(Season).filter(Season.id == season_id).first()


def get_seasons(db: Session) -> List[Season]:
    return db.query(Season).all()


def update_season(db: Session, season_id: int, data: dict) -> Optional[Season]:
    season = get_season(db, season_id)
    if not season:
        return None

    for field, value in data.items():
        setattr(season, field, value)

    db.commit()
    db.refresh(season)
    return season


def delete_season(db: Session, season_id: int) -> bool:
    season = get_season(db, season_id)
    if not season:
        return False

    db.delete(season)
    db.commit()
    return True

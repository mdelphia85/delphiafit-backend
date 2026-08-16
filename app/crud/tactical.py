from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.tactical import TacticalDrill
from app.schemas.tactical import TacticalCreate, TacticalUpdate


def create_tactical_drill(db: Session, data: TacticalCreate) -> TacticalDrill:
    drill = TacticalDrill(
        user_id=data.user_id,
        drill_type=data.drill_type,
        score=data.score,
        duration=data.duration,
        notes=data.notes,
    )
    db.add(drill)
    db.commit()
    db.refresh(drill)
    return drill


def get_tactical_drill(db: Session, drill_id: int) -> Optional[TacticalDrill]:
    return db.query(TacticalDrill).filter(TacticalDrill.id == drill_id).first()


def get_tactical_drills_for_user(db: Session, user_id: int) -> List[TacticalDrill]:
    return db.query(TacticalDrill).filter(TacticalDrill.user_id == user_id).all()


def update_tactical_drill(db: Session, drill_id: int, data: TacticalUpdate) -> Optional[TacticalDrill]:
    drill = get_tactical_drill(db, drill_id)
    if not drill:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(drill, field, value)

    db.commit()
    db.refresh(drill)
    return drill


def delete_tactical_drill(db: Session, drill_id: int) -> bool:
    drill = get_tactical_drill(db, drill_id)
    if not drill:
        return False

    db.delete(drill)
    db.commit()
    return True

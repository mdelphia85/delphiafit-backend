from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.tactical_drill import TacticalDrill
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate


def create_tactical_drill(db: Session, data: TacticalDrillCreate) -> TacticalDrill:
    drill = TacticalDrill(**data.model_dump())
    db.add(drill); db.commit(); db.refresh(drill); return drill


def get_tactical_drill(db: Session, drill_id: int) -> Optional[TacticalDrill]:
    return db.query(TacticalDrill).filter(TacticalDrill.id == drill_id).first()


def get_tactical_drills(db: Session) -> List[TacticalDrill]:
    return db.query(TacticalDrill).all()


def update_tactical_drill(db: Session, drill_id: int, data: TacticalDrillUpdate) -> Optional[TacticalDrill]:
    drill=get_tactical_drill(db,drill_id)
    if not drill:return None
    for field,value in data.model_dump(exclude_unset=True).items(): setattr(drill,field,value)
    db.commit();db.refresh(drill);return drill


def delete_tactical_drill(db: Session, drill_id: int) -> bool:
    drill=get_tactical_drill(db,drill_id)
    if not drill:return False
    db.delete(drill);db.commit();return True

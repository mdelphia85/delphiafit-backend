from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.tactical_drill import TacticalDrill
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate


def get_drills(db: Session, division: str, user_id: int):
    return (
        db.query(TacticalDrill)
        .filter(TacticalDrill.division == division, TacticalDrill.user_id == user_id)
        .all()
    )


def create_drill(db: Session, payload: TacticalDrillCreate, user_id: int):
    values = payload.model_dump(exclude_none=True)
    values["user_id"] = user_id
    drill = TacticalDrill(**values)
    db.add(drill)
    db.commit()
    db.refresh(drill)
    return drill


def update_drill(db: Session, drill_id: int, payload: TacticalDrillUpdate, user_id: int, division: str):
    drill = (
        db.query(TacticalDrill)
        .filter(
            TacticalDrill.id == drill_id,
            TacticalDrill.user_id == user_id,
            TacticalDrill.division == division,
        )
        .first()
    )
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")
    updates = payload.model_dump(exclude_unset=True)
    updates.pop("division", None)
    for key, value in updates.items():
        setattr(drill, key, value)
    db.commit()
    db.refresh(drill)
    return drill


def delete_drill(db: Session, drill_id: int, user_id: int, division: str):
    drill = (
        db.query(TacticalDrill)
        .filter(
            TacticalDrill.id == drill_id,
            TacticalDrill.user_id == user_id,
            TacticalDrill.division == division,
        )
        .first()
    )
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")
    db.delete(drill)
    db.commit()
    return True

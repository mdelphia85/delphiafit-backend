from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.tactical_drill import TacticalDrill
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate


def get_drills(db: Session, division: str):
    return (
        db.query(TacticalDrill)
        .filter(TacticalDrill.division == division)
        .all()
    )


def create_drill(db: Session, payload: TacticalDrillCreate):
    drill = TacticalDrill(
        division=payload.division,
        category=payload.category,
        name=payload.name,
        level=payload.level,
        duration=payload.duration,
        notes=payload.notes,
    )

    db.add(drill)
    db.commit()
    db.refresh(drill)
    return drill


def update_drill(db: Session, drill_id: int, payload: TacticalDrillUpdate):
    drill = db.query(TacticalDrill).filter(TacticalDrill.id == drill_id).first()

    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(drill, key, value)

    db.commit()
    db.refresh(drill)
    return drill


def delete_drill(db: Session, drill_id: int):
    drill = db.query(TacticalDrill).filter(TacticalDrill.id == drill_id).first()

    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")

    db.delete(drill)
    db.commit()
    return True

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate, TacticalDrillResponse
from app.services.tactical_service import get_drills, create_drill, update_drill, delete_drill

router = APIRouter(prefix="/tactical/firefighters", tags=["Firefighters Tactical"])

@router.get("/logs", response_model=list[TacticalDrillResponse])
def get_firefighter_logs(db: Session = Depends(get_db)):
    return get_drills(db, "firefighters")

@router.post("/log", response_model=TacticalDrillResponse)
def create_firefighter_log(payload: TacticalDrillCreate, db: Session = Depends(get_db)):
    payload.division = "firefighters"
    return create_drill(db, payload)

@router.put("/log/{drill_id}", response_model=TacticalDrillResponse)
def update_firefighter_log(drill_id: int, payload: TacticalDrillUpdate, db: Session = Depends(get_db)):
    return update_drill(db, drill_id, payload)

@router.delete("/log/{drill_id}")
def delete_firefighter_log(drill_id: int, db: Session = Depends(get_db)):
    delete_drill(db, drill_id)
    return {"success": True}

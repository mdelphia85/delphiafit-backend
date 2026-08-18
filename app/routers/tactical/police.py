from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate, TacticalDrillResponse
from app.services.tactical_service import get_drills, create_drill, update_drill, delete_drill

router = APIRouter(prefix="/tactical/police", tags=["Police Tactical"])

@router.get("/logs", response_model=list[TacticalDrillResponse])
def get_police_logs(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return get_drills(db, "police", user_id)

@router.post("/log", response_model=TacticalDrillResponse)
def create_police_log(payload: TacticalDrillCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    payload.division = "police"
    return create_drill(db, payload, user_id)

@router.put("/log/{drill_id}", response_model=TacticalDrillResponse)
def update_police_log(drill_id: int, payload: TacticalDrillUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return update_drill(db, drill_id, payload, user_id, "police")

@router.delete("/log/{drill_id}")
def delete_police_log(drill_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    delete_drill(db, drill_id, user_id, "police")
    return {"success": True}

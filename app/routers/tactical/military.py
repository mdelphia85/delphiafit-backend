from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.schemas.tactical import TacticalDrillCreate, TacticalDrillUpdate, TacticalDrillResponse
from app.services.tactical_service import get_drills, create_drill, update_drill, delete_drill

router = APIRouter(prefix="/tactical/military", tags=["Military Tactical"])

@router.get("/logs", response_model=list[TacticalDrillResponse])
def get_military_logs(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return get_drills(db, "military", user_id)

@router.post("/log", response_model=TacticalDrillResponse)
def create_military_log(payload: TacticalDrillCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    payload.division = "military"
    return create_drill(db, payload, user_id)

@router.put("/log/{drill_id}", response_model=TacticalDrillResponse)
def update_military_log(drill_id: int, payload: TacticalDrillUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return update_drill(db, drill_id, payload, user_id, "military")

@router.delete("/log/{drill_id}")
def delete_military_log(drill_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    delete_drill(db, drill_id, user_id, "military")
    return {"success": True}

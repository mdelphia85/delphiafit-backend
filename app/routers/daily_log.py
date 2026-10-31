from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.security import get_current_user_id
from app.schemas.daily_log import DailyLogCreate, DailyLogRead, DailyLogUpdate
from app.crud.daily_log import create_daily_log, get_daily_logs

router = APIRouter(prefix="/daily-log", tags=["daily_log"])

@router.post("/", response_model=DailyLogRead)
def add_daily_log(payload: DailyLogCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return create_daily_log(db, user_id, payload)

@router.get("/", response_model=list[DailyLogRead])
def list_daily_logs(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return get_daily_logs(db, user_id)


@router.put("/{log_id}", response_model=DailyLogRead)
def update_daily_log_for_owner(
    log_id: int, payload: DailyLogUpdate, db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    from app.models.daily_log import DailyLog

    record = db.query(DailyLog).filter_by(id=log_id, user_id=user_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Daily log not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

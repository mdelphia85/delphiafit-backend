from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.hardware_sync import HardwareSyncService

router = APIRouter(prefix="/hardware", tags=["Hardware"])
sync_service = HardwareSyncService()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class DeviceLink(BaseModel):
    user_id: int
    provider: str  # apple, google, garmin, fitbit, whoop, oura
    access_token: str
    refresh_token: Optional[str] = None


class DeviceSync(BaseModel):
    user_id: int
    provider: str


# ---------------------------------------------------------
# Link Device
# ---------------------------------------------------------
@router.post("/link")
def link_device(data: DeviceLink, db: Session = Depends(get_db)):
    try:
        return sync_service.link_device(db, data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Unlink Device
# ---------------------------------------------------------
@router.post("/unlink")
def unlink_device(data: DeviceSync, db: Session = Depends(get_db)):
    try:
        return sync_service.unlink_device(db, data.user_id, data.provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Sync Device
# ---------------------------------------------------------
@router.post("/sync")
def sync_device(data: DeviceSync, db: Session = Depends(get_db)):
    try:
        return sync_service.sync_device(db, data.user_id, data.provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Last Sync
# ---------------------------------------------------------
@router.get("/{user_id}/{provider}/last-sync")
def last_sync(user_id: int, provider: str, db: Session = Depends(get_db)):
    try:
        return sync_service.get_last_sync(db, user_id, provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Device Status
# ---------------------------------------------------------
@router.get("/{user_id}/{provider}/status")
def device_status(user_id: int, provider: str, db: Session = Depends(get_db)):
    try:
        return sync_service.get_device_status(db, user_id, provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

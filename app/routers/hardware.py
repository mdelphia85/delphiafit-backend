from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hardware import UserDevice
from app.services.hardware_sync import HardwareSyncService
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/hardware", tags=["Hardware"])
sync_service = HardwareSyncService()


class DeviceLink(BaseModel):
    provider: str
    access_token: str
    refresh_token: Optional[str] = None


class DeviceSync(BaseModel):
    provider: str


@router.get("/me/devices")
def list_devices(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.query(UserDevice).filter(UserDevice.user_id == user_id).all()
    return [{"provider": row.provider, "status": row.status, "linked_at": row.linked_at, "last_sync": row.last_sync} for row in rows]


@router.post("/link")
def link_device(data: DeviceLink, user_id: int = Depends(get_current_user_id)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Provider OAuth and secure credential storage are not configured; no access token was stored.")


@router.post("/unlink")
def unlink_device(data: DeviceSync, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return sync_service.unlink_device(db, user_id, data.provider)


@router.post("/sync")
def sync_device(data: DeviceSync, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    device = sync_service._get_device(db, user_id, data.provider)
    if not device:
        raise HTTPException(status_code=404, detail="Device is not linked.")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Provider synchronization is unavailable until vendor OAuth/API clients are configured.")


@router.get("/{user_id}/{provider}/last-sync")
def last_sync(user_id: int, provider: str, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Device not found.")
    return sync_service.get_last_sync(db, current_user_id, provider)


@router.get("/{user_id}/{provider}/status")
def device_status(user_id: int, provider: str, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Device not found.")
    return sync_service.get_device_status(db, current_user_id, provider)

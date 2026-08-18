from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.admin_config import AdminConfigSetting
from app.routers.admin.auth import verify_admin


router = APIRouter(prefix="/admin", tags=["Admin Config"])


class AdminConfig(BaseModel):
    appearance: dict


@router.get("/config")
def get_admin_config(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    row = (
        db.query(AdminConfigSetting)
        .filter(AdminConfigSetting.key == "global")
        .first()
    )
    return row.data if row else {}


@router.post("/config")
def save_admin_config(
    config: AdminConfig,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    row = (
        db.query(AdminConfigSetting)
        .filter(AdminConfigSetting.key == "global")
        .first()
    )

    data = config.model_dump()
    if row:
        row.data = data
    else:
        row = AdminConfigSetting(key="global", data=data)
        db.add(row)

    db.commit()
    db.refresh(row)
    return {"success": True, "data": row.data}

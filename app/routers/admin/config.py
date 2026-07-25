from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

class AdminConfig(BaseModel):
    appearance: dict

@router.get("/config")
async def get_admin_config(db=Depends(get_db)):
    row = db.admin_config.find_one({"_id": "global"})
    if not row:
        return {}
    return row["data"]

@router.post("/config")
async def save_admin_config(config: AdminConfig, db=Depends(get_db)):
    db.admin_config.update_one(
        {"_id": "global"},
        {"$set": {"data": config.dict()}},
        upsert=True
    )
    return {"success": True}

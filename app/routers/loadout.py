from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.loadout import LoadoutCRUD
from app.services.loadout_engine import LoadoutEngine
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/loadout", tags=["Loadouts"])
crud = LoadoutCRUD()
engine = LoadoutEngine()


class LoadoutCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class ItemCreate(BaseModel):
    loadout_id: int
    name: str
    weight: Optional[float] = 0.0
    quantity: Optional[int] = 1
    notes: Optional[str] = None


def require_owned(db: Session, loadout_id: int, user_id: int):
    loadout = crud.get_loadout(db, loadout_id, user_id)
    if loadout is None:
        raise HTTPException(status_code=404, detail="Loadout not found.")
    return loadout


@router.post("/create")
def create_loadout(data: LoadoutCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.create_loadout(db, {**data.model_dump(), "user_id": user_id})


@router.get("/list")
def list_my_loadouts(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.list_loadouts(db, user_id)


@router.get("/list/{user_id}")
def list_loadouts(user_id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Loadouts not found.")
    return crud.list_loadouts(db, current_user_id)


@router.get("/{loadout_id}")
def get_loadout(loadout_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return require_owned(db, loadout_id, user_id)


@router.post("/item")
def add_item(data: ItemCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, data.loadout_id, user_id)
    item = crud.add_item(db, data.model_dump())
    items = crud.list_items(db, data.loadout_id)
    totals = engine.calculate_totals(items)
    crud.update_totals(db, data.loadout_id, user_id, totals["total_weight"], totals["mobility_score"], totals["endurance_score"])
    return item


@router.get("/item/{loadout_id}")
def list_items(loadout_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_owned(db, loadout_id, user_id)
    return crud.list_items(db, loadout_id)

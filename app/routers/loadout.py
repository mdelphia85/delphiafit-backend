from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.loadout import LoadoutCRUD
from app.services.loadout_engine import LoadoutEngine

router = APIRouter(prefix="/loadout", tags=["Loadouts"])
crud = LoadoutCRUD()
engine = LoadoutEngine()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class LoadoutCreate(BaseModel):
    user_id: int
    name: str
    category: str
    description: Optional[str] = None


class ItemCreate(BaseModel):
    loadout_id: int
    name: str
    weight: Optional[float] = 0.0
    quantity: Optional[int] = 1
    notes: Optional[str] = None


# ---------------------------------------------------------
# Loadouts
# ---------------------------------------------------------
@router.post("/create")
def create_loadout(data: LoadoutCreate, db: Session = Depends(get_db)):
    return crud.create_loadout(db, data.dict())


@router.get("/list/{user_id}")
def list_loadouts(user_id: int, db: Session = Depends(get_db)):
    return crud.list_loadouts(db, user_id)


@router.get("/{loadout_id}")
def get_loadout(loadout_id: int, db: Session = Depends(get_db)):
    loadout = crud.get_loadout(db, loadout_id)
    if not loadout:
        raise HTTPException(status_code=404, detail="Loadout not found.")
    return loadout


# ---------------------------------------------------------
# Items
# ---------------------------------------------------------
@router.post("/item")
def add_item(data: ItemCreate, db: Session = Depends(get_db)):
    item = crud.add_item(db, data.dict())

    # Recalculate totals
    items = crud.list_items(db, data.loadout_id)
    totals = engine.calculate_totals(items)

    crud.update_totals(
        db,
        data.loadout_id,
        totals["total_weight"],
        totals["mobility_score"],
        totals["endurance_score"]
    )

    return item


@router.get("/item/{loadout_id}")
def list_items(loadout_id: int, db: Session = Depends(get_db)):
    return crud.list_items(db, loadout_id)

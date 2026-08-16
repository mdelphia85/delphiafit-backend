from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.scenario import ScenarioCRUD

router = APIRouter(prefix="/scenario", tags=["Scenario Simulator"])
crud = ScenarioCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class ScenarioCreate(BaseModel):
    name: str
    category: str
    difficulty: Optional[str] = None
    description: Optional[str] = None


class NodeCreate(BaseModel):
    scenario_id: int
    title: str
    node_type: str
    description: Optional[str] = None
    difficulty: Optional[str] = None


class BranchCreate(BaseModel):
    node_id: int
    choice_text: str
    next_node_id: Optional[int] = None
    consequence: Optional[str] = None
    score_change: Optional[float] = 0.0


class RunStart(BaseModel):
    scenario_id: int
    user_id: int


class StepCreate(BaseModel):
    run_id: int
    node_id: int
    choice_text: Optional[str] = None
    score_delta: Optional[float] = 0.0


class RunComplete(BaseModel):
    score: float


# ---------------------------------------------------------
# Scenario
# ---------------------------------------------------------
@router.post("/create")
def create_scenario(data: ScenarioCreate, db: Session = Depends(get_db)):
    return crud.create_scenario(db, data.dict())


@router.get("/list")
def list_scenarios(db: Session = Depends(get_db)):
    return crud.list_scenarios(db)


# ---------------------------------------------------------
# Nodes
# ---------------------------------------------------------
@router.post("/node")
def add_node(data: NodeCreate, db: Session = Depends(get_db)):
    return crud.add_node(db, data.dict())


@router.get("/node/{scenario_id}")
def list_nodes(scenario_id: int, db: Session = Depends(get_db)):
    return crud.list_nodes(db, scenario_id)


# ---------------------------------------------------------
# Branches
# ---------------------------------------------------------
@router.post("/branch")
def add_branch(data: BranchCreate, db: Session = Depends(get_db)):
    return crud.add_branch(db, data.dict())


@router.get("/branch/{node_id}")
def list_branches(node_id: int, db: Session = Depends(get_db)):
    return crud.list_branches(db, node_id)


# ---------------------------------------------------------
# Runs
# ---------------------------------------------------------
@router.post("/run/start")
def start_run(data: RunStart, db: Session = Depends(get_db)):
    return crud.start_run(db, data.dict())


@router.post("/run/{run_id}/complete")
def complete_run(run_id: int, data: RunComplete, db: Session = Depends(get_db)):
    return crud.complete_run(db, run_id, data.score)


# ---------------------------------------------------------
# Steps
# ---------------------------------------------------------
@router.post("/step")
def add_step(data: StepCreate, db: Session = Depends(get_db)):
    return crud.add_step(db, data.dict())


@router.get("/step/{run_id}")
def list_steps(run_id: int, db: Session = Depends(get_db)):
    return crud.list_steps(db, run_id)

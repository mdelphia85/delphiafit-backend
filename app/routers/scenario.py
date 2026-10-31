from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.scenario import ScenarioCRUD
from app.models.scenario import Scenario, ScenarioNode, ScenarioRun
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/scenario", tags=["Scenario Simulator"])
crud = ScenarioCRUD()


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


class StepCreate(BaseModel):
    run_id: int
    node_id: int
    choice_text: Optional[str] = None
    score_delta: Optional[float] = 0.0


class RunComplete(BaseModel):
    score: float


def scenario_payload(scenario: Scenario):
    return {
        "id": scenario.id,
        "name": scenario.name,
        "category": scenario.category,
        "difficulty": scenario.difficulty,
        "description": scenario.description,
        "active": scenario.active,
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
    }


def require_scenario(db: Session, scenario_id: int, user_id: int, *, owned: bool = False):
    query = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.active.is_(True))
    if owned:
        query = query.filter(Scenario.owner_user_id == user_id)
    else:
        query = query.filter((Scenario.owner_user_id.is_(None)) | (Scenario.owner_user_id == user_id))
    scenario = query.first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return scenario


def require_run(db: Session, run_id: int, user_id: int):
    run = db.query(ScenarioRun).filter(ScenarioRun.id == run_id, ScenarioRun.user_id == user_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Scenario run not found.")
    return run


@router.post("/create")
def create_scenario(data: ScenarioCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    scenario = crud.create_scenario(db, {**data.model_dump(), "owner_user_id": user_id})
    return scenario_payload(scenario)


@router.get("/list")
def list_scenarios(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [scenario_payload(scenario) for scenario in crud.list_scenarios(db, user_id)]


@router.post("/node")
def add_node(data: NodeCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_scenario(db, data.scenario_id, user_id, owned=True)
    return crud.add_node(db, data.model_dump())


@router.get("/node/{scenario_id}")
def list_nodes(scenario_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_scenario(db, scenario_id, user_id)
    return crud.list_nodes(db, scenario_id)


@router.post("/branch")
def add_branch(data: BranchCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    node = db.query(ScenarioNode).filter(ScenarioNode.id == data.node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Scenario node not found.")
    require_scenario(db, node.scenario_id, user_id, owned=True)
    if data.next_node_id is not None:
        next_node = db.query(ScenarioNode).filter(ScenarioNode.id == data.next_node_id, ScenarioNode.scenario_id == node.scenario_id).first()
        if next_node is None:
            raise HTTPException(status_code=404, detail="Next scenario node not found.")
    return crud.add_branch(db, data.model_dump())


@router.get("/branch/{node_id}")
def list_branches(node_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    node = db.query(ScenarioNode).filter(ScenarioNode.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Scenario node not found.")
    require_scenario(db, node.scenario_id, user_id)
    return crud.list_branches(db, node_id)


@router.post("/run/start")
def start_run(data: RunStart, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_scenario(db, data.scenario_id, user_id)
    return crud.start_run(db, {"scenario_id": data.scenario_id, "user_id": user_id})


@router.post("/run/{run_id}/complete")
def complete_run(run_id: int, data: RunComplete, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_run(db, run_id, user_id)
    return crud.complete_run(db, run_id, data.score)


@router.post("/step")
def add_step(data: StepCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    run = require_run(db, data.run_id, user_id)
    node = db.query(ScenarioNode).filter(ScenarioNode.id == data.node_id, ScenarioNode.scenario_id == run.scenario_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Scenario node not found.")
    return crud.add_step(db, data.model_dump())


@router.get("/step/{run_id}")
def list_steps(run_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    require_run(db, run_id, user_id)
    return crud.list_steps(db, run_id)

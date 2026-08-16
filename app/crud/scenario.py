from sqlalchemy.orm import Session
from datetime import datetime

from app.models.scenario import Scenario, ScenarioNode, ScenarioBranch, ScenarioRun, ScenarioStep


class ScenarioCRUD:

    # ---------------------------------------------------------
    # Scenario
    # ---------------------------------------------------------
    def create_scenario(self, db: Session, data: dict):
        scenario = Scenario(
            name=data["name"],
            category=data["category"],
            difficulty=data.get("difficulty"),
            description=data.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    def list_scenarios(self, db: Session):
        return db.query(Scenario).filter(Scenario.active == True).all()

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------
    def add_node(self, db: Session, data: dict):
        node = ScenarioNode(
            scenario_id=data["scenario_id"],
            title=data["title"],
            description=data.get("description"),
            node_type=data["node_type"],
            difficulty=data.get("difficulty")
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        return node

    def list_nodes(self, db: Session, scenario_id: int):
        return db.query(ScenarioNode).filter(
            ScenarioNode.scenario_id == scenario_id
        ).all()

    # ---------------------------------------------------------
    # Branches
    # ---------------------------------------------------------
    def add_branch(self, db: Session, data: dict):
        branch = ScenarioBranch(
            node_id=data["node_id"],
            choice_text=data["choice_text"],
            next_node_id=data.get("next_node_id"),
            consequence=data.get("consequence"),
            score_change=data.get("score_change", 0.0)
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch

    def list_branches(self, db: Session, node_id: int):
        return db.query(ScenarioBranch).filter(
            ScenarioBranch.node_id == node_id
        ).all()

    # ---------------------------------------------------------
    # Runs
    # ---------------------------------------------------------
    def start_run(self, db: Session, data: dict):
        run = ScenarioRun(
            scenario_id=data["scenario_id"],
            user_id=data["user_id"],
            score=0.0,
            completed=False,
            started_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def complete_run(self, db: Session, run_id: int, score: float):
        run = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
        run.completed = True
        run.score = score
        run.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        return run

    # ---------------------------------------------------------
    # Steps
    # ---------------------------------------------------------
    def add_step(self, db: Session, data: dict):
        step = ScenarioStep(
            run_id=data["run_id"],
            node_id=data["node_id"],
            choice_text=data.get("choice_text"),
            score_delta=data.get("score_delta", 0.0),
            timestamp=datetime.utcnow()
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    def list_steps(self, db: Session, run_id: int):
        return db.query(ScenarioStep).filter(
            ScenarioStep.run_id == run_id
        ).all()

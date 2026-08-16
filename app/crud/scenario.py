from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.scenario import Scenario


def create_scenario(db: Session, data: dict) -> Scenario:
    scenario = Scenario(**data)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def get_scenario(db: Session, scenario_id: int) -> Optional[Scenario]:
    return db.query(Scenario).filter(Scenario.id == scenario_id).first()


def get_scenarios(db: Session) -> List[Scenario]:
    return db.query(Scenario).all()


def update_scenario(db: Session, scenario_id: int, data: dict) -> Optional[Scenario]:
    scenario = get_scenario(db, scenario_id)
    if not scenario:
        return None

    for field, value in data.items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)
    return scenario


def delete_scenario(db: Session, scenario_id: int) -> bool:
    scenario = get_scenario(db, scenario_id)
    if not scenario:
        return False

    db.delete(scenario)
    db.commit()
    return True

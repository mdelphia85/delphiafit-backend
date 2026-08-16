from pydantic import BaseModel
from datetime import datetime

# ============================================================
# UNIFIED TACTICAL DRILL MODEL (MANUAL + GENERATOR)
# ============================================================

class TacticalDrillBase(BaseModel):
    division: str
    category: str
    name: str
    level: str | None = None
    duration: str | None = None
    notes: str | None = None

    # Shared generator fields
    intensity: str | None = None
    focus: str | None = None
    environment: str | None = None
    objective: str | None = None
    equipment: str | None = None
    hazards: str | None = None
    obstacles: str | None = None
    weather: str | None = None

    # EMS‑specific
    gearLoad: str | None = None
    crewSize: str | None = None
    scenarioType: str | None = None
    patientProfile: str | None = None
    extractionType: str | None = None
    medicalLoad: str | None = None
    timePressure: str | None = None

    # Firefighters‑specific
    fireType: str | None = None
    buildingType: str | None = None
    smokeConditions: str | None = None
    rescueProfile: str | None = None

    # Military‑specific
    terrain: str | None = None
    loadout: str | None = None
    movementType: str | None = None
    contactType: str | None = None

    # Police‑specific
    suspectProfile: str | None = None
    threatLevel: str | None = None


# ============================================================
# CREATE / UPDATE / RESPONSE
# ============================================================

class TacticalDrillCreate(TacticalDrillBase):
    pass


class TacticalDrillUpdate(BaseModel):
    division: str | None = None
    category: str | None = None
    name: str | None = None
    level: str | None = None
    duration: str | None = None
    notes: str | None = None

    intensity: str | None = None
    focus: str | None = None
    environment: str | None = None
    objective: str | None = None
    equipment: str | None = None
    hazards: str | None = None
    obstacles: str | None = None
    weather: str | None = None

    gearLoad: str | None = None
    crewSize: str | None = None
    scenarioType: str | None = None
    patientProfile: str | None = None
    extractionType: str | None = None
    medicalLoad: str | None = None
    timePressure: str | None = None

    fireType: str | None = None
    buildingType: str | None = None
    smokeConditions: str | None = None
    rescueProfile: str | None = None

    terrain: str | None = None
    loadout: str | None = None
    movementType: str | None = None
    contactType: str | None = None

    suspectProfile: str | None = None
    threatLevel: str | None = None


class TacticalDrillResponse(TacticalDrillBase):
    id: int

    class Config:
        from_attributes = True

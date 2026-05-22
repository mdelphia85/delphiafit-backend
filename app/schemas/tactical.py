from pydantic import BaseModel

# ============================================================
# UNIFIED TACTICAL DRILL MODEL (MANUAL + GENERATOR)
# ============================================================

class TacticalDrillBase(BaseModel):
    # Core fields (manual + generator)
    division: str              # firefighters, ems, police, military
    category: str              # category bucket
    name: str                  # drill name
    level: str | None = None
    duration: str | None = None
    notes: str | None = None   # manual notes OR generator description

    # ========================================================
    # GENERATOR METADATA (ALL OPTIONAL)
    # ========================================================

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


class TacticalDrillUpdate(TacticalDrillBase):
    pass


class TacticalDrillResponse(TacticalDrillBase):
    id: int

    class Config:
        orm_mode = True

from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base

class TacticalDrill(Base):
    __tablename__ = "tactical_drills"

    id = Column(Integer, primary_key=True, index=True)
    division = Column(String, index=True)   # firefighters, ems, police, military
    category = Column(String, index=True)
    name = Column(String)
    level = Column(String)
    duration = Column(String)
    notes = Column(Text)
from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base

class TacticalDrill(Base):
    __tablename__ = "tactical_drills"

    id = Column(Integer, primary_key=True, index=True)

    # Core fields (manual + generator)
    division = Column(String, index=True)     # firefighters, ems, police, military
    category = Column(String, index=True)
    name = Column(String)
    level = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    notes = Column(Text, nullable=True)       # manual notes OR generator description

    # Shared generator metadata
    intensity = Column(String, nullable=True)
    focus = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    objective = Column(String, nullable=True)
    equipment = Column(String, nullable=True)
    hazards = Column(String, nullable=True)
    obstacles = Column(String, nullable=True)
    weather = Column(String, nullable=True)

    # EMS‑specific generator fields
    gearLoad = Column(String, nullable=True)
    crewSize = Column(String, nullable=True)
    scenarioType = Column(String, nullable=True)
    patientProfile = Column(String, nullable=True)
    extractionType = Column(String, nullable=True)
    medicalLoad = Column(String, nullable=True)
    timePressure = Column(String, nullable=True)

    # Firefighters‑specific generator fields
    fireType = Column(String, nullable=True)
    buildingType = Column(String, nullable=True)
    smokeConditions = Column(String, nullable=True)
    rescueProfile = Column(String, nullable=True)

    # Military‑specific generator fields
    terrain = Column(String, nullable=True)
    loadout = Column(String, nullable=True)
    movementType = Column(String, nullable=True)
    contactType = Column(String, nullable=True)

    # Police‑specific generator fields
    suspectProfile = Column(String, nullable=True)
    threatLevel = Column(String, nullable=True)

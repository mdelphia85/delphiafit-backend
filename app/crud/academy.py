from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.academy import (
    AcademyProgram,
    AcademyModule,
    AcademyCadet,
    AcademyEvaluation,
)
from app.schemas.academy import (
    AcademyProgramCreate,
    AcademyProgramUpdate,
    AcademyModuleCreate,
    AcademyModuleUpdate,
    AcademyCadetCreate,
    AcademyCadetUpdate,
    AcademyEvaluationCreate,
    AcademyEvaluationUpdate,
)
from datetime import datetime


# -----------------------------
# Academy Programs
# -----------------------------

def create_program(db: Session, data: AcademyProgramCreate) -> AcademyProgram:
    program = AcademyProgram(
        name=data.name,
        category=data.category,
        description=data.description,
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


def get_program(db: Session, program_id: int) -> Optional[AcademyProgram]:
    return db.query(AcademyProgram).filter(AcademyProgram.id == program_id).first()


def get_programs(db: Session) -> List[AcademyProgram]:
    return db.query(AcademyProgram).all()


def update_program(db: Session, program_id: int, data: AcademyProgramUpdate) -> Optional[AcademyProgram]:
    program = get_program(db, program_id)
    if not program:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(program, field, value)

    program.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(program)
    return program


def delete_program(db: Session, program_id: int) -> bool:
    program = get_program(db, program_id)
    if not program:
        return False

    db.delete(program)
    db.commit()
    return True


# -----------------------------
# Academy Modules
# -----------------------------

def create_module(db: Session, data: AcademyModuleCreate) -> AcademyModule:
    module = AcademyModule(
        program_id=data.program_id,
        name=data.name,
        module_type=data.module_type,
        description=data.description,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def get_module(db: Session, module_id: int) -> Optional[AcademyModule]:
    return db.query(AcademyModule).filter(AcademyModule.id == module_id).first()


def get_modules_for_program(db: Session, program_id: int) -> List[AcademyModule]:
    return db.query(AcademyModule).filter(AcademyModule.program_id == program_id).all()


def update_module(db: Session, module_id: int, data: AcademyModuleUpdate) -> Optional[AcademyModule]:
    module = get_module(db, module_id)
    if not module:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(module, field, value)

    db.commit()
    db.refresh(module)
    return module


def delete_module(db: Session, module_id: int) -> bool:
    module = get_module(db, module_id)
    if not module:
        return False

    db.delete(module)
    db.commit()
    return True


# -----------------------------
# Academy Cadets
# -----------------------------

def create_cadet(db: Session, data: AcademyCadetCreate) -> AcademyCadet:
    cadet = AcademyCadet(
        user_id=data.user_id,
        program_id=data.program_id,
        status=data.status or "enrolled",
    )
    db.add(cadet)
    db.commit()
    db.refresh(cadet)
    return cadet


def get_cadet(db: Session, cadet_id: int) -> Optional[AcademyCadet]:
    return db.query(AcademyCadet).filter(AcademyCadet.id == cadet_id).first()


def get_cadets_for_program(db: Session, program_id: int) -> List[AcademyCadet]:
    return db.query(AcademyCadet).filter(AcademyCadet.program_id == program_id).all()


def update_cadet(db: Session, cadet_id: int, data: AcademyCadetUpdate) -> Optional[AcademyCadet]:
    cadet = get_cadet(db, cadet_id)
    if not cadet:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(cadet, field, value)

    db.commit()
    db.refresh(cadet)
    return cadet


def delete_cadet(db: Session, cadet_id: int) -> bool:
    cadet = get_cadet(db, cadet_id)
    if not cadet:
        return False

    db.delete(cadet)
    db.commit()
    return True


# -----------------------------
# Academy Evaluations
# -----------------------------

def create_evaluation(db: Session, data: AcademyEvaluationCreate) -> AcademyEvaluation:
    evaluation = AcademyEvaluation(
        cadet_id=data.cadet_id,
        module_id=data.module_id,
        score=data.score,
        passed=data.passed,
        notes=data.notes,
        timestamp=datetime.utcnow(),
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_evaluation(db: Session, evaluation_id: int) -> Optional[AcademyEvaluation]:
    return db.query(AcademyEvaluation).filter(AcademyEvaluation.id == evaluation_id).first()


def get_evaluations_for_cadet(db: Session, cadet_id: int) -> List[AcademyEvaluation]:
    return db.query(AcademyEvaluation).filter(AcademyEvaluation.cadet_id == cadet_id).all()


def update_evaluation(db: Session, evaluation_id: int, data: AcademyEvaluationUpdate) -> Optional[AcademyEvaluation]:
    evaluation = get_evaluation(db, evaluation_id)
    if not evaluation:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)
    return evaluation


def delete_evaluation(db: Session, evaluation_id: int) -> bool:
    evaluation = get_evaluation(db, evaluation_id)
    if not evaluation:
        return False

    db.delete(evaluation)
    db.commit()
    return True

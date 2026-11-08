from sqlalchemy.orm import Session
from datetime import datetime

from app.models.academy import AcademyProgram, AcademyModule, AcademyCadet, AcademyEvaluation


class AcademyCRUD:

    # ---------------------------------------------------------
    # Programs
    # ---------------------------------------------------------
    def create_program(self, db: Session, data: dict):
        program = AcademyProgram(
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(program)
        db.commit()
        db.refresh(program)
        return program

    def list_programs(self, db: Session):
        return db.query(AcademyProgram).filter(AcademyProgram.active == True).all()

    # ---------------------------------------------------------
    # Modules
    # ---------------------------------------------------------
    def add_module(self, db: Session, data: dict):
        module = AcademyModule(
            program_id=data["program_id"],
            name=data["name"],
            module_type=data["module_type"],
            description=data.get("description")
        )
        db.add(module)
        db.commit()
        db.refresh(module)
        return module

    def list_modules(self, db: Session, program_id: int):
        return db.query(AcademyModule).filter(
            AcademyModule.program_id == program_id
        ).all()

    # ---------------------------------------------------------
    # Cadets
    # ---------------------------------------------------------
    def enroll_cadet(self, db: Session, data: dict):
        cadet = AcademyCadet(
            user_id=data["user_id"],
            program_id=data["program_id"],
            status="enrolled"
        )
        db.add(cadet)
        db.commit()
        db.refresh(cadet)
        return cadet

    def list_cadets(self, db: Session, program_id: int):
        return db.query(AcademyCadet).filter(
            AcademyCadet.program_id == program_id
        ).all()

    # ---------------------------------------------------------
    # Evaluations
    # ---------------------------------------------------------
    def evaluate(self, db: Session, data: dict):
        evaluation = AcademyEvaluation(
            cadet_id=data["cadet_id"],
            module_id=data["module_id"],
            score=data.get("score"),
            passed=data.get("passed", False),
            notes=data.get("notes"),
            timestamp=datetime.utcnow()
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    def get_evaluations(self, db: Session, cadet_id: int):
        return db.query(AcademyEvaluation).filter(
            AcademyEvaluation.cadet_id == cadet_id
        ).all()

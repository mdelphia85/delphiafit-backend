from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.nutrition_settings import GeneratedMealPlan, NutritionSettings
from app.models.user_profile import UserProfile
from app.services.meal_plan import ALLERGENS, MealPlanError, generate_meal_plan
from app.services.nutrition_calc import OVERRIDE_LIMITS, calculate_targets
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/nutrition-coach", tags=["nutrition_coach"])

Diet = Literal["none", "pescatarian", "vegetarian", "vegan"]
Avoid = Literal["dairy", "egg", "fish", "nuts", "gluten", "soy"]


def _bounded(key):
    low, high = OVERRIDE_LIMITS[key]
    return Field(default=None, ge=low, le=high)


class SettingsUpdate(BaseModel):
    """Partial update: omitted fields are unchanged, explicit null clears a value."""

    goal_type: Optional[Literal["lose", "maintain", "gain"]] = None
    target_weight: Optional[float] = Field(default=None, gt=0, le=1500)
    weekly_rate: Optional[float] = Field(default=None, ge=0, le=5)
    goal_unit: Optional[Literal["lbs", "kg"]] = None
    calorie_override: Optional[int] = _bounded("calories")
    protein_override: Optional[int] = _bounded("protein")
    carbs_override: Optional[int] = _bounded("carbs")
    fat_override: Optional[int] = _bounded("fat")
    diet: Optional[Diet] = None
    avoid: Optional[List[Avoid]] = None
    meals_per_day: Optional[Literal[3, 4, 5]] = None
    extras: Optional[dict] = None


class GenerateRequest(BaseModel):
    seed: Optional[int] = None


SETTING_FIELDS = (
    "goal_type", "target_weight", "weekly_rate", "goal_unit", "calorie_override",
    "protein_override", "carbs_override", "fat_override", "diet", "meals_per_day",
)
NOT_NULLABLE = {"goal_unit", "diet", "meals_per_day"}


def _get_settings(db: Session, user_id: int) -> Optional[NutritionSettings]:
    return db.query(NutritionSettings).filter(NutritionSettings.user_id == user_id).first()


def _settings_dict(row: Optional[NutritionSettings]) -> dict:
    if row is None:
        return {
            "goal_type": None, "target_weight": None, "weekly_rate": None, "goal_unit": "lbs",
            "calorie_override": None, "protein_override": None, "carbs_override": None, "fat_override": None,
            "diet": "none", "avoid": [], "meals_per_day": 5, "extras": {},
        }
    return {
        **{f: getattr(row, f) for f in SETTING_FIELDS},
        "avoid": row.avoid_json or [],
        "extras": row.extras_json or {},
    }


def _profile_dict(db: Session, user_id: int) -> dict:
    p = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if p is None:
        return {}
    return {
        "dob": p.dob, "current_weight": p.current_weight, "weight_unit": p.weight_unit,
        "height": p.height, "height_unit": p.height_unit, "sex": p.sex, "activity_level": p.activity_level,
        "goal_weight": p.goal_weight,
    }


def _targets(db: Session, user_id: int) -> dict:
    return calculate_targets(_profile_dict(db, user_id), _settings_dict(_get_settings(db, user_id)))


@router.get("/targets")
def get_targets(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return _targets(db, user_id)


@router.get("/settings")
def get_settings(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return {**_settings_dict(_get_settings(db, user_id)), "allergens": sorted(ALLERGENS)}


@router.put("/settings")
def update_settings(
    data: SettingsUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = _get_settings(db, user_id)
    if row is None:
        row = NutritionSettings(user_id=user_id)
        db.add(row)
    for field in data.model_fields_set:
        value = getattr(data, field)
        if field == "avoid":
            row.avoid_json = value or []
        elif field == "extras":
            row.extras_json = value or {}
        elif value is None and field in NOT_NULLABLE:
            continue
        else:
            setattr(row, field, value)
    db.commit()
    return get_settings(user_id, db)


@router.post("/meal-plans/generate")
def generate_plan(
    body: GenerateRequest = GenerateRequest(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate and save a plan. This never writes to any food or nutrition log."""
    targets = _targets(db, user_id)
    if targets["status"] != "ready":
        raise HTTPException(status_code=422, detail={"message": "Profile or goal information is incomplete.", **{
            k: targets.get(k) for k in ("status", "missing", "problems")}})
    settings = _settings_dict(_get_settings(db, user_id))
    try:
        plan = generate_meal_plan(
            targets["effective"], meals_per_day=settings["meals_per_day"], diet=settings["diet"],
            avoid=settings["avoid"], seed=body.seed,
        )
    except MealPlanError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc)})
    plan["target_source"] = targets["effective"]["source"]
    row = GeneratedMealPlan(user_id=user_id, plan_json=plan)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "created_at": row.created_at, "plan": plan}


@router.get("/meal-plans/latest")
def latest_plan(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    row = (
        db.query(GeneratedMealPlan)
        .filter(GeneratedMealPlan.user_id == user_id)
        .order_by(GeneratedMealPlan.id.desc())
        .first()
    )
    if row is None:
        return {"id": None, "created_at": None, "plan": None}
    return {"id": row.id, "created_at": row.created_at, "plan": row.plan_json}


@router.get("/meal-plans")
def list_plans(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = (
        db.query(GeneratedMealPlan)
        .filter(GeneratedMealPlan.user_id == user_id)
        .order_by(GeneratedMealPlan.id.desc())
        .limit(20)
        .all()
    )
    return [{"id": r.id, "created_at": r.created_at, "plan": r.plan_json} for r in rows]

"""Estimated calorie and macro targets.

Uses the Mifflin-St Jeor equation (Mifflin et al., 1990) for resting energy
expenditure, standard activity multipliers for total daily energy expenditure,
and goal adjustments capped by conservative safeguards. All values are
estimates, not medical advice. Nothing is invented: when a required input is
missing the result reports exactly which fields are missing.
"""

from datetime import date, datetime
from typing import Any, Optional

LB_PER_KG = 2.20462
CM_PER_INCH = 2.54
KCAL_PER_KG_BODY_MASS = 7700.0

ACTIVITY_LEVELS = {
    "sedentary": (1.2, "Sedentary (little or no exercise)"),
    "light": (1.375, "Lightly active (1-3 days/week)"),
    "moderate": (1.55, "Moderately active (3-5 days/week)"),
    "very_active": (1.725, "Very active (6-7 days/week)"),
    "extra_active": (1.9, "Extra active (hard daily training or physical job)"),
}
GOAL_TYPES = ("lose", "maintain", "gain")
SEX_REFERENCES = ("male", "female")

MIN_AGE, MAX_AGE = 18, 100
MIN_WEIGHT_KG, MAX_WEIGHT_KG = 30.0, 300.0
MIN_HEIGHT_CM, MAX_HEIGHT_CM = 120.0, 230.0

CALORIE_FLOOR = {"male": 1500, "female": 1200}
DEFAULT_RATE_KG = {"lose": 0.5, "gain": 0.25}
MAX_LOSS_PCT_BODYWEIGHT_PER_WEEK = 0.01
MAX_GAIN_PCT_BODYWEIGHT_PER_WEEK = 0.005
MAX_LOSS_KG_PER_WEEK = 1.0
MAX_DEFICIT_FRACTION = 0.25
MAX_SURPLUS_FRACTION = 0.15

PROTEIN_G_PER_KG = {"lose": 2.0, "maintain": 1.6, "gain": 1.8}
MIN_PROTEIN_G_PER_KG = 0.8
MAX_PROTEIN_FRACTION = 0.35
FAT_FRACTION = 0.25
MIN_FAT_G_PER_KG = 0.6
MIN_FAT_FRACTION = 0.20
MIN_CARB_G = 50

OVERRIDE_LIMITS = {
    "calories": (800, 6000),
    "protein": (20, 400),
    "carbs": (0, 900),
    "fat": (15, 300),
}

ESTIMATE_DISCLAIMER = (
    "These are estimates based on the Mifflin-St Jeor equation and your profile. "
    "Individual needs vary; adjust using your own results or advice from a "
    "qualified professional."
)


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        text = str(value).strip().replace(",", "")
        return float(text) if text else None
    except ValueError:
        return None


def weight_to_kg(value: Any, unit: Optional[str]) -> Optional[float]:
    number = to_float(value)
    if number is None or number <= 0:
        return None
    return number / LB_PER_KG if (unit or "kg").lower().startswith("lb") else number


def height_to_cm(value: Any, unit: Optional[str]) -> Optional[float]:
    number = to_float(value)
    if number is None or number <= 0:
        return None
    return number * CM_PER_INCH if (unit or "cm").lower() in ("in", "inch", "inches") else number


def age_from_dob(dob: Any, today: Optional[date] = None) -> Optional[int]:
    if not dob:
        return None
    try:
        born = datetime.fromisoformat(str(dob)[:10]).date()
    except ValueError:
        return None
    today = today or date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age if age >= 0 else None


def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "male" else -161)


def _macros_for(calories: float, weight_kg: float, protein_g: Optional[float], fat_g: Optional[float]):
    """Split calories into protein/fat/carbs, returning grams and any notes."""
    notes = []
    protein = protein_g
    if protein is None:
        raise ValueError("protein required")
    fat = fat_g
    if fat is None:
        fat = max(FAT_FRACTION * calories / 9, MIN_FAT_G_PER_KG * weight_kg)
    carbs = (calories - 4 * protein - 9 * fat) / 4
    if carbs < MIN_CARB_G:
        # Lower fat toward its minimum before letting carbs fall below the floor.
        min_fat = max(MIN_FAT_FRACTION * calories / 9, MIN_FAT_G_PER_KG * weight_kg)
        fat = max(min_fat, min(fat, (calories - 4 * protein - 4 * MIN_CARB_G) / 9))
        carbs = (calories - 4 * protein - 9 * fat) / 4
        if carbs < MIN_CARB_G:
            notes.append("Calories are too low to meet protein and fat minimums with meaningful carbohydrates.")
    return round(protein), round(max(carbs, 0)), round(fat), notes


def missing_inputs(profile: dict, settings: dict) -> list:
    """Return [{field, label, where}] for anything required but absent."""
    missing = []

    def need(field, label, where):
        missing.append({"field": field, "label": label, "where": where})

    if age_from_dob(profile.get("dob")) is None:
        need("dob", "Date of birth", "profile")
    if weight_to_kg(profile.get("current_weight"), profile.get("weight_unit")) is None:
        need("current_weight", "Current weight", "profile")
    if height_to_cm(profile.get("height"), profile.get("height_unit")) is None:
        need("height", "Height", "profile")
    if profile.get("sex") not in SEX_REFERENCES:
        need("sex", "Sex (calculation reference)", "profile")
    if profile.get("activity_level") not in ACTIVITY_LEVELS:
        need("activity_level", "Activity level", "profile")
    if settings.get("goal_type") not in GOAL_TYPES:
        need("goal_type", "Goal (lose, maintain or gain)", "goals")
    return missing


def _validate_ranges(age, weight_kg, height_cm):
    problems = []
    if age < MIN_AGE:
        problems.append("Calorie estimates are only provided for adults aged 18 and over.")
    if age > MAX_AGE:
        problems.append("Please check your date of birth; age appears out of range.")
    if not MIN_WEIGHT_KG <= weight_kg <= MAX_WEIGHT_KG:
        problems.append("Please check your current weight; it appears out of range.")
    if not MIN_HEIGHT_CM <= height_cm <= MAX_HEIGHT_CM:
        problems.append("Please check your height; it appears out of range.")
    return problems


def _goal_adjustment(goal, tdee, weight_kg, rate_kg, sex):
    """Return (kcal adjustment per day, effective weekly rate kg, notes)."""
    notes = []
    if goal == "maintain":
        return 0.0, 0.0, notes

    if goal == "lose":
        requested = rate_kg if rate_kg else DEFAULT_RATE_KG["lose"]
        cap = min(MAX_LOSS_KG_PER_WEEK, MAX_LOSS_PCT_BODYWEIGHT_PER_WEEK * weight_kg)
        rate = min(requested, cap)
        if requested > cap:
            notes.append(f"Preferred loss rate was capped at {cap:.2f} kg/week for safety.")
        adjustment = -rate * KCAL_PER_KG_BODY_MASS / 7
        floor_adj = -MAX_DEFICIT_FRACTION * tdee
        if adjustment < floor_adj:
            adjustment = floor_adj
            rate = -adjustment * 7 / KCAL_PER_KG_BODY_MASS
            notes.append("Deficit limited to 25% of maintenance calories.")
        return adjustment, -rate, notes

    requested = rate_kg if rate_kg else DEFAULT_RATE_KG["gain"]
    cap = MAX_GAIN_PCT_BODYWEIGHT_PER_WEEK * weight_kg
    rate = min(requested, cap)
    if requested > cap:
        notes.append(f"Preferred gain rate was capped at {cap:.2f} kg/week to favor lean gains.")
    adjustment = rate * KCAL_PER_KG_BODY_MASS / 7
    cap_adj = MAX_SURPLUS_FRACTION * tdee
    if adjustment > cap_adj:
        adjustment = cap_adj
        rate = adjustment * 7 / KCAL_PER_KG_BODY_MASS
        notes.append("Surplus limited to 15% of maintenance calories.")
    return adjustment, rate, notes


def calculate_targets(profile: dict, settings: dict) -> dict:
    """Compute estimated and effective (override-aware) daily targets.

    profile keys: dob, current_weight, weight_unit, height, height_unit, sex,
    activity_level. settings keys: goal_type, target_weight, goal_unit,
    weekly_rate, calorie_override, protein_override, carbs_override, fat_override.
    """
    missing = missing_inputs(profile, settings)
    base = {
        "estimate_label": "Estimated",
        "disclaimer": ESTIMATE_DISCLAIMER,
        "formula": "Mifflin-St Jeor",
        "notes": [],
        "missing": missing,
    }
    if missing:
        return {**base, "status": "incomplete", "estimate": None, "effective": None, "overrides": _overrides(settings)}

    age = age_from_dob(profile["dob"])
    weight_kg = weight_to_kg(profile["current_weight"], profile.get("weight_unit"))
    height_cm = height_to_cm(profile["height"], profile.get("height_unit"))
    sex = profile["sex"]
    goal = settings["goal_type"]

    problems = _validate_ranges(age, weight_kg, height_cm)
    if problems:
        return {**base, "status": "invalid", "problems": problems, "estimate": None, "effective": None,
                "overrides": _overrides(settings)}

    notes = []
    bmr = mifflin_st_jeor(weight_kg, height_cm, age, sex)
    tdee = bmr * ACTIVITY_LEVELS[profile["activity_level"]][0]

    unit = settings.get("goal_unit") or "lbs"
    rate_value = abs(to_float(settings.get("weekly_rate")) or 0)
    rate_kg = rate_value / LB_PER_KG if unit.lower().startswith("lb") else rate_value
    adjustment, weekly_rate_kg, adj_notes = _goal_adjustment(goal, tdee, weight_kg, rate_kg or None, sex)
    notes += adj_notes

    target_kg = weight_to_kg(settings.get("target_weight"), unit)
    if target_kg is not None:
        if goal == "lose" and target_kg >= weight_kg:
            notes.append("Your target weight is not below your current weight, which does not match a weight-loss goal.")
        elif goal == "gain" and target_kg <= weight_kg:
            notes.append("Your target weight is not above your current weight, which does not match a muscle-gain goal.")
        elif goal == "maintain" and abs(target_kg - weight_kg) > 0.02 * weight_kg:
            notes.append("Your target weight differs from your current weight; consider a loss or gain goal.")

    calories = tdee + adjustment
    floor = CALORIE_FLOOR[sex]
    if calories < floor:
        calories = floor
        notes.append(f"Calories raised to the safe minimum of {floor} kcal/day.")
    calories = round(calories)

    protein_g = PROTEIN_G_PER_KG[goal] * weight_kg
    protein_g = max(protein_g, MIN_PROTEIN_G_PER_KG * weight_kg)
    if protein_g * 4 > MAX_PROTEIN_FRACTION * calories:
        protein_g = MAX_PROTEIN_FRACTION * calories / 4
        notes.append("Protein limited to 35% of calories.")
    protein, carbs, fat, macro_notes = _macros_for(calories, weight_kg, protein_g, None)
    notes += macro_notes

    estimate = {
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "bmr": round(bmr),
        "maintenance_calories": round(tdee),
        "goal_adjustment": round(calories - tdee),
        "weekly_rate_kg": round(weekly_rate_kg, 2),
    }

    effective = dict(estimate)
    overrides = _overrides(settings)
    if any(v is not None for v in overrides.values()):
        eff_cal = overrides["calories"] if overrides["calories"] is not None else calories
        eff_protein = overrides["protein"]
        if eff_protein is None:
            eff_protein = estimate["protein_g"] if eff_cal == calories else min(
                protein_g, MAX_PROTEIN_FRACTION * eff_cal / 4)
        eff_fat = overrides["fat"]
        p, c, f, _ = _macros_for(eff_cal, weight_kg, eff_protein, eff_fat)
        if overrides["carbs"] is not None:
            c = overrides["carbs"]
        effective.update({"calories": eff_cal, "protein_g": p, "carbs_g": c, "fat_g": f})
        if overrides["calories"] is not None and overrides["calories"] != calories:
            notes.append("Using your manual calorie target instead of the estimate.")
        if overrides["protein"] is not None:
            notes.append("Using your manual protein target instead of the estimate.")

    effective["source"] = "manual" if any(v is not None for v in overrides.values()) else "estimate"
    inputs = {
        "age": age,
        "weight_kg": round(weight_kg, 1),
        "height_cm": round(height_cm, 1),
        "sex_reference": sex,
        "activity_level": profile["activity_level"],
        "goal_type": goal,
    }
    return {**base, "status": "ready", "notes": notes, "inputs": inputs, "estimate": estimate,
            "effective": effective, "overrides": overrides}


def _overrides(settings: dict) -> dict:
    return {
        "calories": settings.get("calorie_override"),
        "protein": settings.get("protein_override"),
        "carbs": settings.get("carbs_override"),
        "fat": settings.get("fat_override"),
    }

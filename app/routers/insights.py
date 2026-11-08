"""Server-side streaks, achievements and analytics derived from the user's real logs."""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.daily_log import DailyLog
from app.models.hydration import HydrationLog
from app.models.nutrition import NutritionLog
from app.models.pr_records import PersonalRecord
from app.models.sports_log import SportsLog
from app.models.user_data_record import UserDataRecord
from app.models.weight import WeightLog
from app.models.workout_log import WorkoutLog
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/insights", tags=["insights"])

SOURCE_LABELS = {
    "workouts": "Workout",
    "free_training": "Free training",
    "sports": "Sports",
    "daily_log": "Daily log",
    "water": "Hydration",
    "nutrition": "Nutrition",
    "journal": "Journal",
    "weight": "Body weight",
}


def _day(value) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _collect(db: Session, user_id: int) -> Dict[str, List[dict]]:
    """Return per-source entries as {day, ...} for the current user only."""
    out: Dict[str, List[dict]] = {key: [] for key in SOURCE_LABELS}

    nutrition_by_day: Dict[date, dict] = {}

    def add_nutrition(day, calories, protein):
        if day is None:
            return
        agg = nutrition_by_day.setdefault(day, {"day": day, "calories": 0, "protein": 0})
        agg["calories"] += calories
        agg["protein"] += protein

    for w in db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all():
        entry = {"day": _day(w.date), "minutes": w.duration_minutes or 0}
        out["workouts"].append(entry)
        if w.mode == "manual":
            out["free_training"].append(entry)
    for s in db.query(SportsLog).filter(SportsLog.user_id == user_id).all():
        out["sports"].append({"day": _day(s.date), "minutes": s.duration_minutes or 0})
    for d in db.query(DailyLog).filter(DailyLog.user_id == user_id).all():
        out["daily_log"].append({"day": _day(d.date)})
        add_nutrition(_day(d.date), d.calories or 0, d.protein or 0)
    for h in db.query(HydrationLog).filter(HydrationLog.user_id == user_id).all():
        out["water"].append({"day": _day(h.date), "ml": h.amount_ml or 0})
    # Consumption entries may include negative corrections, so totals are summed per day.
    for n in db.query(NutritionLog).filter(NutritionLog.user_id == user_id).all():
        add_nutrition(_day(n.recorded_at), n.calories or 0, n.protein or 0)
    out["nutrition"] = [
        e for e in nutrition_by_day.values() if e["calories"] > 0 or e["protein"] > 0
    ]
    for r in (
        db.query(UserDataRecord)
        .filter(UserDataRecord.user_id == user_id, UserDataRecord.collection == "journal")
        .all()
    ):
        data = r.data if isinstance(r.data, dict) else {}
        out["journal"].append({"day": _day(data.get("timestamp") or data.get("date")) or _day(r.created_at)})
    for w in db.query(WeightLog).filter(WeightLog.user_id == user_id).all():
        out["weight"].append({"day": _day(w.date), "kg": w.weight_kg})

    for key in out:
        out[key] = [e for e in out[key] if e["day"] is not None]
    return out


def _streak(days: set, today: date) -> dict:
    ordered = sorted(days)
    longest = run = 0
    prev = None
    for d in ordered:
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        longest = max(longest, run)
        prev = d
    cursor = today if today in days else today - timedelta(days=1)
    current = 0
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    return {
        "current": current,
        "longest": longest,
        "total_days": len(days),
        "last_active": ordered[-1].isoformat() if ordered else None,
    }


def _streaks(sources: Dict[str, List[dict]], today: date) -> dict:
    all_days = set()
    result = {}
    for key, entries in sources.items():
        days = {e["day"] for e in entries}
        all_days |= days
        result[key] = {"label": SOURCE_LABELS[key], **_streak(days, today)}
    return {"sources": result, "overall": {"label": "Any activity", **_streak(all_days, today)}}


@router.get("/streaks")
def streaks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return _streaks(_collect(db, user_id), datetime.utcnow().date())


def _achievements(sources: Dict[str, List[dict]], streak_data: dict, prs: int) -> List[dict]:
    total_workouts = len(sources["workouts"])
    minutes = sum(e["minutes"] for e in sources["workouts"]) + sum(e["minutes"] for e in sources["sports"])
    best_streak = streak_data["overall"]["longest"]
    sources_used = sum(1 for entries in sources.values() if entries)
    specs = [
        ("first-workout", "First Workout", "Log your first workout.", total_workouts, 1),
        ("workouts-10", "Consistent", "Log 10 workouts.", total_workouts, 10),
        ("workouts-50", "Dedicated", "Log 50 workouts.", total_workouts, 50),
        ("training-600", "Ten Hours", "Accumulate 600 minutes of training.", minutes, 600),
        ("streak-3", "Three-Day Streak", "Be active 3 days in a row.", best_streak, 3),
        ("streak-7", "Week Warrior", "Be active 7 days in a row.", best_streak, 7),
        ("streak-30", "Month of Discipline", "Be active 30 days in a row.", best_streak, 30),
        ("first-pr", "Personal Record", "Set your first personal record.", prs, 1),
        ("journal-5", "Reflective", "Write 5 journal entries.", len(sources["journal"]), 5),
        ("hydration-7", "Hydrated", "Log water on 7 different days.", len({e["day"] for e in sources["water"]}), 7),
        ("nutrition-7", "Fueled", "Log nutrition on 7 different days.", len({e["day"] for e in sources["nutrition"]}), 7),
        ("weigh-in-5", "Tracking Progress", "Log your body weight 5 times.", len(sources["weight"]), 5),
        ("well-rounded", "Well Rounded", "Log activity in 5 different areas.", sources_used, 5),
    ]
    return [
        {
            "id": key,
            "title": title,
            "description": desc,
            "progress": min(value, target),
            "target": target,
            "unlocked": value >= target,
        }
        for key, title, desc, value, target in specs
    ]


@router.get("/achievements")
def achievements(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    sources = _collect(db, user_id)
    prs = db.query(PersonalRecord).filter(PersonalRecord.user_id == user_id).count()
    items = _achievements(sources, _streaks(sources, datetime.utcnow().date()), prs)
    return {"unlocked": sum(1 for i in items if i["unlocked"]), "total": len(items), "items": items}


def _window(entries: List[dict], since: date) -> List[dict]:
    return [e for e in entries if e["day"] >= since]


@router.get("/summary")
def summary(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    today = datetime.utcnow().date()
    sources = _collect(db, user_id)
    streak_data = _streaks(sources, today)
    d7, d30 = today - timedelta(days=6), today - timedelta(days=29)
    training = sources["workouts"] + sources["sports"]
    counts = {
        key: {"total": len(e), "last_7_days": len(_window(e, d7)), "last_30_days": len(_window(e, d30))}
        for key, e in sources.items()
    }

    weeks = []
    for i in range(7, -1, -1):
        start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        end = start + timedelta(days=6)
        block = [e for e in training if start <= e["day"] <= end]
        weeks.append({
            "week_start": start.isoformat(),
            "sessions": len(block),
            "minutes": sum(e["minutes"] for e in block),
        })

    weights = sorted(sources["weight"], key=lambda e: e["day"])
    weight = {
        "latest_kg": weights[-1]["kg"] if weights else None,
        "first_kg": weights[0]["kg"] if weights else None,
        "change_kg": round(weights[-1]["kg"] - weights[0]["kg"], 2) if len(weights) > 1 else None,
        "entries": len(weights),
    }

    nutrition_days: Dict[date, dict] = {}
    for e in _window(sources["nutrition"], d30):
        agg = nutrition_days.setdefault(e["day"], {"calories": 0, "protein": 0})
        agg["calories"] += e["calories"]
        agg["protein"] += e["protein"]
    n = len(nutrition_days)
    nutrition = {
        "days_logged_30": n,
        "avg_calories": round(sum(v["calories"] for v in nutrition_days.values()) / n) if n else 0,
        "avg_protein": round(sum(v["protein"] for v in nutrition_days.values()) / n) if n else 0,
    }

    water_days: Dict[date, int] = {}
    for e in _window(sources["water"], d30):
        water_days[e["day"]] = water_days.get(e["day"], 0) + e["ml"]

    prs = db.query(PersonalRecord).filter(PersonalRecord.user_id == user_id).count()
    return {
        "counts": counts,
        "training": {
            "total_sessions": len(training),
            "total_minutes": sum(e["minutes"] for e in training),
            "minutes_last_7_days": sum(e["minutes"] for e in _window(training, d7)),
            "minutes_last_30_days": sum(e["minutes"] for e in _window(training, d30)),
            "active_days_last_30": len({e["day"] for e in _window(training, d30)}),
        },
        "weekly_trend": weeks,
        "personal_records": prs,
        "weight": weight,
        "nutrition": nutrition,
        "water": {
            "days_logged_30": len(water_days),
            "avg_ml_per_logged_day": round(sum(water_days.values()) / len(water_days)) if water_days else 0,
        },
        "streaks": {"overall": streak_data["overall"]},
    }

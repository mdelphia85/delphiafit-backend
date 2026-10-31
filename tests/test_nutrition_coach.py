import os
import tempfile
from datetime import date

import pytest

_db_file = os.path.join(tempfile.mkdtemp(), "nutrition_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402

from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.services.meal_plan import MealPlanError, generate_meal_plan  # noqa: E402
from app.services.nutrition_calc import calculate_targets, mifflin_st_jeor  # noqa: E402

run_migrations()
client = TestClient(app)


def _dob(age):
    today = date.today()
    return f"{today.year - age}-01-01"


PROFILE = {
    "dob": _dob(30), "current_weight": "180", "weight_unit": "lbs", "height": "70", "height_unit": "in",
    "sex": "male", "activity_level": "moderate",
}


def make_user(email):
    client.post("/auth/register", json={"name": email, "email": email, "password": "Passw0rd!x"})
    return login(email)


def login(email):
    r = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def set_profile(h, **overrides):
    body = {**PROFILE, "name": "Tester", **overrides}
    assert client.post("/profile/update", headers=h, json=body).status_code == 200


def set_settings(h, **fields):
    r = client.put("/nutrition-coach/settings", headers=h, json=fields)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- calculation ----------

def test_mifflin_reference_values():
    assert mifflin_st_jeor(80, 180, 30, "male") == pytest.approx(1780)
    assert mifflin_st_jeor(60, 165, 30, "female") == pytest.approx(600 + 1031.25 - 150 - 161)


def calc(goal, **kw):
    return calculate_targets(PROFILE, {"goal_type": goal, **kw})


def test_goal_scenarios():
    lose, keep, gain = calc("lose"), calc("maintain"), calc("gain")
    assert lose["status"] == keep["status"] == gain["status"] == "ready"
    m = keep["estimate"]["calories"]
    assert keep["estimate"]["calories"] == keep["estimate"]["maintenance_calories"]
    assert lose["estimate"]["calories"] < m < gain["estimate"]["calories"]
    # default 0.5 kg/week loss is about 550 kcal/day
    assert 500 <= m - lose["estimate"]["calories"] <= 600
    assert lose["estimate"]["protein_g"] > keep["estimate"]["protein_g"]
    for t in (lose, keep, gain):
        e = t["estimate"]
        assert abs(4 * e["protein_g"] + 4 * e["carbs_g"] + 9 * e["fat_g"] - e["calories"]) < 15


def test_safeguards():
    aggressive = calc("lose", weekly_rate=5, goal_unit="kg")
    assert aggressive["estimate"]["weekly_rate_kg"] >= -1.0
    assert aggressive["estimate"]["calories"] >= 1500
    assert any("capped" in n or "limited" in n for n in aggressive["notes"])
    small = calculate_targets({**PROFILE, "sex": "female", "current_weight": "100", "height": "60",
                               "activity_level": "sedentary"}, {"goal_type": "lose", "weekly_rate": 2})
    assert small["estimate"]["calories"] >= 1200
    minor = calculate_targets({**PROFILE, "dob": _dob(15)}, {"goal_type": "maintain"})
    assert minor["status"] == "invalid" and minor["effective"] is None


def test_missing_data_is_reported_not_invented():
    r = calculate_targets({"current_weight": "180"}, {})
    assert r["status"] == "incomplete" and r["estimate"] is None
    fields = {m["field"] for m in r["missing"]}
    assert {"dob", "height", "sex", "activity_level", "goal_type"} <= fields


def test_overrides_take_priority():
    r = calc("lose", calorie_override=2000, protein_override=150)
    assert r["effective"]["calories"] == 2000 and r["effective"]["protein_g"] == 150
    assert r["effective"]["source"] == "manual"
    assert r["estimate"]["calories"] != 2000


# ---------- meal plans ----------

@pytest.mark.parametrize("goal", ["lose", "maintain", "gain"])
@pytest.mark.parametrize("meals", [3, 4, 5])
def test_meal_plan_matches_targets(goal, meals):
    t = calc(goal)["effective"]
    plan = generate_meal_plan(t, meals_per_day=meals, seed=7)
    assert abs(plan["totals"]["calories"] - t["calories"]) / t["calories"] <= 0.05
    assert abs(plan["totals"]["protein_g"] - t["protein_g"]) / t["protein_g"] <= 0.08
    assert len(plan["meals"]) == meals


@pytest.mark.parametrize("diet,banned", [("vegan", {"Eggs", "Salmon, cooked", "Chicken breast, cooked",
                                                    "Greek yogurt, nonfat"}),
                                         ("vegetarian", {"Salmon, cooked", "Chicken breast, cooked"})])
def test_diets_respected(diet, banned):
    plan = generate_meal_plan(calc("maintain")["effective"], 5, diet=diet, seed=3)
    foods = {i["food"] for m in plan["meals"] for i in m["items"]}
    assert not foods & banned


def test_allergen_avoidance():
    plan = generate_meal_plan(calc("maintain")["effective"], 5, avoid=["nuts", "dairy", "gluten"], seed=5)
    foods = " ".join(i["food"] for m in plan["meals"] for i in m["items"])
    for word in ("Almonds", "Peanut", "yogurt", "Cottage", "Pasta", "oats", "bread"):
        assert word.lower() not in foods.lower()


def test_bad_inputs():
    with pytest.raises(MealPlanError):
        generate_meal_plan(calc("maintain")["effective"], 7)


# ---------- API: auth, persistence, isolation ----------

def test_requires_authentication():
    assert client.get("/nutrition-coach/targets").status_code == 401
    assert client.put("/nutrition-coach/settings", json={}).status_code == 401
    assert client.post("/nutrition-coach/meal-plans/generate").status_code == 401


def test_profile_changes_update_targets_and_persist_across_login():
    h = make_user("a@example.com")
    t = client.get("/nutrition-coach/targets", headers=h).json()
    assert t["status"] == "incomplete"

    set_profile(h)
    set_settings(h, goal_type="maintain")
    base = client.get("/nutrition-coach/targets", headers=h).json()
    assert base["status"] == "ready"

    set_profile(h, current_weight="200")
    heavier = client.get("/nutrition-coach/targets", headers=h).json()
    assert heavier["estimate"]["calories"] > base["estimate"]["calories"]

    set_profile(h, activity_level="sedentary")
    lazier = client.get("/nutrition-coach/targets", headers=h).json()
    assert lazier["estimate"]["calories"] < heavier["estimate"]["calories"]

    set_settings(h, goal_type="lose", diet="vegetarian", avoid=["nuts"], meals_per_day=4,
                 target_weight=170, weekly_rate=1, extras={"customGoal": "Run 5k"})
    new_h = login("a@example.com")  # "logout/login" on another device
    s = client.get("/nutrition-coach/settings", headers=new_h).json()
    assert (s["goal_type"], s["diet"], s["avoid"], s["meals_per_day"], s["target_weight"]) == \
        ("lose", "vegetarian", ["nuts"], 4, 170)
    assert s["extras"]["customGoal"] == "Run 5k"


def test_old_profile_clients_do_not_wipe_new_fields():
    h = make_user("old@example.com")
    set_profile(h)
    legacy = {k: PROFILE[k] for k in ("dob", "current_weight", "weight_unit", "height", "height_unit")}
    assert client.post("/profile/update", headers=h, json={"name": "x", **legacy}).status_code == 200
    got = client.get("/profile/get", headers=h).json()
    assert got["sex"] == "male" and got["activity_level"] == "moderate"


def test_override_clear_and_validation():
    h = make_user("ov@example.com")
    set_profile(h)
    set_settings(h, goal_type="maintain", calorie_override=2300, protein_override=170)
    eff = client.get("/nutrition-coach/targets", headers=h).json()["effective"]
    assert eff["calories"] == 2300 and eff["protein_g"] == 170
    set_settings(h, calorie_override=None, protein_override=None)
    assert client.get("/nutrition-coach/targets", headers=h).json()["effective"]["source"] == "estimate"
    assert client.put("/nutrition-coach/settings", headers=h, json={"calorie_override": 50}).status_code == 422
    assert client.put("/nutrition-coach/settings", headers=h, json={"diet": "carnivore"}).status_code == 422


def test_generate_requires_complete_profile():
    h = make_user("empty@example.com")
    r = client.post("/nutrition-coach/meal-plans/generate", headers=h)
    assert r.status_code == 422 and r.json()["detail"]["missing"]


def test_generation_saves_plan_but_logs_no_food():
    from app.database.connection import SessionLocal
    from app.models.daily_log import DailyLog
    from app.models.meals import Meal
    from app.models.nutrition import NutritionLog

    h = make_user("gen@example.com")
    set_profile(h)
    set_settings(h, goal_type="gain")

    def counts():
        db = SessionLocal()
        try:
            return tuple(db.query(m).count() for m in (DailyLog, Meal, NutritionLog))
        finally:
            db.close()

    before = counts()
    r = client.post("/nutrition-coach/meal-plans/generate", headers=h, json={"seed": 1})
    assert r.status_code == 200 and r.json()["plan"]["within_tolerance"]
    assert counts() == before
    assert client.get("/nutrition-coach/meal-plans/latest", headers=login("gen@example.com")).json()["plan"] \
        == r.json()["plan"]
    assert len(client.get("/nutrition-coach/meal-plans", headers=h).json()) == 1


def test_account_isolation():
    a, b = make_user("iso-a@example.com"), make_user("iso-b@example.com")
    set_profile(a)
    set_settings(a, goal_type="lose", calorie_override=1900)
    client.post("/nutrition-coach/meal-plans/generate", headers=a, json={"seed": 2})

    assert client.get("/nutrition-coach/settings", headers=b).json()["calorie_override"] is None
    assert client.get("/nutrition-coach/targets", headers=b).json()["status"] == "incomplete"
    assert client.get("/nutrition-coach/meal-plans/latest", headers=b).json()["plan"] is None
    assert client.get("/nutrition-coach/meal-plans", headers=b).json() == []


def test_migration_is_idempotent_and_preserves_rows():
    from sqlalchemy import text
    from app.database.connection import engine

    h = make_user("mig@example.com")
    set_profile(h)
    run_migrations()
    run_migrations()
    with engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM user_profiles WHERE sex='male'")).scalar() >= 1
    assert client.get("/profile/get", headers=h).json()["current_weight"] == "180"

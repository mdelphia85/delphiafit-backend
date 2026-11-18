"""Meal suggestion generator that scales portions to calculated macro targets.

Macro values are approximate per-100 g figures for common foods (USDA
FoodData Central style, cooked/prepared weights as noted). Portions are
rounded to practical increments, so totals are estimates.
"""

import random
from typing import Optional

# name, role, kcal, protein, carbs, fat (per 100 g), step (g), max (g), tags, unit_g, unit_name, meals
# tags: foods carrying any of these are removed for matching diets/avoid lists.
_F = []


def _food(name, role, kcal, p, c, f, step=5, max_g=400, tags=(), unit_g=None, unit=None, slots=("main",)):
    _F.append({
        "name": name, "role": role, "kcal": kcal, "p": p, "c": c, "f": f,
        "step": step, "max": max_g, "tags": set(tags), "unit_g": unit_g, "unit": unit, "slots": set(slots),
    })


# Proteins (main meals)
_food("Chicken breast, cooked", "protein", 165, 31, 0, 3.6, 5, 350, {"meat"})
_food("Turkey breast, cooked", "protein", 135, 30, 0, 0.7, 5, 350, {"meat"})
_food("Lean ground beef, cooked", "protein", 217, 26, 0, 12, 5, 300, {"meat"})
_food("Salmon, cooked", "protein", 206, 22, 0, 12, 5, 300, {"fish"})
_food("White fish (cod), cooked", "protein", 105, 23, 0, 0.9, 5, 350, {"fish"})
_food("Eggs", "protein", 143, 12.6, 0.7, 9.5, 50, 300, {"egg"}, 50, "large egg", ("breakfast",))
_food("Egg whites", "protein", 52, 11, 0.7, 0.2, 30, 360, {"egg"}, 30, "egg white", ("breakfast",))
_food("Firm tofu", "protein", 144, 17, 3, 8.7, 5, 350, {"soy"})
_food("Tempeh", "protein", 192, 20, 7.6, 11, 5, 250, {"soy"})
_food("Lentils, cooked", "protein", 116, 9, 20, 0.4, 5, 450, ())
_food("Chickpeas, cooked", "protein", 164, 8.9, 27, 2.6, 5, 400, ())
# Proteins (snacks)
_food("Greek yogurt, nonfat", "protein", 59, 10, 3.6, 0.4, 5, 400, {"dairy"}, slots=("snack",))
_food("Cottage cheese, low-fat", "protein", 82, 11, 3.4, 2.3, 5, 350, {"dairy"}, slots=("snack",))
_food("Edamame, cooked", "protein", 121, 12, 9, 5.2, 5, 300, {"soy"}, slots=("snack",))
_food("Hummus", "protein", 166, 8, 14, 10, 5, 200, (), slots=("snack",))
_food("Tuna, canned in water", "protein", 116, 26, 0, 0.8, 5, 250, {"fish"}, slots=("snack",))
_food("Roasted chickpeas", "protein", 364, 19, 61, 6, 5, 120, (), slots=("snack",))

# Carbohydrates (main)
_food("White rice, cooked", "carbs", 130, 2.7, 28, 0.3, 5, 600, ())
_food("Brown rice, cooked", "carbs", 123, 2.7, 26, 1, 5, 600, ())
_food("Pasta, cooked", "carbs", 158, 5.8, 31, 0.9, 5, 550, {"gluten"})
_food("Sweet potato, baked", "carbs", 90, 2, 21, 0.2, 5, 650, ())
_food("Potato, boiled", "carbs", 87, 1.9, 20, 0.1, 5, 700, ())
_food("Quinoa, cooked", "carbs", 120, 4.4, 21, 1.9, 5, 550, ())
_food("Rolled oats, dry", "carbs", 389, 16.9, 66, 6.9, 5, 150, {"gluten"}, slots=("breakfast",))
_food("Whole-wheat bread", "carbs", 247, 13, 41, 3.4, 30, 180, {"gluten"}, 30, "slice", ("breakfast",))
# Carbohydrates (snack)
_food("Banana", "carbs", 89, 1.1, 23, 0.3, 120, 240, (), 120, "medium banana", ("snack",))
_food("Apple", "carbs", 52, 0.3, 14, 0.2, 180, 360, (), 180, "medium apple", ("snack",))
_food("Rice cakes", "carbs", 387, 8, 82, 3, 9, 90, (), 9, "cake", ("snack",))
_food("Blueberries", "carbs", 57, 0.7, 14, 0.3, 5, 300, (), slots=("snack",))
_food("Oat cereal, dry", "carbs", 379, 13, 68, 6.5, 5, 120, {"gluten"}, slots=("snack",))

# Vegetables
_food("Broccoli, steamed", "veggies", 35, 2.4, 7.2, 0.4, 5, 250, (), slots=("main",))
_food("Spinach, cooked", "veggies", 23, 3, 3.8, 0.3, 5, 250, (), slots=("main",))
_food("Bell peppers", "veggies", 31, 1, 6, 0.3, 5, 250, (), slots=("main", "snack"))
_food("Green beans, cooked", "veggies", 35, 1.9, 7.9, 0.3, 5, 250, (), slots=("main",))
_food("Carrots", "veggies", 41, 0.9, 10, 0.2, 5, 200, (), slots=("snack",))
_food("Cucumber", "veggies", 15, 0.7, 3.6, 0.1, 5, 250, (), slots=("snack",))

# Fats
_food("Olive oil", "fats", 884, 0, 0, 100, 5, 25, (), 5, "tsp", ("main",))
_food("Avocado", "fats", 160, 2, 8.5, 14.7, 5, 200, (), slots=("main", "breakfast"))
_food("Almonds", "fats", 579, 21, 22, 50, 5, 45, {"nuts"}, slots=("breakfast", "main"))
_food("Peanut butter", "fats", 588, 25, 20, 50, 5, 40, {"nuts"}, slots=("breakfast",))
_food("Chia seeds", "fats", 486, 17, 42, 31, 5, 30, (), slots=("breakfast",))

DIET_EXCLUDES = {
    "none": set(),
    "pescatarian": {"meat"},
    "vegetarian": {"meat", "fish"},
    "vegan": {"meat", "fish", "egg", "dairy"},
}
ALLERGENS = {"dairy", "egg", "fish", "nuts", "gluten", "soy"}

# Share of daily macros per meal, in display order.
MEAL_LAYOUTS = {
    3: [("breakfast", 0.30), ("lunch", 0.35), ("dinner", 0.35)],
    4: [("breakfast", 0.27), ("lunch", 0.30), ("snack1", 0.13), ("dinner", 0.30)],
    5: [("breakfast", 0.25), ("snack1", 0.10), ("lunch", 0.30), ("snack2", 0.10), ("dinner", 0.25)],
}
ROLES = {
    "breakfast": ("protein", "carbs", "veggies", "fats"),
    "lunch": ("protein", "carbs", "veggies", "fats"),
    "dinner": ("protein", "carbs", "veggies", "fats"),
    "snack1": ("protein", "carbs", "veggies"),
    "snack2": ("protein", "carbs", "veggies"),
}
TOLERANCE = {"calories": 0.05, "protein": 0.08}


class MealPlanError(ValueError):
    pass


def _slot_kind(meal: str) -> str:
    return "snack" if meal.startswith("snack") else ("breakfast" if meal == "breakfast" else "main")


def _eligible(role, meal, diet, avoid):
    excluded = set(DIET_EXCLUDES.get(diet, set())) | {a for a in avoid if a in ALLERGENS}
    slot = _slot_kind(meal)

    def pick(kind):
        return [f for f in _F if f["role"] == role and kind in f["slots"] and not (f["tags"] & excluded)]

    pool = pick(slot)
    # Breakfast-specific foods are preferred; otherwise fall back to main-meal foods.
    return pool or (pick("main") if slot == "breakfast" else [])


def _amount(food, grams):
    grams = max(0, min(grams, food["max"]))
    step = food["step"]
    return int(round(grams / step)) * step


def _macros(food, grams):
    k = grams / 100
    return {"calories": food["kcal"] * k, "protein": food["p"] * k, "carbs": food["c"] * k, "fat": food["f"] * k}


def _sum(items):
    total = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for it in items:
        for key in total:
            total[key] += it[key]
    return total


def _solve_meal(meal, target, foods, veg_g):
    """Iteratively size protein, carb and fat sources to hit a meal's macros."""
    amounts = {role: 0.0 for role in foods}
    if "veggies" in foods:
        amounts["veggies"] = veg_g
    for _ in range(60):
        for role, key in (("protein", "protein"), ("carbs", "carbs"), ("fats", "fat")):
            if role not in foods:
                continue
            food = foods[role]
            others = _sum([_macros(foods[r], amounts[r]) for r in foods if r != role])
            per_g = {"protein": food["p"], "carbs": food["c"], "fat": food["f"]}[key] / 100
            if per_g <= 0:
                continue
            need = target[key] - others[key]
            amounts[role] = max(0.0, min(food["max"], need / per_g))
    return {role: _amount(foods[role], g) for role, g in amounts.items()}


def _item_dict(role, food, grams):
    m = _macros(food, grams)
    portion = f"{grams} g"
    if food["unit_g"]:
        count = grams / food["unit_g"]
        count_txt = f"{count:.0f}" if abs(count - round(count)) < 0.05 else f"{count:.1f}"
        portion = f"{count_txt} {food['unit']}{'' if count_txt == '1' else 's'} ({grams} g)"
    return {
        "role": role, "food": food["name"], "grams": grams, "portion": portion,
        "calories": round(m["calories"]), "protein_g": round(m["protein"], 1),
        "carbs_g": round(m["carbs"], 1), "fat_g": round(m["fat"], 1),
    }


def generate_meal_plan(targets: dict, meals_per_day: int = 5, diet: str = "none",
                       avoid: Optional[list] = None, seed: Optional[int] = None) -> dict:
    """Build a one-day plan. `targets` needs calories, protein_g, carbs_g, fat_g."""
    if meals_per_day not in MEAL_LAYOUTS:
        raise MealPlanError("meals_per_day must be 3, 4 or 5")
    if diet not in DIET_EXCLUDES:
        raise MealPlanError("Unknown dietary preference")
    avoid = [a for a in (avoid or []) if a in ALLERGENS]
    rng = random.Random(seed)

    remaining = {"calories": targets["calories"], "protein": targets["protein_g"],
                 "carbs": targets["carbs_g"], "fat": targets["fat_g"]}
    layout = MEAL_LAYOUTS[meals_per_day]
    weights_left = sum(w for _, w in layout)
    used_foods = set()
    out_meals = []

    for meal, weight in layout:
        share = weight / weights_left
        meal_target = {k: max(v, 0) * share for k, v in remaining.items()}
        best = None
        for _attempt in range(8):
            foods = {}
            for role in ROLES[meal]:
                pool = _eligible(role, meal, diet, avoid)
                if not pool:
                    if role == "fats":
                        continue
                    raise MealPlanError(f"No {role} options match your dietary preferences for {meal}.")
                fresh = [f for f in pool if f["name"] not in used_foods] or pool
                foods[role] = rng.choice(fresh)
            veg_g = 0 if "veggies" not in foods else (80 if _slot_kind(meal) == "snack" else 120)
            amounts = _solve_meal(meal, meal_target, foods, veg_g)
            items = [_item_dict(role, foods[role], g) for role, g in amounts.items() if g > 0]
            totals = _sum([{"calories": i["calories"], "protein": i["protein_g"], "carbs": i["carbs_g"],
                            "fat": i["fat_g"]} for i in items])
            error = sum(abs(totals[k] - meal_target[k]) / max(meal_target[k], 1) for k in totals)
            if best is None or error < best[0]:
                best = (error, foods, items, totals)
        _, foods, items, totals = best
        used_foods.update(f["name"] for f in foods.values())
        for key in remaining:
            remaining[key] -= totals[key]
        weights_left -= weight
        out_meals.append({
            "meal": meal, "items": items,
            "totals": {"calories": round(totals["calories"]), "protein_g": round(totals["protein"]),
                       "carbs_g": round(totals["carbs"]), "fat_g": round(totals["fat"])},
        })

    day = _sum([{"calories": m["totals"]["calories"], "protein": m["totals"]["protein_g"],
                 "carbs": m["totals"]["carbs_g"], "fat": m["totals"]["fat_g"]} for m in out_meals])
    day_totals = {"calories": round(day["calories"]), "protein_g": round(day["protein"]),
                  "carbs_g": round(day["carbs"]), "fat_g": round(day["fat"])}
    notes = []
    cal_off = abs(day_totals["calories"] - targets["calories"]) / max(targets["calories"], 1)
    pro_off = abs(day_totals["protein_g"] - targets["protein_g"]) / max(targets["protein_g"], 1)
    on_target = cal_off <= TOLERANCE["calories"] and pro_off <= TOLERANCE["protein"]
    if not on_target:
        notes.append("Portions hit practical limits, so this plan is not exactly on target. "
                     "Add more meals or snacks, or adjust portions, to close the gap.")
    return {
        "meals_per_day": meals_per_day,
        "diet": diet,
        "avoid": avoid,
        "targets": {"calories": targets["calories"], "protein_g": targets["protein_g"],
                    "carbs_g": targets["carbs_g"], "fat_g": targets["fat_g"]},
        "totals": day_totals,
        "within_tolerance": on_target,
        "meals": out_meals,
        "notes": notes,
        "estimate_label": "Estimated portions and macros (approximate food values; cooked weights).",
    }

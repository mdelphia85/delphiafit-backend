"""Short, stateful, no-cost workout-modification dialogue for reported knee pain.

Each response asks only the next useful question. The state is stored in the
authenticated user's existing AI coaching record, never in a shared variable.
"""
import re

from app.services.injury_workout import _duration_minutes, _upper_body_options

_KNEE = re.compile(r"\bknees?\b", re.I)
_SYMPTOM = re.compile(r"\b(pain|hurt|hurts|injur\w*|sore|aching|ache)\b", re.I)
_WORKOUT = re.compile(
    r"\b(workout|work out|exercise|training|train|cardio|strength|lift|"
    r"modify|modified|plan|routine|what can i do)\b", re.I
)
_URGENT = re.compile(
    r"\b(chest pain|shortness of breath|difficulty breathing|"
    r"can't bear weight|cannot bear weight|unable to bear weight|"
    r"severe\s+(?:[a-z-]+\s+){0,3}pain|deform\w*)\b", re.I
)
_CANNOT_SIT = re.compile(
    r"\b(can't|cannot|unable to|can't even)\s+sit\b|"
    r"\bsitt?ing\s+(?:is\s+)?(?:painful|hurts|causes pain)\b|"
    r"\bpain\s+(?:when|while)\s+sitt?ing\b", re.I
)
_CAN_SIT = re.compile(
    r"\b(can|able to|okay to|ok to)\s+sit\b|"
    r"\bsitt?ing\s+(?:is\s+)?(?:fine|ok|okay|comfortable|painless)\b|"
    r"\bno pain\s+(?:when|while)\s+sitt?ing\b", re.I
)


def _goal(text: str) -> str | None:
    if re.search(r"\b(cardio|endurance|aerobic)\b", text, re.I):
        return "cardio"
    if re.search(r"\b(strength|weights?|lifting|muscle|hypertrophy)\b", text, re.I):
        return "strength"
    return None


def _equipment(text: str) -> str | None:
    if re.search(r"\b(no equipment|none|nothing|bodyweight|body weight)\b", text, re.I):
        return "bodyweight"
    if re.search(r"\b(dumbbells?|hand weights?)\b", text, re.I):
        return "dumbbell"
    if re.search(r"\b(resistance bands?|exercise bands?|bands?)\b", text, re.I):
        return "band"
    if re.search(r"\b(gym machines?|machines?|gym)\b", text, re.I):
        return "gym"
    return None


def _ask(question: str, stage: str, state: dict) -> dict:
    return {
        "coach_response": question,
        "coach_state": {**state, "stage": stage},
    }


def _plan(state: dict, user_data: dict) -> dict:
    initial = str(state.get("original", ""))
    equipment = state["equipment"]
    goal = state["goal"]
    time = int(state.get("minutes") or _duration_minutes(initial, user_data))
    side_match = re.search(r"\b(right|left)\s+knee\b", initial, re.I)
    side = f"{side_match.group(1).lower()} " if side_match else ""
    start = (
        f"Based on what you told me, here's a possible modification for {side}knee pain. "
        "I can't tell whether your knee is safe to exercise; if pain is unexplained or "
        "worsening, get professional advice before training. Stop anything that hurts. "
        "These are options only if you can sit comfortably and have no restrictions.\n\n"
    )
    if goal == "cardio":
        content = (
            f"For a cardio session of up to {time} minutes, avoid knee-loading intervals. "
            "If you have a seated arm cycle and it causes no knee pain, try a few easy "
            "30–60-second intervals with generous rest. Without one, seated arm movements "
            "are gentle movement, not a replacement cardio workout."
        )
    else:
        options, note = _upper_body_options(equipment)
        sets = "1 set of 6–10" if time <= 10 else "1–2 sets of 8–12"
        content = (
            f"For your {time}-minute strength session, skip movements that aggravate "
            "your knee, including squats, lunges and step-ups for now. "
            f"Consider {sets} comfortable repetitions of these seated options, with rest:\n"
            + "\n".join(f"- {item}" for item in options[:2])
            + f"\n{note}"
        )
    return {
        "coach_response": start + content + "\n\nWould you like to adjust the time or equipment?",
        "coach_state": {**state, "stage": "plan"},
    }


def guided_knee_reply(message: str, user_data: dict, prior_state: dict | None) -> dict | None:
    """Return the next brief question/plan, or None for unrelated conversation."""
    message = message.strip()
    state = dict(prior_state or {})
    stage = state.get("stage")

    # Don't carry an old knee conversation into an explicitly new topic.
    if re.search(r"\b(new topic|different question|start over|forget the knee)\b", message, re.I):
        return None

    starting = bool(_KNEE.search(message) and _SYMPTOM.search(message) and _WORKOUT.search(message))
    if not stage and not starting:
        return None

    # Safety screen on EVERY new answer, not just on the first question.
    if _URGENT.search(message):
        return {
            "coach_response": (
                "Do not exercise with those symptoms. Seek urgent medical assessment; "
                "for chest pain or breathing difficulty, contact emergency services. "
                "I can't determine whether exercising is safe."
            )
        }

    if not stage:
        state = {
            "stage": "symptoms",
            "original": message[:500],
            "minutes": _duration_minutes(message, user_data),
        }
        return _ask(
            "For knee pain, I can help modify your workout, but this is not "
            "clearance to train. First: which movements hurt your knee, "
            "and can you sit comfortably without pain?",
            "symptoms", state,
        )

    if stage == "symptoms":
        if _CANNOT_SIT.search(message):
            return {
                "coach_response": (
                    "If sitting also hurts, I can't safely suggest a seated alternative. "
                    "Please have the knee evaluated before trying a replacement workout."
                )
            }
        if not _CAN_SIT.search(message):
            return _ask(
                "Thanks. Can you sit comfortably without knee pain? "
                "A simple yes or no is fine.",
                "sit_check", {**state, "movement": message[:300]},
            )
        state["movement"] = message[:300]
        state["sit_ok"] = True
        if _goal(state.get("original", "")):
            state["goal"] = _goal(state["original"])
            return _ask(
                "Got it. Do you have dumbbells, resistance bands, gym machines, or no equipment?",
                "equipment", state,
            )
        return _ask(
            "Got it. Is the workout you're modifying mainly strength training or cardio?",
            "goal", state,
        )

    if stage == "sit_check":
        if _CANNOT_SIT.search(message) or message.casefold() in {"no", "nope"}:
            return {
                "coach_response": (
                    "If sitting causes knee pain, I can't safely recommend a seated "
                    "replacement workout. Get advice from a qualified clinician first."
                )
            }
        if not (_CAN_SIT.search(message) or message.casefold() in {"yes", "yep", "yeah"}):
            return _ask("Can you sit without knee pain — yes or no?", "sit_check", state)
        state["sit_ok"] = True
        if _goal(state.get("original", "")):
            state["goal"] = _goal(state["original"])
            return _ask("What equipment do you have: dumbbells, bands, gym machines, or none?", "equipment", state)
        return _ask("Are we modifying a strength workout or cardio?", "goal", state)

    if stage == "goal":
        goal = _goal(message)
        if goal is None:
            return _ask("Strength training or cardio?", "goal", state)
        state["goal"] = goal
        return _ask(
            "What equipment do you have: dumbbells, resistance bands, gym machines, or none?",
            "equipment", state,
        )

    if stage == "equipment":
        equipment = _equipment(message)
        if equipment is None:
            return _ask("Do you have dumbbells, bands, gym machines, or no equipment?", "equipment", state)
        state["equipment"] = equipment
        return _plan(state, user_data)

    if stage == "plan":
        time_match = re.search(r"\b(\d{1,3})\s*[- ]?\s*minutes?\b", message, re.I)
        equipment = _equipment(message)
        goal = _goal(message)
        if time_match or equipment or goal:
            if time_match:
                state["minutes"] = max(5, min(int(time_match.group(1)), 45))
            if equipment:
                state["equipment"] = equipment
            if goal:
                state["goal"] = goal
            return _plan(state, user_data)
        return None

    return None

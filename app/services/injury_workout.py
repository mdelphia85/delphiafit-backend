"""Question-specific, no-cost workout modifications for reported knee pain.

Suggestions are conditional examples, not diagnosis, medical clearance, or a
guarantee that an activity cannot aggravate an injury. The workout options are
intentionally limited to lower-knee-load exercises, and only when comfortable.
"""
import re


_WORKOUT_WORDS = re.compile(
    r"\b(workout|workouts|work out|exercise|exercises|train|training|"
    r"routine|session|plan|cardio|endurance|strength|muscle|lift|"
    r"modify|modified|adapt|alternative|what can i do)\b"
)
_CARDIO_WORDS = re.compile(r"\b(cardio|endurance|aerobic|heart rate)\b")
_MUSCLE_WORDS = re.compile(
    r"\b(build|building|muscle|hypertrophy|strength|weights|lifting)\b"
)


def _duration_minutes(message: str, user_data: dict) -> int:
    explicit = re.search(r"\b(\d{1,3})\s*[- ]?\s*(?:min(?:ute)?s?)\b", message)
    duration = explicit.group(1) if explicit else next(
        (
            user_data[key]
            for key in ("available_minutes", "time_minutes", "duration_minutes", "session_minutes")
            if user_data.get(key) is not None
        ),
        15,
    )
    try:
        minutes = int(duration)
    except (TypeError, ValueError):
        minutes = 15
    return max(5, min(minutes, 45))


def _equipment(message: str, user_data: dict) -> str:
    supplied = str(user_data.get("equipment") or "")
    context = f"{message} {supplied}".lower()
    if re.search(r"\b(no equipment|without equipment|bodyweight|body weight)\b", context):
        return "bodyweight"
    if re.search(r"\b(dumbbells?|hand weights?|free weights?)\b", context):
        return "dumbbell"
    if re.search(r"\b(resistance bands?|exercise bands?|bands?)\b", context):
        return "band"
    if re.search(r"\b(gym|machines?|cable stations?)\b", context):
        return "gym"
    if re.search(r"\b(at home|home workout)\b", context):
        return "bodyweight"
    return "unspecified"


def _upper_body_options(equipment: str) -> tuple[list[str], str]:
    """Avoid lower-body loading, unsafe improvised anchors, and unsupported promises."""
    if equipment == "dumbbell":
        return (
            [
                "Seated light dumbbell curls, back supported if possible.",
                "Seated light dumbbell lateral raises, arms below shoulder height if comfortable.",
                "Seated light triceps extensions with one light weight, if comfortable.",
            ],
            "Use light dumbbells you already control; do not brace or push through your knees.",
        )
    if equipment == "band":
        return (
            [
                "Seated resistance-band rows with the band attached to a securely rated anchor.",
                "Seated light band chest presses with a secure anchor, if comfortable.",
                "Seated light band elbow extensions, if comfortable.",
            ],
            "Do not improvise an anchor or loop the band under the painful knee.",
        )
    if equipment == "gym":
        return (
            [
                "A light seated chest-press machine without leg drive.",
                "A seated row machine that does not require pushing through your legs.",
                "A seated biceps-curl machine or supported light dumbbell curls.",
            ],
            "Choose machines with back support; avoid setups needing knee pressure or a forceful leg drive.",
        )
    if equipment == "bodyweight":
        return (
            [
                "Seated shoulder-blade squeezes with relaxed shoulders.",
                "Seated gentle arm raises through a comfortable range.",
                "Seated elbow bends and straightens at a slow, comfortable pace.",
            ],
            "With no resistance equipment, this is a gentle upper-body movement session, not a full strength substitute.",
        )
    return (
        [
            "Seated light biceps curls if you have light dumbbells; otherwise gentle elbow bends.",
            "Seated rows using a properly anchored resistance band, if available.",
            "Seated gentle shoulder-blade squeezes without resistance.",
        ],
        "Tell me whether you have dumbbells, resistance bands, or gym machines so I can select one equipment-specific version.",
    )


def modified_knee_workout(user_data: dict, message: str) -> str:
    """Suggest a conditional, request-specific alternative while protecting safety boundaries."""
    question = message.lower()
    if not _WORKOUT_WORDS.search(question):
        return (
            "For knee pain, which movements make it worse, and when did it begin? "
            "I can suggest a knee-sparing workout modification if you want one, "
            "but I cannot determine whether exercising with the injury is safe."
        )

    side_match = re.search(r"\b(right|left)\s+knee\b", question)
    side = f"{side_match.group(1)} " if side_match else ""
    minutes = _duration_minutes(question, user_data)
    equipment = _equipment(question, user_data)
    cardio = bool(_CARDIO_WORDS.search(question))
    strength = bool(_MUSCLE_WORDS.search(question))

    try:
        fatigue = float(user_data.get("fatigue", 0))
    except (TypeError, ValueError):
        fatigue = 0

    intro = (
        f"With {side}knee pain, I'd modify your workout to avoid loading or twisting "
        "the painful knee. Only consider the seated options below if sitting and "
        "moving your arms are comfortable and you have no exercise restrictions. "
        "Since no workout can be guaranteed not to worsen an injury, take care with any movement. Stop if pain increases, "
        "and consult a qualified healthcare professional for new or worsening symptoms; seek urgent care "
        "for severe pain, marked swelling, or trouble bearing weight. "
        "This is not clearance to train.\n\n"
    )

    if fatigue >= 8:
        return (
            intro
            + "With the fatigue you reported, consider rest today rather than a workout. "
            "If a clinician has cleared light movement, keep it very gentle and short. "
            "What is causing the knee pain, and do you have exercise restrictions?"
        )

    if cardio:
        return (
            intro
            + f"Knee-sparing cardio alternative (up to {minutes} minutes):\n"
            "- 2 minutes: gentle seated arm and shoulder movement to warm up.\n"
            "- If you have access to a seated upper-body ergometer (arm cycle) and can use "
            "it without knee movement or pain: alternate 30-60 seconds of easy arm cycling "
            "with 60 seconds of rest. Start with a few comfortable intervals rather than "
            "trying to fill the entire time.\n"
            "- 2 minutes: gentle seated arm movement to cool down.\n"
            "Avoid running, jumping, stair intervals, hard cycling, or movements that "
            "load or twist the knee until a clinician advises what is appropriate. "
            "Without an arm cycle, don't assume seated arm motions provide an equivalent "
            "cardio workout.\n\n"
            "Do you have an arm cycle, and which knee movements or positions hurt?"
        )

    exercises, equipment_note = _upper_body_options(equipment)
    sets = 1 if minutes <= 10 else 2
    reps = "6-10" if minutes <= 10 else "8-12"
    focus = "upper-body strength" if strength else "upper-body workout"
    return (
        intro
        + f"Modified {focus} option (about {minutes} minutes, only if comfortable):\n"
        + "- Warm-up: 2-3 minutes of gentle seated arm and shoulder movement.\n"
        + f"- Main work: {sets} set{'s' if sets != 1 else ''} of {reps} controlled repetitions "
        "for each comfortable option below, resting about 60 seconds as needed:\n"
        + "\n".join(f"  - {exercise}" for exercise in exercises)
        + "\n- Cool-down: gentle arm movement and relaxed breathing.\n"
        + "Skip squats, lunges, step-ups, jumping, running, and deep knee bends for now "
        "rather than pushing through the pain.\n"
        + equipment_note + "\n\n"
        + "Do you have gym equipment, dumbbells, or bands? I can swap these options "
        "to match your equipment and the movements that bother your knee."
    )

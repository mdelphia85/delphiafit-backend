"""No-cost, symptom-aware workout modifications across common complaints.

Advice is conditional and educational, not a diagnosis, clearance to train,
or a promise that movements are safe for a particular injury.
"""
import re

_SYMPTOM = re.compile(
    r"\b(pain|painful|hurt|hurts|hurting|injur\w*|ache|aches|aching|headaches?|"
    r"migraine|sore|soreness|stiff\w*|swoll\w*|sprain\w*|strain\w*|"
    r"bruis\w*|tendinitis|tendonitis|arthritis|bursitis|sciatica|"
    r"plantar fasciitis|sick|illness|flu|fever|cough|cold|"
    r"nausea|nauseous|vomit\w*|dizz\w*|faint\w*|infection|"
    r"concussion|asthma|wheezing|fatigue|exhausted|cramps?|cramping|"
    r"spasms?|tightness|chills|congestion|unwell|sore throat)\b", re.I
)
_URGENT = re.compile(
    r"\b(chest pain|difficulty breathing|shortness of breath|"
    r"can't bear weight|cannot bear weight|unable to bear weight|"
    r"deform\w*|severe pain|severe\s+(?:[a-z-]+\s+){0,3}pain|"
    r"loss of (?:bowel|bladder) control|new (?:bowel|bladder) problems|"
    r"numbness (?:around|in) (?:the )?groin|saddle numbness|"
    r"(?:new|worsening|progressive) leg weakness|"
    r"fainting|sudden worst headache|worst headache of my life)\b", re.I
)
_SYSTEMIC = re.compile(
    r"\b(fever|flu|infection|vomit\w*|nauseous|nausea|"
    r"dizz\w*|faint\w*|concussion|wheez\w*|asthma attack|"
    r"cold|cough|congestion|chills|sore throat|unwell|illness|sick)\b", re.I
)
_FATIGUE = re.compile(r"\b(fatigue|exhausted|run down|worn out)\b", re.I)
_HEAD = re.compile(r"\b(headaches?|migraine|head pain|head injury)\b", re.I)
_WORKOUT = re.compile(
    r"\b(workout|workouts|work out|exercise|exercises|train\w*|"
    r"routine|session|plan|cardio|lifting|lift|weights|gym|"
    r"build muscle|strength|endurance|modify|modified|adapt|"
    r"what (?:can|should) i do)\b", re.I
)
_AREAS = (
    ("back", re.compile(r"\b(lower back|low back|upper back|mid back|back|lumbar|"
                        r"spine|spinal|sciatica)\b", re.I)),
    ("neck", re.compile(r"\b(neck|cervical)\b", re.I)),
    ("lower-body", re.compile(
        r"\b(knees?|hips?|ankles?|feet|foot|toes?|heels?|shins?|calves?|calf|"
        r"legs?|thighs?|hamstrings?|quadriceps|quads?|groin|achilles|"
        r"plantar fasciitis)\b", re.I)),
    ("upper-body", re.compile(
        r"\b(shoulders?|rotator cuff|elbows?|wrists?|hands?|fingers?|thumbs?|"
        r"arms?|forearms?|biceps?|triceps?)\b", re.I)),
    ("trunk", re.compile(r"\b(abdomen|abdominal|stomach|ribs?|chest)\b", re.I)),
)


def is_condition_question(message: str, context: str = "") -> bool:
    return bool(_SYMPTOM.search(message + " " + context) or _URGENT.search(message + " " + context))


def _location(context: str) -> tuple[str | None, str | None, int]:
    found = [(kind, m.group(0).lower()) for kind, pattern in _AREAS
             if (m := pattern.search(context))]
    if not found:
        return None, None, 0
    return found[0][0], found[0][1], len(found)


def adapt_workout(user_data: dict, message: str, context: str) -> str:
    """Give an actual lower-strain alternative where possible, before a question."""
    if _URGENT.search(context):
        return (
            "Do not exercise based on this guidance. These symptoms may require "
            "urgent medical assessment. Seek appropriate urgent care or emergency "
            "services rather than trying to train through them. "
            "I cannot diagnose or clear you for exercise."
        )

    if _SYSTEMIC.search(context):
        return (
            "With the illness or symptoms you described, skip a structured or "
            "intense workout for now, especially with fever, dizziness, vomiting, "
            "or breathing symptoms. Rest and recover; consider gentle activity "
            "only once you feel well and it is appropriate for your condition. "
            "Ask a healthcare professional if symptoms persist or worsen. "
            "Do not use exercise to push through illness."
        )

    if _FATIGUE.search(context):
        return (
            "With the fatigue you described, consider a rest day rather than "
            "pushing through a demanding workout. If comfortable, a short "
            "easy walk or gentle mobility may be a recovery option, but "
            "stop if you feel worse. Unusual or persistent fatigue deserves "
            "medical advice; don't use training to push through feeling unwell."
        )

    if _HEAD.search(context):
        return (
            "For a headache or migraine, an intense workout may aggravate symptoms. "
            "Rest in a comfortable environment and consider only gentle movement "
            "if it does not worsen symptoms. Seek medical advice for new or unusual "
            "headaches, and urgent assessment for sudden, severe or neurological "
            "symptoms. A workout is not the priority while symptoms are active."
        )

    area, name, area_count = _location(context)
    try:
        fatigue = float(user_data.get("fatigue") or 0)
    except (TypeError, ValueError):
        fatigue = 0

    safety = (
        "Stop if symptoms increase; no workout is guaranteed not to aggravate "
        "an injury. This is not clearance to train or a diagnosis. "
        "A qualified healthcare professional can advise on your specific "
        "restrictions. Seek urgent care for severe pain, significant swelling, "
        "a deformity, or inability to bear weight."
    )
    if fatigue >= 8:
        return (
            "With pain or injury and the high fatigue you reported, consider a "
            "recovery day instead of a workout. If comfortable, gentle movement "
            "or position changes are an option, not a requirement. "
            + safety
        )
    if area_count > 1:
        return (
            "Because you mentioned symptoms in more than one area, I would "
            "avoid prescribing a full exercise circuit that could stress one of "
            "them. A short easy walk or gentle position change only if all "
            "affected areas tolerate it is a more conservative option. "
            + safety + " Which area currently limits your movement most?"
        )
    if not area:
        return (
            "You can still work around some discomfort, but the affected area "
            "isn't clear yet. For now, avoid movements that reproduce pain and "
            "consider only gentle, comfortable activity instead of a full "
            "training session. " + safety
            + " What area is affected so I can suggest a specific modification?"
        )

    if not _WORKOUT.search(message):
        return (
            f"For {name} pain or discomfort, avoid movements that increase symptoms "
            "rather than exercising through pain. " + safety
            + " If you'd like a modified workout, tell me whether you train "
            "at home or at a gym."
        )

    if area == "lower-body":
        options = (
            "- Start with 2 minutes of gentle seated arm movements, if sitting is comfortable.\n"
            "- Try one light set of 6-10 seated biceps curls only if you have "
            "light weights, can sit comfortably, and do not brace through the injured area.\n"
            "- Try 5-8 gentle seated shoulder-blade squeezes, with no leg drive.\n"
            "- Cool down or rest. Avoid jumping, running, squats, lunges, "
            "and loaded leg exercises that provoke symptoms."
        )
    elif area in {"back", "neck"}:
        options = (
            "- Try 2-3 minutes of easy walking only if walking is comfortable.\n"
            "- If supported sitting feels good, try 5-8 gentle seated arm or "
            "shoulder-blade movements without heavy resistance, twisting, "
            "or forceful trunk/neck bracing.\n"
            "- Pause to reassess symptoms; rest rather than completing a target duration.\n"
            "- Skip heavy lifting, loaded bends, impact, and any position that "
            "increases back or neck pain."
        )
    elif area == "upper-body":
        options = (
            "- Try 3-5 minutes of easy walking if your legs, balance, and back "
            "are comfortable.\n"
            "- If tolerated, continue with a few more minutes of easy walking "
            "or stationary cycling without weight-bearing through the painful arm.\n"
            "- Skip gripping, pushing, pulling, overhead lifting, and any "
            "upper-body resistance that increases symptoms."
        )
    else:
        options = (
            "- Try a 2-3-minute gentle walk only if it does not stress the "
            "painful trunk area.\n"
            "- Pause, reassess, and repeat a short walk only if comfortable.\n"
            "- Avoid heavy lifting, forceful abdominal bracing, bending, "
            "twisting, and training that increases symptoms."
        )

    return (
        f"With {name} pain or discomfort, here's a conservative modified workout "
        "option, only if each movement is comfortable:\n"
        + options + "\n\n" + safety
        + "\n\nDo you have any movement restrictions or equipment? "
        "I can tailor the options without assuming that an exercise is safe."
    )

import re

from app.services.personalization import PersonalizationEngine
from app.services.smart_mode import SmartModeEngine
from app.services.weekly_plan import WeeklyPlanGenerator
from app.services.form_scoring import FormScoringEngine
from app.services.velocity import VelocityEngine


class AIEngine:
    """
    Central orchestrator for all AI + Personalization systems.
    Every AI feature routes through this engine.
    """

    def __init__(self):
        self.personalization = PersonalizationEngine()
        self.smart_mode = SmartModeEngine()
        self.weekly_plan = WeeklyPlanGenerator()
        self.form_scoring = FormScoringEngine()
        self.velocity = VelocityEngine()

    # ---------------------------------------------------------
    # AI Coach Chat (High-level reasoning)
    # ---------------------------------------------------------
    def coach(self, user_data: dict, message: str):
        """Return bounded, rule-based guidance; this is not a medical assessment."""
        profile = self.personalization.build_user_profile(user_data)
        difficulty = self.smart_mode.adjust(profile)["recommended_difficulty"]
        injuries = user_data.get("injuries") or []
        injury_text = " ".join(str(item) for item in injuries) if isinstance(injuries, list) else str(injuries)
        text = f"{message} {injury_text}".lower()

        urgent = re.search(
            r"\b(chest pain|shortness of breath|difficulty breathing|can't bear weight|cannot bear weight|"
            r"unable to bear weight|deform\w*|severe pain)\b",
            text,
        )
        if urgent:
            return {"coach_response": (
                "Do not exercise based on this advice. Your reported symptoms may need urgent assessment. "
                "Seek urgent medical care; for chest pain or difficulty breathing, call emergency services. "
                "I can't diagnose symptoms or determine whether exercise is safe."
            )}

        if re.search(r"\b(pain|painful|hurt|hurts|hurting|injur\w*|sore|soreness|ache|aching|swollen|swelling|sprain\w*|tear|torn|surgery)\b", text):
            safety = (
                "I can't diagnose pain or determine whether exercise is safe. Stop any movement that causes "
                "or worsens pain, and consult a qualified healthcare professional for advice tailored to you. "
                "Seek urgent care for severe pain, a deformed joint, inability to bear weight, a hot or very "
                "swollen joint, or fever with joint pain.\n\n"
            )
            if re.search(r"\bknees?\b", text):
                advice = (
                    "For knee pain, avoid movements that aggravate the knee. If you can sit and exercise without "
                    "knee pain and have no restrictions from your clinician, you could try a gentle seated "
                    "upper-body session: seated light rows and seated light presses, 1-2 sets of 8-12 "
                    "comfortable repetitions each, with rests between sets. Stop if positioning or any exercise "
                    "causes pain; skip the session if you cannot do it comfortably. This is not clearance to train.\n\n"
                    "How long has the pain been present, and which movements make it worse?"
                )
            else:
                advice = (
                    "I can't safely suggest an injury-specific workout without knowing the affected area and "
                    "your limitations. What area hurts, how long has it hurt, and which movements aggravate it?"
                )
            return {"coach_response": safety + advice}

        muscle_goal = bool(re.search(
            r"\b(muscle(?:s)?|muscular|hypertrophy|bulking|bulk|build(?:ing)? (?:more )?(?:muscle|size)|"
            r"gain(?:ing)? (?:more )?(?:muscle|size)|put on size)\b",
            text,
        ))
        explicit_bodyweight = bool(re.search(r"\b(bodyweight|body weight|no equipment|at home)\b", text))
        explicit_beginner = bool(re.search(r"\b(beginner|beginner's|new to exercise)\b", text))
        prefix = f"Estimated training difficulty: {difficulty}. This is not an assessment of injury or medical readiness.\\n\\n"
        if re.search(r"\b(sleep|recovery|recover|rest|fatigue|tired)\b", text):
            advice = (
                "For recovery, consider an easier session or a rest day when you feel unusually fatigued. "
                "Prioritize consistent sleep and hydration, and avoid increasing training load until you feel ready. "
                "What does your recent training and sleep look like?"
            )
        elif re.search(r"\b(nutrition|protein|food|eat|eating|calories|diet)\b", text):
            if muscle_goal:
                advice = (
                    "To support muscle growth, pair progressive resistance training with enough food and "
                    "consistent protein-containing meals. Include carbohydrate sources for training energy, "
                    "fruits or vegetables, and regular hydration. Individual protein/calorie needs vary; "
                    "what is your experience level, body-weight goal, and how often are you training?"
                )
            else:
                advice = (
                    "For general nutrition, build meals around a protein source, fruits or vegetables, and foods "
                    "that provide energy for training. Drink enough fluids. What is your training goal and what "
                    "would you like help with: meals, protein, or fueling workouts?"
                )
        elif muscle_goal:
            if explicit_bodyweight:
                advice = (
                    "To build muscle with bodyweight training, use challenging but controlled progressions "
                    "and gradually increase repetitions, sets, or exercise difficulty. A full-body session "
                    "could include 2-3 sets each of squats or split squats, incline-to-floor push-ups, "
                    "rows using a safe and stable setup, and glute bridges or hip hinges, generally 6-15 reps "
                    "per set at a manageable effort. Train 2-3 nonconsecutive days per week, allow recovery, "
                    "and stop for pain or dizziness. If you are new, start with easier variations. "
                    "What equipment or sturdy anchor points do you have, what is your experience, "
                    "and how many days can you train?"
                )
            else:
                advice = (
                    "For building muscle (hypertrophy), prioritize progressive resistance training rather "
                    "than only a short easy circuit. A practical full-body starting framework is 2-3 "
                    "sessions per week with a squat or lunge, hip hinge, push, pull, and optional arm/core "
                    "exercises. Start with about 2-3 sets of 6-12 controlled repetitions for each "
                    "major movement, resting roughly 1-3 minutes between challenging sets. Choose loads "
                    "you can control; increase repetitions or resistance gradually as movements become "
                    "manageable. Leave recovery time between hard sessions, sleep consistently, and "
                    "eat adequately to support the goal. What is your actual training experience, "
                    "do you have gym equipment or train at home, and how many days each week are available?"
                )
            if explicit_beginner and not explicit_bodyweight:
                advice += " If you are a beginner, begin with lighter loads and learn exercise technique first."
        elif re.search(r"\b(workout|workouts|work out|exercise|exercises|train|training|strength|cardio|plan)\b", text):
            experience = str(user_data.get("experience", "")).lower()
            beginner_request = bool(re.search(r"\b(beginner|beginner's|new to exercise)\b", text))
            bodyweight_request = bool(re.search(r"\b(bodyweight|body weight|no equipment|at home)\b", text))
            beginner_bodyweight = (
                beginner_request
                or experience in {"beginner", "novice"}
                or (bodyweight_request and experience not in {"intermediate", "advanced"})
            )
            if beginner_bodyweight:
                time_match = re.search(r"\b(\d{1,2})\s*-?\s*minutes?\b", text)
                requested_minutes = next(
                    (
                        user_data.get(key)
                        for key in ("available_minutes", "time_minutes", "duration_minutes", "session_minutes")
                        if user_data.get(key) is not None
                    ),
                    None,
                )
                if time_match:
                    requested_minutes = int(time_match.group(1))
                duration_is_explicit = requested_minutes is not None
                try:
                    duration = int(requested_minutes) if requested_minutes is not None else 20
                except (TypeError, ValueError):
                    duration = 20
                duration = max(5, min(duration, 60))
                if duration == 20 and duration_is_explicit:
                    advice = (
                        "Beginner bodyweight session (20 minutes total):\n"
                        "Warm-up (3 minutes): easy marching and comfortable arm circles.\n"
                        "Main circuit (14 minutes): complete 3 rounds. Each movement has a 45-second station; "
                        "do the listed reps at a controlled pace and rest for the remainder. Take 15 seconds "
                        "after every station, including the last station of each round, and 60 seconds after "
                        "rounds 1 and 2.\n"
                        "- Chair squats: 8-10 reps.\n"
                        "- Incline push-ups against a sturdy counter or wall: 6-10 reps.\n"
                        "- Glute bridges: 10-12 reps.\n"
                        "- Bird-dogs: 5 reps per side.\n"
                        "Cool-down (3 minutes): easy walking and gentle, comfortable movement. "
                        "Timing adds up to 3 + 14 + 3 = 20 minutes. Keep the effort comfortable and stop "
                        "for pain or dizziness."
                    )
                elif duration <= 12:
                    advice = (
                        f"Beginner bodyweight session (about {duration} minutes):\n"
                        "Warm-up (2 minutes): march in place, then do comfortable arm circles.\n"
                        "Complete 2 rounds. Rest 15-30 seconds between movements and 30-45 seconds between rounds:\n"
                        "- Chair squats: 8 controlled reps.\n"
                        "- Incline push-ups against a sturdy counter or wall: 6-8 reps.\n"
                        "- Glute bridges: 10 reps.\n"
                        "- Bird-dogs: 5 reps per side.\n"
                        "Use the remaining time for easy walking and a gentle cool-down. Keep the effort comfortable "
                        "and stop for pain or dizziness."
                    )
                else:
                    rounds = max(2, min(4, duration // 7))
                    advice = (
                        f"Beginner bodyweight session (about {duration} minutes):\n"
                        "Warm-up: 3-5 minutes of easy marching and comfortable arm circles.\n"
                        f"Complete {rounds} rounds, resting 60-90 seconds between rounds:\n"
                        "- Chair squats: 8-10 controlled reps.\n"
                        "- Incline push-ups against a sturdy counter or wall: 6-10 reps.\n"
                        "- Glute bridges: 10-12 reps.\n"
                        "- Bird-dogs: 6 reps per side.\n"
                        "Cool down with a few minutes of easy walking. Keep the effort comfortable, stop for pain "
                        "or dizziness, and add repetitions gradually only when the session feels manageable."
                    )
            else:
                advice = (
                    "For a general workout, warm up for 3-5 minutes, then complete 2-3 sets of a squat or leg "
                    "movement, a push, and a pull that suit your equipment; aim for 8-12 comfortable reps per "
                    "set and rest 60-90 seconds. Finish with a few minutes of easy movement. Start at a "
                    "manageable effort and progress gradually. What is your goal, experience level, available "
                    "equipment, and time for the session?"
                )
        else:
            advice = (
                "I can offer limited rule-based guidance about workouts, recovery, nutrition, and reported pain; "
                "I cannot answer every free-form question. Please describe your goal and what you need help with."
            )
        return {"coach_response": prefix + advice}

    # ---------------------------------------------------------
    # Personalization
    # ---------------------------------------------------------
    def personalize(self, user_data: dict):
        return self.personalization.generate_recommendations(user_data)

    # ---------------------------------------------------------
    # Smart Mode (Auto-regulation)
    # ---------------------------------------------------------
    def smart_mode_adjust(self, user_data: dict):
        profile = self.personalization.build_user_profile(user_data)
        return self.smart_mode.adjust(profile)

    # ---------------------------------------------------------
    # Weekly Plan Generation
    # ---------------------------------------------------------
    def generate_weekly_plan(self, user_data: dict):
        profile = self.personalization.build_user_profile(user_data)
        return self.weekly_plan.generate_plan(profile)

    # ---------------------------------------------------------
    # Biomechanics + Form Scoring
    # ---------------------------------------------------------
    def score_form(self, motion_data: dict):
        return self.form_scoring.score(motion_data)

    # ---------------------------------------------------------
    # Velocity Estimation
    # ---------------------------------------------------------
    def estimate_velocity(self, rep_data: dict):
        return self.velocity.estimate(rep_data)

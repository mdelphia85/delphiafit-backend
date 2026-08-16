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
        """
        Main AI coaching endpoint.
        Combines personalization, smart mode, biomechanics,
        recovery, nutrition, and performance trends.
        """

        profile = self.personalization.build_user_profile(user_data)
        difficulty = self.smart_mode.adjust_difficulty(profile)
        recovery = self.personalization.recovery_status(profile)
        nutrition = self.personalization.nutrition_status(profile)

        response = (
            f"Based on your current profile:\n"
            f"- Difficulty level: {difficulty}\n"
            f"- Recovery status: {recovery}\n"
            f"- Nutrition alignment: {nutrition}\n\n"
            f"Your message: {message}\n"
            f"My coaching advice: Stay consistent, adjust intensity based on recovery, "
            f"and maintain nutritional balance to support your training."
        )

        return {"coach_response": response}

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
        return self.smart_mode.adjust_difficulty(profile)

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

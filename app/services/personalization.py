from typing import Dict, Any, List


class PersonalizationEngine:
    """
    Full AI personalization engine.

    Responsibilities:
    - Build structured user profile from raw data
    - Model recovery, fatigue, and readiness
    - Evaluate nutrition alignment
    - Analyze recent training volume and intensity
    - Infer adaptive difficulty
    - Suggest training focus based on goals, injuries, and preferences
    - Provide a unified recommendation object for AIEngine, SmartMode, WeeklyPlan
    """

    # ---------------------------------------------------------
    # User Profile Construction
    # ---------------------------------------------------------
    def build_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw user data into a structured profile.
        This profile is used by all other AI systems.
        """

        profile = {
            "experience": user_data.get("experience", "beginner"),          # beginner / intermediate / advanced
            "fatigue": user_data.get("fatigue", 0),                         # 0–10 scale
            "sleep_hours": user_data.get("sleep_hours", 7.0),              # last night or average
            "nutrition_score": user_data.get("nutrition_score", 70),       # 0–100
            "recent_volume": user_data.get("recent_volume", 0),            # total sets/reps last 7 days
            "recent_intensity": user_data.get("recent_intensity", 0),      # RPE or %1RM average
            "rest_days_last_week": user_data.get("rest_days_last_week", 2),
            "goals": user_data.get("goals", []),                           # e.g., ["strength", "muscle_gain"]
            "injuries": user_data.get("injuries", []),                     # e.g., ["shoulder", "knee"]
            "preferences": user_data.get("preferences", {}),               # e.g., {"likes_cardio": True}
            "sessions_per_week": user_data.get("sessions_per_week", 3),
        }

        # Derived fields
        profile["recovery_status"] = self.recovery_status(profile)
        profile["nutrition_status"] = self.nutrition_status(profile)
        profile["difficulty"] = self._adaptive_difficulty(profile)
        profile["focus"] = self._suggest_focus(profile)

        return profile

    # ---------------------------------------------------------
    # Recovery Status
    # ---------------------------------------------------------
    def recovery_status(self, profile: Dict[str, Any]) -> str:
        fatigue = profile["fatigue"]
        sleep = profile["sleep_hours"]
        rest_days = profile["rest_days_last_week"]

        if fatigue >= 8 or sleep < 5:
            return "overreached — prioritize deload and recovery"
        if fatigue >= 6 or sleep < 6:
            return "fatigued — reduce intensity and volume"
        if rest_days < 1:
            return "under‑recovered — add at least one rest day"
        return "recovered — normal training load is appropriate"

    # ---------------------------------------------------------
    # Nutrition Status
    # ---------------------------------------------------------
    def nutrition_status(self, profile: Dict[str, Any]) -> str:
        score = profile["nutrition_score"]

        if score < 40:
            return "poor nutrition — fix basics: protein, hydration, regular meals"
        if score < 60:
            return "suboptimal nutrition — tighten consistency and macro balance"
        if score < 80:
            return "solid nutrition — maintain and refine"
        return "excellent nutrition — supports performance and recovery"

    # ---------------------------------------------------------
    # Adaptive Difficulty
    # ---------------------------------------------------------
    def _adaptive_difficulty(self, profile: Dict[str, Any]) -> str:
        exp = profile["experience"]
        fatigue = profile["fatigue"]
        recent_intensity = profile["recent_intensity"]
        recent_volume = profile["recent_volume"]

        # Base difficulty by experience
        if exp == "beginner":
            base = "easy"
        elif exp == "intermediate":
            base = "moderate"
        else:
            base = "hard"

        # Fatigue overrides
        if fatigue >= 7:
            return "easy"
        if fatigue >= 5 and base == "hard":
            return "moderate"

        # Recent load adjustments
        if recent_intensity > 8 or recent_volume > 120:
            if base == "hard":
                return "moderate"

        return base

    # ---------------------------------------------------------
    # Public: Generate Recommendations
    # ---------------------------------------------------------
    def generate_recommendations(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for AIEngine and routers.
        Returns a structured recommendation object.
        """

        profile = self.build_user_profile(user_data)

        recommendations = {
            "profile": profile,
            "difficulty": profile["difficulty"],
            "recovery": profile["recovery_status"],
            "nutrition": profile["nutrition_status"],
            "suggested_focus": profile["focus"],
            "weekly_load_hint": self._weekly_load_hint(profile),
            "session_style_hint": self._session_style_hint(profile),
        }

        return recommendations

    # ---------------------------------------------------------
    # Internal: Suggest Training Focus
    # ---------------------------------------------------------
    def _suggest_focus(self, profile: Dict[str, Any]) -> str:
        goals: List[str] = profile["goals"]
        injuries: List[str] = profile["injuries"]
        prefs: Dict[str, Any] = profile["preferences"]

        if injuries:
            return "rehab‑friendly training emphasizing safe ranges and controlled tempo"

        if "strength" in goals:
            return "low‑rep strength blocks with progressive overload"
        if "muscle_gain" in goals:
            return "hypertrophy focus: moderate reps, controlled tempo, higher volume"
        if "fat_loss" in goals:
            return "conditioning + calorie control with mixed modal training"
        if "endurance" in goals:
            return "aerobic base building with progressive duration"

        if prefs.get("likes_cardio"):
            return "mixed conditioning with intervals and steady‑state work"
        if prefs.get("prefers_short_sessions"):
            return "high‑density sessions with supersets and EMOM structures"

        return "balanced training across strength, hypertrophy, and conditioning"

    # ---------------------------------------------------------
    # Internal: Weekly Load Hint
    # ---------------------------------------------------------
    def _weekly_load_hint(self, profile: Dict[str, Any]) -> str:
        sessions = profile["sessions_per_week"]
        difficulty = profile["difficulty"]

        if sessions <= 2:
            return "focus on full‑body sessions with compound lifts"
        if sessions == 3:
            if difficulty == "easy":
                return "3 moderate full‑body sessions with emphasis on technique"
            if difficulty == "moderate":
                return "upper/lower/full split with controlled volume"
            return "push/pull/legs split with progressive overload"
        if sessions >= 4:
            if difficulty == "easy":
                return "4 lighter sessions emphasizing movement quality and recovery"
            return "4–5 sessions with structured split and periodized intensity"

        return "default to 3 full‑body sessions per week"

    # ---------------------------------------------------------
    # Internal: Session Style Hint
    # ---------------------------------------------------------
    def _session_style_hint(self, profile: Dict[str, Any]) -> str:
        difficulty = profile["difficulty"]
        recovery = profile["recovery_status"]

        if "overreached" in recovery or "under‑recovered" in recovery:
            return "low‑impact, technique‑focused sessions with extended rest and reduced volume"

        if difficulty == "easy":
            return "technique‑focused, low‑stress sessions with longer rest and simpler movements"
        if difficulty == "moderate":
            return "mixed intensity sessions with compound lifts and moderate accessory work"
        return "high‑intensity sessions with heavy compounds and focused accessory work"

from typing import Dict, Any, List


class WeeklyPlanGenerator:
    """
    Generates a full weekly training plan based on:
    - user profile (experience, goals, injuries, sessions/week)
    - recovery and nutrition status
    - adaptive difficulty from personalization/smart mode
    """

    # ---------------------------------------------------------
    # Public: Generate Weekly Plan
    # ---------------------------------------------------------
    def generate_plan(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        sessions_per_week = profile.get("sessions_per_week", 3)
        difficulty = profile.get("difficulty", "moderate")
        focus = profile.get("focus", "balanced training")
        recovery = profile.get("recovery_status", "recovered")
        goals = profile.get("goals", [])
        injuries = profile.get("injuries", [])

        # A list of reported injuries does not provide enough information to
        # identify safe movements, loading, or a return-to-training clearance.
        # Keep the plan structure but do not prescribe unverified exercises.
        needs_review = bool(injuries)
        split = self._choose_split(sessions_per_week, difficulty, goals)
        days = self._build_days(split, difficulty, focus, recovery, injuries)

        return {
            "sessions_per_week": sessions_per_week,
            "split": split,
            "focus": (
                "Training schedule pending review of reported restrictions"
                if needs_review else focus
            ),
            "recovery_status": self._describe_recovery(recovery),
            "requires_injury_review": needs_review,
            "safety_note": (
                "Restrictions were reported. No exercises or conditioning are "
                "automatically prescribed because this planner cannot determine "
                "which movements are safe. Consult a qualified professional for "
                "individualized advice before using this schedule."
                if needs_review else
                "This plan is general exercise guidance, not medical clearance."
            ),
            "plan": days,
        }

    @staticmethod
    def _describe_recovery(status: str) -> str:
        """Reported sleep/fatigue indicator, not diagnosis or injury clearance."""
        if "overreached" in status:
            return "High fatigue or short sleep reported; consider additional rest."
        if "fatigued" in status:
            return "Reported sleep or fatigue suggests a lighter workload."
        if "under" in status and "recover" in status:
            return "Few rest days reported; consider additional recovery time."
        return "Reported sleep and fatigue suggest typical recovery; not medical clearance."

    # ---------------------------------------------------------
    # Choose Training Split
    # ---------------------------------------------------------
    def _choose_split(self, sessions: int, difficulty: str, goals: List[str]) -> str:
        if sessions <= 2:
            return "full_body"
        if sessions == 3:
            if "strength" in goals:
                return "upper_lower_full"
            return "full_body"
        if sessions == 4:
            return "upper_lower_repeat"
        if sessions >= 5:
            if "muscle_gain" in goals or "bodybuilding" in goals:
                return "push_pull_legs_upper_lower"
            return "push_pull_legs"

        return "full_body"

    # ---------------------------------------------------------
    # Build Day-by-Day Plan
    # ---------------------------------------------------------
    def _build_days(
        self,
        split: str,
        difficulty: str,
        focus: str,
        recovery: str,
        injuries: List[str],
    ) -> List[Dict[str, Any]]:
        days: List[Dict[str, Any]] = []

        templates = self._split_templates(split)

        for i, template in enumerate(templates, start=1):
            day = {
                "day": i,
                "type": template["type"],
                "primary_focus": (
                    "Exercise selection requires individual review"
                    if injuries else self._day_focus(template["type"], focus)
                ),
                "intensity": None if injuries else self._day_intensity(difficulty, recovery, i),
                "volume": None if injuries else self._day_volume(difficulty, i),
                "exercises": self._exercise_block(template["type"], injuries),
                "conditioning": None if injuries else self._conditioning_block(focus, i),
                "notes": (
                    "No exercises assigned until reported restrictions have been reviewed."
                    if injuries else self._day_notes(recovery, i)
                ),
            }
            days.append(day)

        return days

    # ---------------------------------------------------------
    # Split Templates
    # ---------------------------------------------------------
    def _split_templates(self, split: str) -> List[Dict[str, str]]:
        if split == "full_body":
            return [
                {"type": "full_body"},
                {"type": "full_body"},
                {"type": "full_body"},
            ]
        if split == "upper_lower_full":
            return [
                {"type": "upper"},
                {"type": "lower"},
                {"type": "full_body"},
            ]
        if split == "upper_lower_repeat":
            return [
                {"type": "upper"},
                {"type": "lower"},
                {"type": "upper"},
                {"type": "lower"},
            ]
        if split == "push_pull_legs":
            return [
                {"type": "push"},
                {"type": "pull"},
                {"type": "legs"},
                {"type": "full_body"},
                {"type": "conditioning"},
            ]
        if split == "push_pull_legs_upper_lower":
            return [
                {"type": "push"},
                {"type": "pull"},
                {"type": "legs"},
                {"type": "upper"},
                {"type": "lower"},
            ]

        return [{"type": "full_body"}]

    # ---------------------------------------------------------
    # Day Focus
    # ---------------------------------------------------------
    def _day_focus(self, day_type: str, global_focus: str) -> str:
        if day_type == "upper":
            return "upper body strength / hypertrophy"
        if day_type == "lower":
            return "lower body strength / hypertrophy"
        if day_type == "push":
            return "pressing strength and chest/shoulders"
        if day_type == "pull":
            return "pulling strength and back/biceps"
        if day_type == "legs":
            return "squats, hinges, and lower body power"
        if day_type == "conditioning":
            return "conditioning and aerobic base"
        return global_focus

    # ---------------------------------------------------------
    # Day Intensity
    # ---------------------------------------------------------
    def _day_intensity(self, difficulty: str, recovery: str, day_index: int) -> str:
        if "overreached" in recovery:
            return "low"
        if "fatigued" in recovery and day_index <= 2:
            return "low_to_moderate"

        if difficulty == "easy":
            return "low_to_moderate"
        if difficulty == "moderate":
            if day_index in (1, 3):
                return "moderate_to_high"
            return "moderate"
        return "high_with_variation"

    # ---------------------------------------------------------
    # Day Volume
    # ---------------------------------------------------------
    def _day_volume(self, difficulty: str, day_index: int) -> str:
        if difficulty == "easy":
            return "low"
        if difficulty == "moderate":
            if day_index in (2, 4):
                return "moderate"
            return "moderate_high"
        return "high"

    # ---------------------------------------------------------
    # Exercise Block
    # ---------------------------------------------------------
    def _exercise_block(self, day_type: str, injuries: List[str]) -> List[Dict[str, Any]]:
        # Do not label exercises "injury-friendly" without assessing the injury.
        # General templates are offered only when no restrictions are reported.
        if injuries:
            return []

        if day_type == "upper":
            return [
                {"name": "Bench Press", "sets": 3, "reps": "5–8"},
                {"name": "Seated Cable Row", "sets": 3, "reps": "8–10"},
                {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "6–8"},
            ]
        if day_type == "lower":
            return [
                {"name": "Goblet Squat", "sets": 3, "reps": "5–8"},
                {"name": "Romanian Deadlift", "sets": 3, "reps": "6–8"},
                {"name": "Reverse Lunge", "sets": 3, "reps": "8–10"},
            ]
        if day_type == "push":
            return [
                {"name": "Dumbbell Bench Press", "sets": 3, "reps": "6–10"},
                {"name": "Dumbbell Overhead Press", "sets": 3, "reps": "6–8"},
                {"name": "Dumbbell Chest Fly", "sets": 3, "reps": "10–12"},
            ]
        if day_type == "pull":
            return [
                {"name": "Romanian Deadlift", "sets": 3, "reps": "5–8"},
                {"name": "Seated Cable Row", "sets": 3, "reps": "8–10"},
                {"name": "Lat Pulldown", "sets": 3, "reps": "6–10"},
            ]
        if day_type == "legs":
            return [
                {"name": "Goblet Squat", "sets": 3, "reps": "5–8"},
                {"name": "Reverse Lunge", "sets": 3, "reps": "8–10"},
                {"name": "Leg Curl", "sets": 3, "reps": "10–12"},
            ]

        # full_body or default
        return [
            {"name": "Goblet Squat", "sets": 3, "reps": "5–8"},
            {"name": "Dumbbell Bench Press", "sets": 3, "reps": "6–10"},
            {"name": "Seated Cable Row", "sets": 3, "reps": "8–10"},
        ]

    # ---------------------------------------------------------
    # Conditioning Block
    # ---------------------------------------------------------
    def _conditioning_block(self, focus: str, day_index: int) -> Dict[str, Any]:
        if "fat_loss" in focus or "conditioning" in focus or "endurance" in focus:
            if day_index in (2, 4):
                return {"type": "intervals", "duration_minutes": 15}
            return {"type": "steady_state", "duration_minutes": 20}
        return {"type": "optional", "duration_minutes": 10}

    # ---------------------------------------------------------
    # Day Notes
    # ---------------------------------------------------------
    def _day_notes(self, recovery: str, day_index: int) -> str:
        if "overreached" in recovery:
            return "Keep RPE low, prioritize technique, and consider extra rest."
        if "fatigued" in recovery and day_index == 1:
            return "Start the week lighter; build up if you feel better."
        if day_index == 3:
            return "Mid‑week check: adjust load based on how you feel."
        return "Stay consistent, track performance, and adjust if needed."

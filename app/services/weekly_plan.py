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

        split = self._choose_split(sessions_per_week, difficulty, goals)
        days = self._build_days(split, difficulty, focus, recovery, injuries)

        return {
            "sessions_per_week": sessions_per_week,
            "split": split,
            "focus": focus,
            "recovery_status": recovery,
            "plan": days,
        }

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
                "primary_focus": self._day_focus(template["type"], focus),
                "intensity": self._day_intensity(difficulty, recovery, i),
                "volume": self._day_volume(difficulty, i),
                "exercises": self._exercise_block(template["type"], injuries),
                "conditioning": self._conditioning_block(focus, i),
                "notes": self._day_notes(recovery, i),
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
        safe_suffix = " (injury‑friendly)" if injuries else ""

        if day_type == "upper":
            return [
                {"name": f"Bench Press{safe_suffix}", "sets": 3, "reps": "5–8"},
                {"name": f"Row Variation{safe_suffix}", "sets": 3, "reps": "8–10"},
                {"name": f"Shoulder Press{safe_suffix}", "sets": 3, "reps": "6–8"},
            ]
        if day_type == "lower":
            return [
                {"name": f"Squat Variation{safe_suffix}", "sets": 3, "reps": "5–8"},
                {"name": f"Hinge Variation{safe_suffix}", "sets": 3, "reps": "6–8"},
                {"name": f"Single‑Leg Work{safe_suffix}", "sets": 3, "reps": "8–10"},
            ]
        if day_type == "push":
            return [
                {"name": f"Bench or Dumbbell Press{safe_suffix}", "sets": 3, "reps": "6–10"},
                {"name": f"Overhead Press{safe_suffix}", "sets": 3, "reps": "6–8"},
                {"name": f"Chest Isolation{safe_suffix}", "sets": 3, "reps": "10–12"},
            ]
        if day_type == "pull":
            return [
                {"name": f"Deadlift or RDL{safe_suffix}", "sets": 3, "reps": "5–8"},
                {"name": f"Row Variation{safe_suffix}", "sets": 3, "reps": "8–10"},
                {"name": f"Pull‑up / Lat Work{safe_suffix}", "sets": 3, "reps": "6–10"},
            ]
        if day_type == "legs":
            return [
                {"name": f"Squat Variation{safe_suffix}", "sets": 3, "reps": "5–8"},
                {"name": f"Lunge / Split Squat{safe_suffix}", "sets": 3, "reps": "8–10"},
                {"name": f"Hamstring Isolation{safe_suffix}", "sets": 3, "reps": "10–12"},
            ]

        # full_body or default
        return [
            {"name": f"Squat Variation{safe_suffix}", "sets": 3, "reps": "5–8"},
            {"name": f"Press Variation{safe_suffix}", "sets": 3, "reps": "6–10"},
            {"name": f"Row Variation{safe_suffix}", "sets": 3, "reps": "8–10"},
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

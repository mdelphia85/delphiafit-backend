from typing import Dict, Any


class SmartModeEngine:
    """
    Real-time auto-regulation engine.
    Adjusts workout difficulty, volume, intensity, and exercise selection
    based on fatigue, recovery, velocity trends, form quality, and user profile.
    """

    # ---------------------------------------------------------
    # Main Smart Mode Adjustment
    # ---------------------------------------------------------
    def adjust(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a full smart-mode adjustment package:
        - recommended difficulty
        - volume adjustment
        - intensity adjustment
        - rest interval
        - exercise style
        - readiness score
        """

        difficulty = self._difficulty(profile)
        readiness = self._readiness(profile)
        volume = self._volume_adjustment(difficulty, readiness)
        intensity = self._intensity_adjustment(difficulty, readiness)
        rest = self._rest_interval(difficulty, readiness)
        style = self._exercise_style(difficulty, profile["recovery_status"])

        return {
            "recommended_difficulty": difficulty,
            "readiness_score": readiness,
            "volume_adjustment": volume,
            "intensity_adjustment": intensity,
            "rest_interval": rest,
            "exercise_style": style,
        }

    # ---------------------------------------------------------
    # Difficulty Logic
    # ---------------------------------------------------------
    def _difficulty(self, profile: Dict[str, Any]) -> str:
        base = profile["difficulty"]
        fatigue = profile["fatigue"]
        recovery = profile["recovery_status"]
        recent_volume = profile["recent_volume"]
        recent_intensity = profile["recent_intensity"]

        # Fatigue overrides
        if fatigue >= 8:
            return "easy"
        if fatigue >= 6 and base == "hard":
            return "moderate"

        # Recovery overrides
        if "overreached" in recovery:
            return "easy"
        if "fatigued" in recovery and base == "hard":
            return "moderate"

        # Recent load adjustments
        if recent_volume > 120 or recent_intensity > 8:
            if base == "hard":
                return "moderate"

        return base

    # ---------------------------------------------------------
    # Readiness Score (0–100)
    # ---------------------------------------------------------
    def _readiness(self, profile: Dict[str, Any]) -> int:
        fatigue = profile["fatigue"]
        sleep = profile["sleep_hours"]
        nutrition = profile["nutrition_score"]
        rest_days = profile["rest_days_last_week"]

        score = 100

        # Fatigue penalty
        score -= fatigue * 5

        # Sleep penalty
        if sleep < 6:
            score -= (6 - sleep) * 5

        # Nutrition penalty
        if nutrition < 60:
            score -= (60 - nutrition) // 2

        # Rest day penalty
        if rest_days < 1:
            score -= 10

        # Clamp
        return max(0, min(100, score))

    # ---------------------------------------------------------
    # Volume Adjustment
    # ---------------------------------------------------------
    def _volume_adjustment(self, difficulty: str, readiness: int) -> str:
        if readiness < 40:
            return "reduce volume by 40–50%"
        if readiness < 60:
            return "reduce volume by 20–30%"

        if difficulty == "easy":
            return "reduce volume by 30%"
        if difficulty == "moderate":
            return "maintain normal volume"
        return "increase volume by 10–15%"

    # ---------------------------------------------------------
    # Intensity Adjustment
    # ---------------------------------------------------------
    def _intensity_adjustment(self, difficulty: str, readiness: int) -> str:
        if readiness < 40:
            return "use RPE 5–6 or 50–60% 1RM"
        if readiness < 60:
            return "use RPE 6–7 or 60–70% 1RM"

        if difficulty == "easy":
            return "use RPE 6 or 60% 1RM"
        if difficulty == "moderate":
            return "use RPE 7–8 or 70–80% 1RM"
        return "use RPE 8–9 or 80–85% 1RM"

    # ---------------------------------------------------------
    # Rest Interval Logic
    # ---------------------------------------------------------
    def _rest_interval(self, difficulty: str, readiness: int) -> str:
        if readiness < 40:
            return "rest 2–3 minutes between sets"
        if readiness < 60:
            return "rest 2 minutes between sets"

        if difficulty == "easy":
            return "rest 2 minutes"
        if difficulty == "moderate":
            return "rest 90 seconds"
        return "rest 60–90 seconds"

    # ---------------------------------------------------------
    # Exercise Style Logic
    # ---------------------------------------------------------
    def _exercise_style(self, difficulty: str, recovery: str) -> str:
        if "overreached" in recovery:
            return "slow tempo, controlled movements, avoid max effort"
        if difficulty == "easy":
            return "technique-focused, low impact, controlled tempo"
        if difficulty == "moderate":
            return "mixed tempo, compound lifts + moderate accessories"
        return "explosive compounds + targeted accessory work"

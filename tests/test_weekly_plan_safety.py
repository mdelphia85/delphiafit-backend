"""Regression tests for weekly plan clarity and reported injury restrictions.

Run with: python -m unittest discover -s tests -p 'test_weekly_plan_safety.py'
"""
import unittest

from app.services.weekly_plan import WeeklyPlanGenerator


class WeeklyPlanSafetyTests(unittest.TestCase):
    def setUp(self):
        self.generator = WeeklyPlanGenerator()

    def test_generates_concrete_exercises_for_unrestricted_training(self):
        result = self.generator.generate_plan({
            "sessions_per_week": 3,
            "difficulty": "easy",
            "focus": "strength",
            "goals": ["strength"],
            "recovery_status": "recovered — normal training load is appropriate",
            "injuries": [],
        })
        self.assertEqual(result["split"], "upper_lower_full")
        self.assertFalse(result["requires_injury_review"])
        self.assertEqual(len(result["plan"]), 3)
        names = [exercise["name"] for day in result["plan"] for exercise in day["exercises"]]
        self.assertIn("Seated Cable Row", names)
        self.assertIn("Goblet Squat", names)
        self.assertNotIn("Row Variation", names)
        self.assertTrue(all("injury" not in name.lower() for name in names))
        self.assertNotIn("normal training load is appropriate", result["recovery_status"])

    def test_injuries_do_not_receive_automatic_exercises_or_false_clearance(self):
        result = self.generator.generate_plan({
            "sessions_per_week": 3,
            "difficulty": "easy",
            "focus": "rehab-friendly training emphasizing safe ranges",
            "goals": ["strength"],
            "recovery_status": "recovered — normal training load is appropriate",
            "injuries": ["shoulder"],
        })
        self.assertTrue(result["requires_injury_review"])
        self.assertIn("review", result["safety_note"].lower())
        self.assertEqual(len(result["plan"]), 3)
        self.assertFalse(any(day["exercises"] for day in result["plan"]))
        self.assertTrue(all(day["conditioning"] is None for day in result["plan"]))
        self.assertTrue(all(day["intensity"] is None for day in result["plan"]))
        self.assertTrue(all(day["volume"] is None for day in result["plan"]))
        self.assertNotIn("injury-friendly", str(result).lower())
        self.assertNotIn("rehab-friendly", str(result).lower())
        self.assertNotIn("normal training load is appropriate", str(result).lower())

    def test_reports_fatigue_as_indicator_not_medical_diagnosis(self):
        result = self.generator.generate_plan({
            "sessions_per_week": 2,
            "difficulty": "easy",
            "focus": "balanced",
            "goals": [],
            "recovery_status": "fatigued — reduce intensity and volume",
            "injuries": [],
        })
        self.assertIn("lighter workload", result["recovery_status"])
        self.assertFalse(result["requires_injury_review"])
        self.assertTrue(result["plan"])

    def test_existing_plan_structure_remains_compatible(self):
        result = self.generator.generate_plan({
            "sessions_per_week": 4,
            "difficulty": "moderate",
            "focus": "endurance",
            "goals": ["endurance"],
            "recovery_status": "recovered",
            "injuries": [],
        })
        for key in ("sessions_per_week", "split", "focus", "recovery_status", "plan"):
            self.assertIn(key, result)
        self.assertEqual(len(result["plan"]), 4)
        self.assertTrue(all("day" in day and "exercises" in day for day in result["plan"]))


if __name__ == "__main__":
    unittest.main()

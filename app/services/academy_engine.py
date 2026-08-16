class AcademyEngine:

    def academic_score(self, correct: int, total: int):
        pct = correct / max(total, 1)
        return {
            "percentage": round(pct * 100, 2),
            "passed": pct >= 0.7
        }

    def fitness_score(self, run_time: float, pushups: int, situps: int):
        score = 0
        score += max(0, 60 - run_time) * 1.5
        score += pushups * 0.5
        score += situps * 0.3
        return {"score": round(score, 2)}

    def scenario_score(self, decisions: int, errors: int):
        score = decisions - (errors * 2)
        return {
            "score": max(score, 0),
            "passed": score >= 10
        }

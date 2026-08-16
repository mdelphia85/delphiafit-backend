class ScenarioEngine:

    def evaluate_branch(self, score: float, score_delta: float):
        new_score = score + score_delta
        return {"new_score": round(new_score, 2)}

    def difficulty_modifier(self, difficulty: str):
        mapping = {
            "easy": 0.8,
            "moderate": 1.0,
            "hard": 1.2,
            "extreme": 1.5
        }
        return {"modifier": mapping.get(difficulty, 1.0)}

    def outcome(self, score: float):
        if score >= 90:
            return {"outcome": "excellent"}
        if score >= 70:
            return {"outcome": "successful"}
        if score >= 50:
            return {"outcome": "partial"}
        return {"outcome": "failed"}

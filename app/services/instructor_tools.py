class InstructorTools:

    def evaluate_performance(self, score: float, difficulty: str):
        modifier = {
            "easy": 0.9,
            "moderate": 1.0,
            "hard": 1.2,
            "extreme": 1.5
        }.get(difficulty, 1.0)

        adjusted = score * modifier

        if adjusted >= 90:
            return {"rating": "excellent", "adjusted_score": round(adjusted, 2)}
        if adjusted >= 75:
            return {"rating": "good", "adjusted_score": round(adjusted, 2)}
        if adjusted >= 60:
            return {"rating": "fair", "adjusted_score": round(adjusted, 2)}
        return {"rating": "poor", "adjusted_score": round(adjusted, 2)}

    def approve_loadout(self, total_weight: float, mobility: float):
        if total_weight > 80:
            return {"approved": False, "reason": "Loadout too heavy"}
        if mobility < 0.5:
            return {"approved": False, "reason": "Mobility too low"}
        return {"approved": True}

    def certify(self, evaluations):
        avg = sum(e.score for e in evaluations if e.score is not None) / max(len(evaluations), 1)
        return {
            "average_score": round(avg, 2),
            "certified": avg >= 75
        }

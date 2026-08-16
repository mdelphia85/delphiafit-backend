class MissionReplayEngine:

    def compute_score(self, steps):
        score = 0.0
        for step in steps:
            score += step.score_delta
        return {"score": round(score, 2)}

    def timeline(self, steps):
        return [
            {
                "timestamp": step.timestamp.isoformat(),
                "action": step.action_type,
                "description": step.description,
                "score_delta": step.score_delta
            }
            for step in steps
        ]

    def instructor_summary(self, annotations):
        return [
            {
                "timestamp": ann.timestamp.isoformat(),
                "category": ann.category,
                "note": ann.note
            }
            for ann in annotations
        ]

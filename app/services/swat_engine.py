class SWATEngine:

    def cqb_score(self, hits: int, misses: int, time: float):
        score = (hits * 2) - misses - (time * 0.5)
        return {"score": round(max(score, 0), 2)}

    def breaching_score(self, time: float, errors: int):
        score = 100 - (time * 2) - (errors * 10)
        return {"score": round(max(score, 0), 2)}

    def hostage_rescue_score(self, decisions: int, errors: int):
        score = decisions * 3 - errors * 5
        return {"score": round(max(score, 0), 2)}

    def marksmanship_score(self, accuracy: float, speed: float):
        score = (accuracy * 0.7) + (speed * 0.3)
        return {"score": round(score, 2)}

    def stress_inoculation(self, heart_rate: float, performance: float):
        stress_factor = heart_rate / 200
        score = performance - (stress_factor * 10)
        return {"score": round(max(score, 0), 2)}

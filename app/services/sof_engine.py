class SOFEngine:

    def ruck_score(self, weight: float, distance: float, time: float):
        # Lower time = better score
        base = (distance * weight) / max(time, 1)
        return {"score": round(base, 2)}

    def swim_score(self, distance: float, time: float):
        pace = distance / max(time, 1)
        return {"pace": round(pace, 2)}

    def land_nav_score(self, points_found: int, total_points: int, time: float):
        pct = points_found / max(total_points, 1)
        score = pct * 100 - (time * 0.1)
        return {"score": round(max(score, 0), 2)}

    def team_event_score(self, cohesion: float, leadership: float, stress: float):
        score = (cohesion * 0.4) + (leadership * 0.4) - (stress * 0.2)
        return {"score": round(score, 2)}

    def selection_gate(self, score: float, threshold: float):
        return {"passed": score >= threshold}

class MaritimeEngine:

    def sea_state_risk(self, sea_state: str):
        mapping = {
            "calm": "low",
            "moderate": "medium",
            "rough": "high",
            "severe": "critical"
        }
        return {"risk": mapping.get(sea_state, "unknown")}

    def swimmer_risk(self, wave_height: float):
        if wave_height < 1:
            return {"risk": "low"}
        if wave_height < 2.5:
            return {"risk": "medium"}
        if wave_height < 4:
            return {"risk": "high"}
        return {"risk": "critical"}

    def interdiction_score(self, speed: float, distance: float):
        score = (speed / max(distance, 1)) * 10
        return {"score": round(score, 2)}

    def man_overboard_probability(self, wind_speed: float, sea_state: str):
        base = {"calm": 0.01, "moderate": 0.05, "rough": 0.15, "severe": 0.3}.get(sea_state, 0.05)
        return {"probability": round(base + (wind_speed * 0.01), 3)}

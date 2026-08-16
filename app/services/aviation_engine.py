class AviationEngine:

    def hoist_risk(self, wind_speed: float, visibility: float):
        # simple placeholder scoring
        risk = 0.0
        risk += wind_speed * 0.02
        risk += (1 - visibility) * 0.5
        if risk < 0.3:
            level = "low"
        elif risk < 0.6:
            level = "medium"
        elif risk < 0.8:
            level = "high"
        else:
            level = "critical"
        return {"risk_score": round(risk, 2), "risk_level": level}

    def fuel_margin(self, planned_time_min: int, fuel_available_min: int):
        margin = fuel_available_min - planned_time_min
        return {
            "margin_minutes": margin,
            "status": "ok" if margin >= 20 else "tight" if margin >= 5 else "critical"
        }

    def crew_fatigue(self, duty_hours: float):
        if duty_hours < 8:
            return {"fatigue": "low"}
        if duty_hours < 12:
            return {"fatigue": "medium"}
        if duty_hours < 16:
            return {"fatigue": "high"}
        return {"fatigue": "critical"}

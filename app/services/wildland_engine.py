class WildlandEngine:

    def fire_spread_rate(self, wind_speed: float, fuel_load: float, humidity: float):
        rate = (wind_speed * 0.3) + (fuel_load * 0.5) - (humidity * 0.2)
        return {"spread_rate": round(max(rate, 0), 2)}

    def containment_projection(self, crews: int, dozers: int, air_support: int):
        score = (crews * 0.1) + (dozers * 0.2) + (air_support * 0.3)
        return {"projected_containment_gain": round(score, 2)}

    def risk_level(self, temp: float, wind_speed: float, humidity: float):
        risk = (temp * 0.02) + (wind_speed * 0.03) - (humidity * 0.01)
        if risk < 0.3:
            level = "low"
        elif risk < 0.6:
            level = "moderate"
        elif risk < 0.9:
            level = "high"
        else:
            level = "extreme"
        return {"risk": level, "score": round(risk, 2)}

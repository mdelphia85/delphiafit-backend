class DisasterEngine:

    def estimate_impact(self, severity: str, population: int):
        base = {"minor": 0.1, "moderate": 0.3, "major": 0.6, "catastrophic": 0.9}.get(severity, 0.3)
        return {"estimated_affected": int(base * population)}

    def sector_priority(self, sector_status: str):
        if sector_status == "inaccessible":
            return {"priority": "high"}
        if sector_status == "active":
            return {"priority": "medium"}
        return {"priority": "low"}

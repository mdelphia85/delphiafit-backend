class HazmatEngine:

    def threat_score(self, threat_level: str, contamination: float):
        base = {"low": 0.2, "moderate": 0.4, "high": 0.7, "critical": 0.9}.get(threat_level, 0.3)
        score = base + (contamination * 0.1)
        return {"score": round(score, 2)}

    def zone_risk(self, zone_type: str):
        mapping = {
            "hot": "critical",
            "warm": "high",
            "cold": "low"
        }
        return {"risk": mapping.get(zone_type, "unknown")}

    def ppe_required(self, threat_level: str):
        mapping = {
            "low": "Level D",
            "moderate": "Level C",
            "high": "Level B",
            "critical": "Level A"
        }
        return {"ppe": mapping.get(threat_level, "Level C")}

    def exposure_severity(self, contamination: float):
        if contamination < 0.2:
            return {"severity": "mild"}
        if contamination < 0.5:
            return {"severity": "moderate"}
        if contamination < 0.8:
            return {"severity": "severe"}
        return {"severity": "critical"}

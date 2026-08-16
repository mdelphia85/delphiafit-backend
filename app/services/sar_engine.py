class SAREngine:

    def generate_grid(self, area_size):
        # Placeholder logic
        return {"grid_cells": int(area_size / 50)}

    def beacon_detect(self, signal_strength):
        return {"detected": signal_strength > 0.7, "strength": signal_strength}

    def triage(self, vitals):
        hr = vitals.get("heart_rate", 0)
        resp = vitals.get("resp_rate", 0)
        conscious = vitals.get("conscious", False)

        if not conscious or hr > 140 or resp > 30:
            return {"condition": "critical"}
        return {"condition": "stable"}

    def extraction_time(self, terrain_difficulty):
        return {"minutes": terrain_difficulty * 12}

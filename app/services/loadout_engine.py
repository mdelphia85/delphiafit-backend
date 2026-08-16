class LoadoutEngine:

    def calculate_totals(self, items):
        total_weight = sum(i.weight * i.quantity for i in items)

        # Mobility decreases with weight
        mobility_score = max(0.1, 1.5 - (total_weight * 0.02))

        # Endurance decreases with weight
        endurance_score = max(0.1, 1.2 - (total_weight * 0.015))

        return {
            "total_weight": round(total_weight, 2),
            "mobility_score": round(mobility_score, 2),
            "endurance_score": round(endurance_score, 2)
        }

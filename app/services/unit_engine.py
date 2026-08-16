class UnitEngine:

    def compute_readiness(self, members, capabilities):
        # Member count contributes to readiness
        member_score = len(members) * 5

        # Capability scores contribute directly
        capability_score = sum(c.score for c in capabilities)

        readiness = member_score + capability_score

        return {"readiness_score": round(readiness, 2)}

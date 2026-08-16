class CertificationEngine:

    def evaluate_requirements(self, requirements, user_scores):
        """
        requirements: list of CertificationRequirement
        user_scores: dict {target_id: score}
        """
        total = 0
        count = 0

        for req in requirements:
            score = user_scores.get(req.target_id, 0)
            total += score
            count += 1

        avg = total / max(count, 1)
        return {"average_score": round(avg, 2)}

    def check_pass(self, average_score, required_score):
        return {"passed": average_score >= required_score}

    def expiration_date(self, months):
        return {"months_valid": months}

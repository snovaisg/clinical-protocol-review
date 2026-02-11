
class ScoringEngine:
    def score_protocol(self, amendment_risks: list[dict]) -> int:
        """
        Scores the protocol based on the identified amendment risks.
        Higher score means fewer/less severe risks.

        Uses a weighted-average approach so the score reflects the mean
        severity of risks rather than blowing out to 0 when many risks
        are reported (which is normal for a thorough review).

        A small volume penalty (capped at 15 points) is applied so that
        protocols with more total risks score slightly lower than those
        with fewer risks at the same average severity.
        """
        if not amendment_risks:
            return 100

        severity_scores = {
            "Low": 90,
            "Medium": 70,
            "High": 40,
        }

        risk_values = [
            severity_scores.get(risk.get("severity", "Low"), 90)
            for risk in amendment_risks
        ]
        avg_score = sum(risk_values) / len(risk_values)

        # Small penalty for sheer volume of risks, capped at 15
        volume_penalty = min(len(amendment_risks) * 1.5, 15)

        return max(0, round(avg_score - volume_penalty))
"""Debate scoring configuration"""

from pydantic import BaseModel
from typing import Dict


class DebateConfig(BaseModel):
    """Debate configuration"""

    max_rounds: int = 5
    convergence_threshold: float = 0.8
    score_margin_threshold: float = 0.3

    weights: Dict[str, float] = {
        "votes": 0.35,
        "critiques": 0.35,
        "confidence": 0.15,
        "evidence": 0.15,
    }

    critique_prompt: str = """
    Critically evaluate this proposal:
    {proposal}

    Provide structured analysis:
    1. STRENGTHS: What works well (2-3 points)
    2. WEAKNESSES: Specific flaws or gaps (2-3 points)
    3. EVIDENCE_GAPS: Missing supporting evidence
    4. SCORE: 1-10 with justification

    IMPORTANT: Critically audit reasoning rather than defaulting to agreement.
    """

    voting_criteria: str = """
    Select the best proposal based on:
    - Evidence quality and factual support
    - Logical coherence and argument structure
    - Practical feasibility
    - Completeness of solution

    You cannot vote for your own proposal.
    """


class DebateScorer:
    """Calculate debate scores"""

    @staticmethod
    def count_votes(votes: Dict[str, str]) -> Dict[str, int]:
        """Count votes per proposal"""
        counts = {}
        for proposal_id in votes.values():
            counts[proposal_id] = counts.get(proposal_id, 0) + 1
        return counts

    @staticmethod
    def calculate_weighted_score(
        proposal: Dict, weights: Dict[str, float], total_agents: int
    ) -> float:
        """Calculate weighted score for a proposal"""
        vote_count = proposal.get("votes", 0)
        critique_avg = proposal.get("critique_avg", 5.0)
        confidence = proposal.get("confidence", 0.5)
        evidence_count = proposal.get("evidence_count", 0)

        score = (
            weights["votes"] * (vote_count / total_agents)
            + weights["critiques"] * (critique_avg / 10.0)
            + weights["confidence"] * confidence
            + weights["evidence"] * min(evidence_count / 5.0, 1.0)
        )

        return min(max(score, 0.0), 1.0)


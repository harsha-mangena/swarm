"""Convergence detection"""

from typing import Dict, List


class ConvergenceChecker:
    """Check if debate has converged"""

    def __init__(self, config):
        self.config = config

    def check(
        self,
        round_num: int,
        max_rounds: int,
        votes: Dict[str, str],
        scores: Dict[str, float],
    ) -> bool:
        """Check convergence conditions"""

        # Condition 1: Max rounds reached
        if round_num >= max_rounds:
            return True

        # Condition 2: Supermajority agreement (80%+)
        vote_counts = {}
        for proposal_id in votes.values():
            vote_counts[proposal_id] = vote_counts.get(proposal_id, 0) + 1

        if vote_counts:
            max_votes = max(vote_counts.values())
            total_votes = len(votes)
            if total_votes > 0 and max_votes / total_votes >= self.config.convergence_threshold:
                return True

        # Condition 3: Clear score margin (>0.3 difference)
        if scores:
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] > self.config.score_margin_threshold:
                return True

        return False


"""Debate state machine"""

from typing import List, Dict, Literal
from backend.agents.base import BaseAgent
from backend.models.debate import DebateState, DebatePhase
from backend.debate.scoring import DebateConfig, DebateScorer
from backend.debate.convergence import ConvergenceChecker


class DebateEngine:
    """LangGraph-style debate orchestration"""

    def __init__(self, agents: List[BaseAgent], config: DebateConfig):
        self.agents = agents
        self.config = config
        self.scorer = DebateScorer()
        self.convergence_checker = ConvergenceChecker(config)

    async def run(self, topic: str, task_id: str, max_rounds: int = 5) -> DebateState:
        """Execute full debate"""

        state: DebateState = DebateState(
            task_id=task_id,
            topic=topic,
            proposals=[],
            critiques=[],
            rebuttals=[],
            votes={},
            scores={},
            round=1,
            max_rounds=max_rounds,
            phase=DebatePhase.PROPOSAL,
            winner=None,
            converged=False,
        )

        while state.round <= max_rounds and not state.converged:
            # Collect proposals
            state = await self._collect_proposals(state)

            # Collect critiques
            state = await self._collect_critiques(state)

            # Collect rebuttals (optional)
            state = await self._collect_rebuttals(state)

            # Conduct voting
            state = await self._conduct_voting(state)

            # Calculate scores
            state = await self._calculate_scores(state)

            # Check convergence
            state.converged = self.convergence_checker.check(
                state.round,
                state.max_rounds,
                state.votes,
                state.scores,
            )

            if not state.converged:
                state.round += 1

        # Select winner
        if state.scores:
            state.winner = max(state.scores.items(), key=lambda x: x[1])[0]
            state.phase = DebatePhase.CONVERGED

        return state

    async def _collect_proposals(self, state: DebateState) -> DebateState:
        """Each agent submits a proposal"""
        proposals = []
        current_round_proposals = [
            p for p in state.proposals if p.get("round") == state.round
        ]

        for agent in self.agents:
            previous = current_round_proposals[-1] if current_round_proposals else None
            critiques = [
                c
                for c in state.critiques
                if c.get("target_proposal_id") == agent.id
                and c.get("round") == state.round - 1
            ]

            proposal_result = await agent.generate_proposal(
                topic=state.topic,
                previous_round=previous,
                critiques_received=critiques,
            )

            proposals.append({
                "agent_id": agent.id,
                "content": proposal_result.content,
                "confidence": proposal_result.confidence,
                "evidence": proposal_result.evidence,
                "round": state.round,
            })

        state.proposals.extend(proposals)
        return state

    async def _collect_critiques(self, state: DebateState) -> DebateState:
        """Each agent critiques other proposals"""
        current_proposals = [
            p for p in state.proposals if p.get("round") == state.round
        ]
        critiques = []

        for agent in self.agents:
            other_proposals = [
                p for p in current_proposals if p.get("agent_id") != agent.id
            ]

            for proposal in other_proposals:
                critique_dict = await agent.critique_proposal(
                    proposal=proposal,
                    critique_prompt=self.config.critique_prompt,
                )

                critiques.append({
                    "critic_id": agent.id,
                    "target_proposal_id": proposal.get("agent_id"),
                    "strengths": critique_dict.get("strengths", []),
                    "weaknesses": critique_dict.get("weaknesses", []),
                    "score": critique_dict.get("score", 5.0),
                    "round": state.round,
                })

        state.critiques.extend(critiques)
        return state

    async def _collect_rebuttals(self, state: DebateState) -> DebateState:
        """Agents can respond to critiques"""
        # Simplified - agents can add rebuttals
        state.rebuttals = []  # Placeholder
        return state

    async def _conduct_voting(self, state: DebateState) -> DebateState:
        """Agents vote for best proposal"""
        current_proposals = [
            p for p in state.proposals if p.get("round") == state.round
        ]
        votes = {}

        for agent in self.agents:
            other_proposals = [
                p for p in current_proposals if p.get("agent_id") != agent.id
            ]

            if other_proposals:
                vote_result = await agent.vote(
                    proposals=other_proposals,
                    voting_criteria=self.config.voting_criteria,
                )
                votes[agent.id] = vote_result.get("selected_proposal_id", "")

        state.votes = votes
        return state

    async def _calculate_scores(self, state: DebateState) -> DebateState:
        """Calculate weighted scores for each proposal"""
        current_proposals = [
            p for p in state.proposals if p.get("round") == state.round
        ]
        scores = {}

        vote_counts = self.scorer.count_votes(state.votes)

        for proposal in current_proposals:
            pid = proposal.get("agent_id")

            # Vote count
            vote_count = vote_counts.get(pid, 0)

            # Average critique score
            critiques = [
                c
                for c in state.critiques
                if c.get("target_proposal_id") == pid
                and c.get("round") == state.round
            ]
            avg_critique = (
                sum(c.get("score", 5.0) for c in critiques) / len(critiques)
                if critiques
                else 5.0
            )

            # Self-confidence
            confidence = proposal.get("confidence", 0.5)

            # Evidence count
            evidence_count = len(proposal.get("evidence", []))

            proposal_data = {
                "votes": vote_count,
                "critique_avg": avg_critique,
                "confidence": confidence,
                "evidence_count": evidence_count,
            }

            scores[pid] = self.scorer.calculate_weighted_score(
                proposal_data, self.config.weights, len(self.agents)
            )

        state.scores = scores
        return state


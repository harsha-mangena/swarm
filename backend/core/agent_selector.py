"""Agent selection with pheromone learning"""

import random
from typing import List, Dict
from backend.agents.base import BaseAgent
from backend.core.decomposer import TaskNode


class AgentSelector:
    """Select best agent using confidence + pheromone learning"""

    def __init__(self, agents: List[BaseAgent]):
        self.agents = {a.id: a for a in agents}
        self.pheromone_matrix: Dict[str, Dict[str, float]] = {}

        # Hyperparameters
        self.alpha = 1.0  # Pheromone importance
        self.beta = 2.0  # Heuristic importance
        self.evaporation_rate = 0.1
        self.initial_pheromone = 1.0

    async def select(self, task: TaskNode, available_agents: List[str]) -> str:
        """Select best agent for task"""

        # Initialize pheromones if needed
        task_type = task.agent_type
        if task_type not in self.pheromone_matrix:
            self.pheromone_matrix[task_type] = {
                aid: self.initial_pheromone for aid in available_agents
            }

        # Calculate selection probabilities
        probabilities = []
        for agent_id in available_agents:
            agent = self.agents[agent_id]

            # Pheromone strength (learned)
            pheromone = self.pheromone_matrix[task_type].get(
                agent_id, self.initial_pheromone
            )

            # Heuristic score (immediate)
            heuristic = await self._compute_heuristic(agent, task)

            # Combined probability
            prob = (pheromone ** self.alpha) * (heuristic ** self.beta)
            probabilities.append(prob)

        # Normalize and select
        total = sum(probabilities)
        if total == 0:
            return random.choice(available_agents)

        probabilities = [p / total for p in probabilities]
        selected_idx = random.choices(
            range(len(available_agents)), weights=probabilities
        )[0]
        return available_agents[selected_idx]

    async def _compute_heuristic(
        self, agent: BaseAgent, task: TaskNode
    ) -> float:
        """Compute immediate fitness score"""

        # Skill match
        skill_match = self._skill_similarity(agent.capabilities, task.agent_type)

        # Historical success rate
        success_rate = agent.get_success_rate(task.agent_type)

        # Current availability
        availability = 1.0 - agent.current_load

        return 0.4 * skill_match + 0.4 * success_rate + 0.2 * availability

    def _skill_similarity(self, capabilities: List, task_type: str) -> float:
        """Check if agent capabilities match task type"""
        task_type_lower = task_type.lower()
        for cap in capabilities:
            if task_type_lower in str(cap).lower():
                return 1.0
        return 0.5  # Partial match

    def update_pheromones(
        self, task_type: str, agent_id: str, success: bool, quality: float
    ):
        """Update pheromone trails after task completion"""

        # Evaporate all trails
        if task_type in self.pheromone_matrix:
            for aid in self.pheromone_matrix[task_type]:
                self.pheromone_matrix[task_type][aid] *= (1 - self.evaporation_rate)

        # Deposit based on success
        if success:
            if task_type not in self.pheromone_matrix:
                self.pheromone_matrix[task_type] = {}

            current = self.pheromone_matrix[task_type].get(
                agent_id, self.initial_pheromone
            )
            self.pheromone_matrix[task_type][agent_id] = current + quality


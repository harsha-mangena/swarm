"""Reviewer agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class ReviewerAgent(BaseAgent):
    """Review and critique agent"""

    agent_type = "reviewer"
    capabilities = [AgentCapability.REVIEW]

    async def process(self, task: Task) -> AgentResult:
        """Review and critique solution"""
        prompt = f"""<role>
You are a {self.agent_type.capitalize()}, an expert reviewer providing constructive, 
actionable feedback. You collaborate with other agents to ensure quality.
</role>

<context>
You are part of a multi-agent team reviewing work for quality. Your critique will 
help improve the final output. Be constructive but thorough.

You have access to web_search tool - use it to verify facts or check best practices.
</context>

<task>
{task.description}
</task>

<solution_to_review>
{task.result or 'No solution yet'}
</solution_to_review>

<evaluation_criteria>
1. CORRECTNESS (weight: 40%)
   - Does it fulfill stated requirements?
   - Are there factual or logical errors?

2. QUALITY (weight: 25%)
   - Does it follow best practices?
   - Is it well-structured and maintainable?

3. COMPLETENESS (weight: 20%)
   - Are all requirements addressed?
   - Are edge cases handled?

4. CLARITY (weight: 15%)
   - Is it readable and understandable?
   - Is documentation adequate?
</evaluation_criteria>

<scoring_rubric>
5 - Excellent: Exceeds requirements, exemplary quality
4 - Good: Meets all requirements, minor improvements possible
3 - Acceptable: Meets most requirements, some issues
2 - Needs Work: Significant gaps or issues
1 - Inadequate: Fails to meet requirements
</scoring_rubric>

<output_format>
Provide structured critique:
1. SCORES: Rate each criterion 1-5 with brief reasoning
2. STRENGTHS: What works well (2-3 points)
3. ISSUES: Problems found with severity (CRITICAL/MAJOR/MINOR) and fix suggestions
4. WEIGHTED_TOTAL: Calculate overall score (0-5.0)
5. VERDICT: APPROVE (4+), REVISE (2.5-4), or REJECT (<2.5)
</output_format>"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.7,
        )


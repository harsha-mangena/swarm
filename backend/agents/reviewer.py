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
        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology.
Review is performed by decomposing evaluation into atomic criteria and atomic defects.
</aot_framework>

<role>
You are a {self.agent_type.capitalize()}, an expert reviewer producing constructive, actionable feedback.
</role>

<context>
You are part of a multi-agent team reviewing work for quality.
You have access to web_search and may use it to verify claims or best practices.
</context>

<task>
{task.description}
</task>

<solution_to_review>
{task.result or 'No solution yet'}
</solution_to_review>

<atomic_review_protocol>
PHASE 1: Decompose evaluation into independent criterion-atoms
- C1: Correctness vs requirements
- C2: Quality / best practices
- C3: Completeness / edge cases
- C4: Clarity / maintainability

PHASE 2: Score each criterion independently (no cross-contamination)
Use 1-5 scale, and provide evidence.

PHASE 3: Extract defect atoms
- Each defect is a single concrete issue with location/context
- Tag severity: CRITICAL|MAJOR|MINOR
- Provide a minimally sufficient fix suggestion

PHASE 4: Contract to final verdict
- Compute weighted score (Correctness 0.40, Quality 0.25, Completeness 0.20, Clarity 0.15)
- Derive verdict: APPROVE (>=4.0), REVISE (2.5-4.0), REJECT (<2.5)
</atomic_review_protocol>

<output_schema>
Return JSON only:
```json
{{
   "scores": {{
      "correctness": {{"score": 0, "evidence": ["..."]}},
      "quality": {{"score": 0, "evidence": ["..."]}},
      "completeness": {{"score": 0, "evidence": ["..."]}},
      "clarity": {{"score": 0, "evidence": ["..."]}}
   }},
   "defects": [
      {{
         "id": "D1",
         "severity": "CRITICAL|MAJOR|MINOR",
         "issue": "single issue statement",
         "location": "file/symbol/section if known",
         "impact": "what breaks",
         "fix": "minimal actionable fix"
      }}
   ],
   "strengths": ["..."],
   "weighted_total": 0.0,
   "verdict": "APPROVE|REVISE|REJECT",
   "rework_instructions": [
      {{"priority": "high|medium|low", "instruction": "...", "maps_to": ["D1"]}}
   ]
}}
```
</output_schema>
"""

        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.7,
        )


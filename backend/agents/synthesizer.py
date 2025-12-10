"""Synthesizer agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class SynthesizerAgent(BaseAgent):
    """Final synthesis agent"""

    agent_type = "synthesizer"
    capabilities = [AgentCapability.SYNTHESIS]

    async def process(self, task: Task) -> AgentResult:
        """Synthesize final result from multiple inputs"""
        # Extract context from task
        context = task.context or {}
        previous_work = context.get("previous_work", "")
        coordination_context = context.get("coordination_context", "")
        
        # Build comprehensive synthesis prompt
        prompt = f"""<role>
You are a Synthesis Specialist. Your task is to integrate outputs from multiple agents 
into a unified, coherent response while preserving attribution and resolving conflicts.
</role>

<context>
You are the final agent in a multi-agent pipeline. Your output will be the FINAL ANSWER 
presented to the user. Ensure it is comprehensive and well-structured.

You have access to web_search tool - use it to fill any gaps or verify information.
</context>

<original_task>
{task.description}
</original_task>

<agent_outputs>
{previous_work if previous_work else coordination_context}
</agent_outputs>

<synthesis_protocol>
1. THEME EXTRACTION
   - Identify key themes across all agent inputs
   - Map which agent contributed which insights

2. CONFLICT RESOLUTION
   - Flag contradictions between agents
   - Evaluate evidence strength for each position
   - Resolve or present both perspectives with weights

3. INTEGRATION
   - Weave insights into coherent narrative
   - Preserve attribution for key claims: [Agent: insight]
   - Eliminate redundancy while maintaining coverage

4. GAP IDENTIFICATION
   - Note missing perspectives or information
   - Flag areas that may need follow-up
</synthesis_protocol>

<output_requirements>
Your final output should include:
1. EXECUTIVE SUMMARY: Key findings in 2-3 sentences
2. SYNTHESIZED ANALYSIS: Full integrated narrative
3. CONFLICTS RESOLVED: Any contradictions and how resolved
4. ATTRIBUTION MAP: Key insights with source agent
5. GAPS IDENTIFIED: Missing information or perspectives

Prefix your response with: FINAL ANSWER
</output_requirements>"""
        
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.85,
        )


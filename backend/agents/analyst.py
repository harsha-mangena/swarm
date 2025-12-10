"""Analyst agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class AnalystAgent(BaseAgent):
    """Analysis and planning agent"""

    agent_type = "analyst"
    capabilities = [AgentCapability.ANALYSIS]

    async def process(self, task: Task) -> AgentResult:
        """Perform analysis"""
        context = task.context or {}
        is_rework = "rework_instruction" in context
        
        # Autonomous web search for current information
        web_context = ""
        try:
            search_query = task.description[:200]  # Use task description as search query
            web_results = await self.auto_web_search(search_query, max_results=3)
            if web_results:
                web_context = f"""
<web_research>
Recent information gathered from web search:
{web_results}
</web_research>
"""
        except Exception as e:
            print(f"AnalystAgent web search skipped: {e}")
        
        # Build rework section if applicable
        rework_section = ""
        if is_rework:
            rework_section = f"""
<previous_attempt>
Score: {context.get('supervisor_score', 'N/A')}/10
Feedback: {context.get('supervisor_feedback', '')}
Your previous output: {context.get('previous_attempt', '')[:1000]}...
</previous_attempt>

<rework_instruction>
Address the supervisor's feedback above. Focus on improving the identified weaknesses.
</rework_instruction>"""
        
        prompt = f"""<role>
You are a {self.agent_type.capitalize()}, collaborating with other specialized agents 
to solve a complex task. Your expertise: {self.agent_type} with deep analytical skills.
</role>

<context>
You are part of a multi-agent team. Other agents may continue your work or build upon 
your analysis. If you cannot fully complete the task, that's OK—provide what you can 
so another agent can continue.
</context>

<task>
{task.description}
</task>

<original_context>
{context.get('original_task', task.description)}
</original_context>
{web_context}{rework_section}
<analytical_framework>
Apply this structured analysis:

1. SITUATION ASSESSMENT
   - Current state identification
   - Key metrics and indicators
   - Relevant context

2. PATTERN ANALYSIS
   - Key patterns and trends
   - Anomalies or outliers
   - Correlations

3. CAUSAL REASONING
   - Root causes
   - Contributing factors
   - Dependencies

4. IMPLICATIONS
   - Short-term impacts
   - Long-term consequences
   - Risk assessment (high/medium/low)

5. RECOMMENDATIONS
   - Prioritized actions
   - Trade-off analysis
   - Implementation considerations
</analytical_framework>

<output_requirements>
- Provide data-driven conclusions with specific evidence
- Quantify uncertainty where applicable (high/medium/low confidence)
- Make recommendations actionable and prioritized
- If you have the final answer for the team, prefix with: FINAL ANSWER
</output_requirements>"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.85 if is_rework else 0.75,
        )


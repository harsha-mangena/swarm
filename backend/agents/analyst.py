"""Analyst agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability
from backend.prompts.citation_requirements import CITATION_INSTRUCTIONS, SOURCE_USAGE_INSTRUCTIONS
from backend.prompts.depth_requirements import DEPTH_REQUIREMENTS, FORBIDDEN_OUTPUTS


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
        sources_metadata = []
        try:
            search_query = task.description[:200]
            web_results, sources_metadata = await self.auto_web_search(search_query, max_results=5)
            if web_results:
                web_context = f"""
<web_sources>
{web_results}
</web_sources>

{SOURCE_USAGE_INSTRUCTIONS}
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

{CITATION_INSTRUCTIONS}
{DEPTH_REQUIREMENTS}
{FORBIDDEN_OUTPUTS}

<analytical_framework>
Apply this structured analysis:

1. SITUATION ASSESSMENT
   - Current state with specific data points [cite sources]
   - Key metrics and indicators from research
   - Relevant context with evidence

2. PATTERN ANALYSIS
   - Key patterns and trends (with numbers/percentages)
   - Anomalies or outliers
   - Correlations with supporting data

3. CAUSAL REASONING
   - Root causes with evidence
   - Contributing factors
   - Dependencies and relationships

4. IMPLICATIONS
   - Short-term impacts (specific outcomes)
   - Long-term consequences
   - Risk assessment with probability estimates

5. RECOMMENDATIONS
   - Prioritized actions with rationale
   - Trade-off analysis
   - Implementation considerations
</analytical_framework>

<output_requirements>
- MUST cite sources using [1], [2], [3] format
- Provide data-driven conclusions with specific evidence
- Include concrete numbers, examples, and data points
- Minimum 500 words of substantive analysis
- If you have the final answer for the team, prefix with: FINAL ANSWER
</output_requirements>"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.85 if is_rework else 0.75,
            sources=sources_metadata,
            metadata={"agent_type": self.agent_type}
        )



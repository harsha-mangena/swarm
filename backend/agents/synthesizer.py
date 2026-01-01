"""Synthesizer agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability
from backend.prompts.depth_requirements import DEPTH_REQUIREMENTS, FORBIDDEN_OUTPUTS


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
        agent_outputs = context.get("agent_outputs", {})
        
        # Build comprehensive agent outputs section
        agent_outputs_text = previous_work if previous_work else coordination_context
        
        # If we have structured agent_outputs dict, format it properly
        if agent_outputs and isinstance(agent_outputs, dict):
            formatted_outputs = []
            for i, (agent_id, output) in enumerate(agent_outputs.items(), 1):
                formatted_outputs.append(f"""
<agent_{i}_output agent_id="{agent_id}">
{output}
</agent_{i}_output>
""")
            if formatted_outputs:
                agent_outputs_text = "\n".join(formatted_outputs)
        
        # Count agents for explicit requirements
        agent_count = len(agent_outputs) if agent_outputs else 1
        
        # Build comprehensive synthesis prompt
        prompt = f"""<role>
You are a Synthesis Specialist. Your task is to integrate outputs from multiple agents 
into a unified, coherent response while preserving ALL information from each agent.
</role>

<context>
You are the final agent in a multi-agent pipeline. Your output will be the FINAL ANSWER 
presented to the user. This is the ONLY response the user will see, so it must be COMPLETE.
</context>

<original_task>
{task.description}
</original_task>

<agent_outputs>
{agent_outputs_text}
</agent_outputs>

<critical_instruction>
YOU MUST COMBINE ALL OUTPUTS COMPLETELY.
- DO NOT condense, summarize, or omit ANY information from the agent outputs above
- DO NOT say "as mentioned above" or refer to other agents - include their full content
- DO NOT truncate or abbreviate - include EVERYTHING
- Your output MUST include findings from ALL {agent_count} agent(s) listed above
- If an agent provided citations [1], [2], etc., preserve and include them
</critical_instruction>

{DEPTH_REQUIREMENTS}
{FORBIDDEN_OUTPUTS}

<synthesis_protocol>
1. THEME EXTRACTION
   - Identify ALL key themes across all agent inputs
   - Map which agent contributed which insights

2. COMPLETE INTEGRATION
   - Include EVERY insight, data point, and finding from each agent
   - Weave into coherent narrative without losing any detail
   - Preserve all citations: [1], [2], [3] format

3. CONFLICT RESOLUTION
   - Flag contradictions between agents
   - Present both perspectives with evidence

4. GAP IDENTIFICATION
   - Note missing perspectives or information
   - Flag areas that may need follow-up
</synthesis_protocol>

<output_requirements>
Your final output MUST include:

1. EXECUTIVE SUMMARY (2-3 sentences with key findings)

2. COMPREHENSIVE ANALYSIS (minimum 800 words)
   - Include ALL findings from ALL agents
   - Preserve all data points, statistics, and examples
   - Maintain all citations

3. CONFLICTS & CONSIDERATIONS
   - Any contradictions found and how resolved
   
4. RECOMMENDATIONS
   - Specific, actionable next steps

5. SOURCES (if agents provided citations)
   - List all cited sources with URLs

Prefix your response with: FINAL ANSWER
</output_requirements>"""
        
        # Additional web search for gaps if available
        supplementary_sources = []
        try:
            web_results, supplementary_sources = await self.auto_web_search(
                task.description[:100], max_results=3
            )
        except:
            pass
        
        content = await self._llm_call(prompt)

        # Check for completeness indicators
        if len(content) < 500:
            # Output seems too short, add warning
            content = f"[WARNING: Output may be incomplete]\n\n{content}"

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.85,
            sources=supplementary_sources,
            metadata={"agent_type": self.agent_type}
        )



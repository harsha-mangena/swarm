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
        context = task.context or {}
        previous_work = context.get("previous_work", "")
        coordination_context = context.get("coordination_context", "")

        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology.
Synthesis is performed by contracting atomic contributions from upstream agents.
</aot_framework>

<role>
You are a Synthesis Specialist.
You integrate outputs from multiple agents into a unified answer while preserving provenance.
</role>

<context>
You are the final agent in a multi-agent pipeline.
You may use web_search to verify critical claims or fill essential gaps.
</context>

<original_task>
{task.description}
</original_task>

<agent_outputs>
{agent_outputs_text}
</agent_outputs>

<atomic_extraction>
PHASE 1: Extract atomic contributions
- Convert each agent output into a set of ATOMS (single claim, insight, step, or recommendation)
- For each atom: attach source agent label (if present) and supporting evidence if any

Atom format:
```json
{{
   "atom_id": "S1",
   "source": "agent_name_or_unknown",
   "type": "fact|assumption|recommendation|code_change|risk|open_question",
   "content": "single atomic statement",
   "support": ["evidence or citation if provided"],
   "confidence": "high|medium|low"
}}
```
</atomic_extraction>

<conflict_detection>
PHASE 2: Detect conflicts
- If atoms contradict, list them explicitly
- Do not silently reconcile; choose based on evidence strength or keep both with caveats
</conflict_detection>

<contraction_synthesis>
PHASE 3: Contract atoms into final response
- Treat the set of accepted atoms as KNOWN CONDITIONS
- Build: executive summary → main solution → tradeoffs/risks → next steps
- Remove redundancy by merging only if semantics are identical
</contraction_synthesis>

<output_schema>
Return JSON only:
```json
{{
   "atomic_contributions": [{{"atom_id": "S1", "source": "...", "type": "...", "content": "...", "confidence": "..."}}],
   "conflicts": [
      {{"conflict_id": "K1", "atoms": ["S1", "S2"], "resolution": "chosen|both|needs_more_info", "notes": "..."}}
   ],
   "gaps": ["missing info needed"],
   "final_answer": {{
      "executive_summary": "2-3 sentences",
      "answer": "full user-facing answer",
      "risks_and_tradeoffs": ["..."],
      "next_steps": ["..."],
      "confidence": "high|medium|low"
   }}
}}
```

Prefix your message with: FINAL ANSWER
</output_schema>
"""

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



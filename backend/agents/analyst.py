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
        
            prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology. Each reasoning unit is atomic and self-contained.
The Markov property applies: your current state depends only on the present question, not accumulated history.
</aot_framework>

<role>
You are a {self.agent_type.capitalize()} with deep analytical expertise.
You collaborate with specialized agents, each processing independent atomic units.
Your outputs become known conditions for dependent agents downstream.
</role>

<task>
{task.description}
</task>

<original_context>
{context.get('original_task', task.description)}
</original_context>

{web_context}
{rework_section}

<atomic_decomposition_protocol>
PHASE 1: DECOMPOSE into atomic subquestions

Identify and classify each analytical component:

INDEPENDENT ATOMS (Q_ind) - Solvable with only task information:
- A1: [Atomic question about current state/metrics]
- A2: [Atomic question about patterns/trends]
- A3: [Atomic question about causal factors]

DEPENDENT ATOMS (Q_dep) - Require answers from other atoms:
- A4: [Depends on A1, A2] → Implications synthesis
- A5: [Depends on A3, A4] → Recommendations derivation

Express as DAG:
A1 ──┐
       ├──► A4 ──┐
A2 ──┘         ├──► A5 (Final)
A3 ────────────┘
</atomic_decomposition_protocol>

<atomic_solving_protocol>
PHASE 2: SOLVE each atom independently

For each INDEPENDENT atom, produce:
```json
{{
   "atom_id": "A1",
   "question": "specific atomic question",
   "analysis": "focused analysis using only available context",
   "conclusion": "atomic finding",
   "evidence": ["specific data point 1", "specific data point 2"],
   "confidence": "high|medium|low",
   "uncertainty_source": "what would change this conclusion"
}}
```

CRITICAL: Process each atom in isolation. Do NOT let conclusions from one atom influence another during this phase.
</atomic_solving_protocol>

<contraction_protocol>
PHASE 3: CONTRACT dependent atoms

For each DEPENDENT atom:
1. Incorporate solved atoms as KNOWN CONDITIONS
2. Reformulate the dependent question with these knowns
3. Solve the contracted (simplified) question
4. Repeat until final answer emerges

Contraction format:
```json
{{
   "atom_id": "A4",
   "depends_on": ["A1", "A2"],
   "known_conditions": {{
      "from_A1": "extracted conclusion",
      "from_A2": "extracted conclusion"
   }},
   "contracted_question": "simplified question given knowns",
   "analysis": "reasoning on contracted question only",
   "conclusion": "atomic finding"
}}
```
</contraction_protocol>

<output_schema>
Return structured JSON:
```json
{{
   "decomposition": {{
      "independent_atoms": [
         {{"id": "A1", "question": "...", "depends_on": []}},
         {{"id": "A2", "question": "...", "depends_on": []}},
         {{"id": "A3", "question": "...", "depends_on": []}}
      ],
      "dependent_atoms": [
         {{"id": "A4", "question": "...", "depends_on": ["A1", "A2"]}},
         {{"id": "A5", "question": "...", "depends_on": ["A3", "A4"]}}
      ]
   }},
   "atomic_solutions": {{
      "A1": {{"conclusion": "...", "evidence": [], "confidence": "..."}},
      "A2": {{"conclusion": "...", "evidence": [], "confidence": "..."}},
      "A3": {{"conclusion": "...", "evidence": [], "confidence": "..."}}
   }},
   "contractions": {{
      "A4": {{"known_conditions": {{}}, "contracted_question": "...", "conclusion": "..."}},
      "A5": {{"known_conditions": {{}}, "contracted_question": "...", "conclusion": "..."}}
   }},
   "final_synthesis": {{
      "executive_summary": "2-3 sentences",
      "key_findings": ["finding with evidence citation"],
      "recommendations": [
         {{"action": "...", "priority": "high|medium|low", "rationale": "from atom X"}}
      ],
      "risk_assessment": {{"level": "high|medium|low", "factors": []}},
      "confidence_map": {{"A1": "high"}}
   }}
}}
```

If this is the final answer for the team, prefix with: FINAL ANSWER
</output_schema>

<anti_contamination_directive>
CRITICAL: Maintain atomic independence during solving phase.
- Do NOT cross-reference between atoms until contraction phase
- Each atom's confidence is assessed independently
- Conflicting conclusions between atoms must be explicitly flagged, not silently reconciled
</anti_contamination_directive>
"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.85 if is_rework else 0.75,
        )


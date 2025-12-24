"""Coder agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class CoderAgent(BaseAgent):
    """Code generation agent"""

    agent_type = "coder"
    capabilities = [AgentCapability.CODING]

    async def process(self, task: Task) -> AgentResult:
        """Generate code solution"""
        
        # Autonomous web search for API docs and best practices
        web_context = ""
        try:
            # Extract key technical terms for search
            search_query = f"programming {task.description[:150]} best practices"
            web_results = await self.auto_web_search(search_query, max_results=3)
            if web_results:
                web_context = f"""
<web_research>
Recent documentation and best practices:
{web_results}
</web_research>
"""
        except Exception as e:
            print(f"CoderAgent web search skipped: {e}")
        
        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology. Each reasoning unit is atomic and self-contained.
The Markov property applies: your current state depends only on the present question, not accumulated history.
</aot_framework>

<role>
You are a {self.agent_type.capitalize()}, an expert software engineer.
You collaborate with other agents; your output must be immediately actionable as code changes.
</role>

{web_context}

<task>
{task.description}
</task>

<additional_context>
{task.context or 'None provided'}
</additional_context>

<atomic_coding_protocol>
PHASE 1: DECOMPOSE into atomic implementation tasks

INDEPENDENT ATOMS (can be implemented without other atoms):
- A1: Identify target files/symbols and current behavior
- A2: Define required behavior and acceptance criteria
- A3: Draft minimal code changes (patch plan)

DEPENDENT ATOMS:
- A4: Implement code changes (depends on A1-A3)
- A5: Add/update tests and verify (depends on A4)

Represent as DAG:
A1 ──┐
         ├──► A4 ──► A5
A2 ──┤
A3 ──┘
</atomic_coding_protocol>

<constraints>
- Make the smallest, correct change that satisfies requirements
- Preserve existing public APIs unless task requires breaking changes
- Avoid unrelated refactors
- Prefer existing project patterns and utilities
</constraints>

<output_schema>
Return JSON with an implementation-ready patch plan and code.
```json
{{
    "atoms": {{
        "A1": {{"finding": "files/symbols", "notes": "current behavior"}},
        "A2": {{"acceptance_criteria": ["..."]}},
        "A3": {{
            "patch_plan": [
                {{"file": "path", "change": "what/why", "risk": "low|medium|high"}}
            ]
        }},
        "A4": {{
            "code_changes": [
                {{"file": "path", "diff_summary": "..."}}
            ]
        }},
        "A5": {{
            "tests": [{{"file": "path", "what": "test scenario"}}],
            "verification": ["commands to run"],
            "expected_results": ["..."],
            "fallback_plan": "if tests fail"
        }}
    }},
    "final_answer": "If this is final, also include a concise human-readable summary here."
}}
```

If this is the final answer for the team, prefix your message with: FINAL ANSWER
</output_schema>

<anti_contamination_directive>
CRITICAL: Keep atoms independent until execution phase; do not invent repo state.
If you lack concrete repo details, state assumptions explicitly and propose verification steps.
</anti_contamination_directive>
"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.8,
        )


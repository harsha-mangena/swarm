"""Researcher agent"""

from typing import List, Dict, Any
from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class ResearcherAgent(BaseAgent):
    """Deep web research with iterative refinement"""

    agent_type = "researcher"
    capabilities = [AgentCapability.RESEARCH]

    RESEARCH_CONFIG = {
        "max_iterations": 10,
        "parallel_searches": 3,
        "min_sources_per_claim": 2,
    }

    async def process(self, task: Task) -> AgentResult:
        """Execute research workflow"""
        query = task.description
        context = task.context or {}
        
        # Check if this is a rework request
        is_rework = "rework_instruction" in context
        
        # Decompose into sub-questions
        sub_questions = await self._decompose_query(query)

        # Parallel search for each sub-question
        all_results = []
        for sq in sub_questions:
            results = await self._search_with_refinement(sq)
            all_results.extend(results)

        # Identify knowledge gaps
        gaps = self._identify_gaps(query, all_results)

        # Fill gaps with targeted searches
        if gaps:
            gap_results = await self._fill_gaps(gaps)
            all_results.extend(gap_results)

        # Synthesize findings (with rework context if applicable)
        synthesis = await self._synthesize(query, all_results, context if is_rework else None)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=synthesis,
            confidence=0.9 if is_rework else 0.8,
            evidence=[r.get("url", "") for r in all_results[:5]],
        )

    async def _decompose_query(self, query: str) -> List[str]:
        """Decompose query into sub-questions"""
        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology.
Decompose the research query into atomic, independently answerable sub-questions.
</aot_framework>

<role>
You are a research analyst specializing in atomic decomposition for evidence gathering.
</role>

<query>
{query}
</query>

<atomic_decomposition_rules>
- Each atom must be answerable via web_search/web_fetch
- Avoid multi-part questions; one verifiable claim per atom
- Separate definitions/context, facts/metrics, comparisons, and counterpoints
- Mark dependencies explicitly (DAG)
</atomic_decomposition_rules>

<output_format>
Return JSON only:
```json
{{
    "atoms": [
        {{"id": "R1", "question": "...", "type": "definition|fact|comparison|counterpoint", "depends_on": []}},
        {{"id": "R2", "question": "...", "type": "fact", "depends_on": []}},
        {{"id": "R3", "question": "...", "type": "comparison", "depends_on": ["R1", "R2"]}}
    ]
}}
```
</output_format>"""
        try:
            response = await self._llm_call(prompt)
            # Simple parsing - in production would use structured output
            # For now, return the original query as a single sub-question
            return [query]
        except Exception:
            return [query]

    async def _search_with_refinement(
        self, query: str, max_iterations: int = 3
    ) -> List[Dict]:
        """Iterative search refinement"""
        results = []
        current_query = query

        for i in range(max_iterations):
            try:
                search_results = await self.use_tool(
                    "web_search", {"query": current_query, "max_results": 5}
                )
                results.extend(search_results)

                if self._sufficient_results(results):
                    break

                # Refine query based on what we found
                current_query = await self._refine_query(query, results)
            except Exception as e:
                # If tool fails, break
                break

        return results

    def _sufficient_results(self, results: List[Dict]) -> bool:
        """Check if we have enough quality results"""
        return len(results) >= 5

    async def _refine_query(self, original_query: str, results: List[Dict]) -> str:
        """Refine search query based on results"""
        # Simple refinement - in production would use LLM
        return original_query

    def _identify_gaps(self, query: str, results: List[Dict]) -> List[str]:
        """Identify knowledge gaps"""
        # Simplified - would use LLM to analyze
        return []

    async def _fill_gaps(self, gaps: List[str]) -> List[Dict]:
        """Fill identified gaps"""
        all_results = []
        for gap in gaps:
            try:
                results = await self.use_tool(
                    "web_search", {"query": gap, "max_results": 3}
                )
                all_results.extend(results)
            except Exception:
                continue
        return all_results

    async def _synthesize(self, query: str, results: List[Dict], rework_context: Dict = None) -> str:
        """Synthesize research findings"""
        results_text = "\n\n".join(
            [
                f"Source: {r.get('title', 'Unknown')}\nURL: {r.get('url', '')}\nContent: {r.get('content', '')[:500]}"
                for r in results[:10]
            ]
        )
        
        # Build rework section if applicable
        rework_section = ""
        if rework_context:
            rework_section = f"""
<previous_attempt>
Score: {rework_context.get('supervisor_score', 'N/A')}/10
Feedback: {rework_context.get('supervisor_feedback', '')}
Your previous output: {rework_context.get('previous_attempt', '')[:1000]}...
</previous_attempt>

<rework_instruction>
Address the supervisor's feedback. Improve based on identified weaknesses.
</rework_instruction>"""

        prompt = f"""<aot_framework>
    You operate using Atom of Thought (AoT) methodology.
    Synthesis must be a contraction over atomic evidence extracted from sources.
    </aot_framework>

    <role>
    You are a senior research analyst: source evaluation, evidence extraction, and rigorous synthesis.
    </role>

    <research_query>
    {query}
    </research_query>

    <sources>
    {results_text}
    </sources>
    {rework_section}

    <atomic_evidence_extraction>
    PHASE 1: Extract atomic claims from sources
    - Each claim must be a single verifiable statement
    - Attach provenance: URL + short quote/summary
    - Assess reliability and recency

    For each source, produce atomic claims:
    ```json
    {{
      "source_url": "...",
      "source_title": "...",
      "reliability": "high|medium|low",
      "claims": [
        {{"claim_id": "C1", "claim": "...", "support": "quote or summary", "confidence": "high|medium|low"}}
      ]
    }}
    ```
    </atomic_evidence_extraction>

    <conflict_detection>
    PHASE 2: Identify conflicts
    - If two claims disagree, list them explicitly
    - Do not reconcile conflicts without additional evidence
    </conflict_detection>

    <contraction_synthesis>
    PHASE 3: Contract claims into a final answer
    - Use only extracted claims as known conditions
    - If evidence is insufficient, say what is unknown and what to search next
    </contraction_synthesis>

    <output_requirements>
    Return:
    1) Summary (2-3 sentences)
    2) Findings (bullets with inline citations: [URL])
    3) Conflicts (explicit)
    4) Limitations / Unknowns
    5) Confidence (high/medium/low) + why

    If you have the final answer, prefix with: FINAL ANSWER
    </output_requirements>"""
        return await self._llm_call(prompt)


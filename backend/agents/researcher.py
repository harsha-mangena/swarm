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
        prompt = f"""<role>
You are a research analyst breaking down complex queries into manageable sub-questions.
</role>

<instructions>
Decompose this research query into 2-4 atomic sub-questions:

1. What specific FACTS are needed?
2. What CONTEXT is required to understand the topic?
3. What COMPARISONS or alternatives are relevant?
4. What EVIDENCE would support conclusions?

Each sub-question should be:
- Answerable with available research tools
- Specific and focused
- Independent but complementary
</instructions>

<query>{query}</query>

<output_format>
Return JSON: {{"sub_questions": ["question 1", "question 2", ...]}}
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

        prompt = f"""<role>
You are a senior research analyst synthesizing findings into a comprehensive report.
Your expertise: systematic information gathering, source evaluation, evidence-based synthesis.
</role>

<context>
You are part of a multi-agent team. If you have the final answer, prefix with: FINAL ANSWER
</context>

<research_query>
{query}
</research_query>

<sources>
{results_text}
</sources>
{rework_section}
<synthesis_protocol>
1. COMBINE findings into a coherent narrative
2. CITE sources inline: [Source: description]
3. FLAG conflicting information explicitly
4. STATE confidence levels: high/medium/low
5. IDENTIFY gaps in available information
</synthesis_protocol>

<output_requirements>
- Summary: Key findings in 2-3 sentences
- Synthesis: Integrated narrative with inline citations
- Conflicts: Any contradictory information found
- Limitations: Known gaps or caveats
- Confidence: Overall confidence in conclusions (high/medium/low)
</output_requirements>"""
        return await self._llm_call(prompt)


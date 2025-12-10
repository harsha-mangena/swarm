"""Query expansion"""

from typing import Dict, Any, List
from pydantic import BaseModel
from backend.llm.router import SwarmOSRouter


class QueryExpansion(BaseModel):
    """Query expansion result"""

    original: str
    execution_mode: str  # "direct" or "decompose"
    expanded_queries: List[str] = []
    clarifying_questions: List[str] = []
    intent_hypotheses: List[str] = []
    sub_queries: List[str] = []
    requires_debate: bool = False
    suggested_agents: List[str] = []


class QueryExpander:
    """Expand ambiguous queries into comprehensive task plans"""

    COMPLEXITY_SIGNALS = [
        "multiple_entities",
        "temporal_sequence",
        "conditional_logic",
        "cross_domain",
        "ambiguous_scope",
        "implicit_requirements",
    ]

    DECOMPOSITION_THRESHOLD = 0.4

    def __init__(self, llm_router: SwarmOSRouter):
        self.llm_router = llm_router

    async def expand(self, query: str) -> QueryExpansion:
        """Analyze and expand query"""
        try:
            complexity = await self._assess_complexity(query)

            if complexity < self.DECOMPOSITION_THRESHOLD:
                return QueryExpansion(
                    original=query,
                    execution_mode="direct",
                    expanded_queries=[query],
                    requires_debate=False,
                )

            # Use LLM for multi-perspective expansion
            expansion = await self._llm_expand(query)

            return QueryExpansion(
                original=query,
                execution_mode="decompose",
                clarifying_questions=expansion.get("clarifications", []),
                intent_hypotheses=expansion.get("intents", []),
                sub_queries=expansion.get("sub_queries", [query]),
                requires_debate=expansion.get("complexity", 0) > 0.7,
                suggested_agents=self._suggest_agents(expansion),
            )
        except Exception as e:
            # Fallback to simple direct execution
            print(f"Query expansion error: {e}")
            import traceback
            traceback.print_exc()
            return QueryExpansion(
                original=query,
                execution_mode="direct",
                expanded_queries=[query],
                requires_debate=False,
            )

    async def _assess_complexity(self, query: str) -> float:
        """Score query complexity 0-1"""
        # Simple heuristic-based complexity assessment
        # Check for complexity signals without LLM call
        complexity_indicators = [
            " and ", " or ", " then ", " after ", " before ",
            " multiple ", " several ", " various ", " different ",
            " analyze ", " compare ", " evaluate ", " assess "
        ]
        
        query_lower = query.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        # Simple scoring: more indicators = higher complexity
        base_complexity = min(0.3 + (indicator_count * 0.1), 0.9)
        
        # Try LLM-based assessment if available, but don't fail if it doesn't work
        try:
            prompt = f"""<role>
You are analyzing query complexity for a multi-agent system.
</role>

<query>{query}</query>

<complexity_signals>
Check for these indicators:
- Multiple entities or concepts
- Temporal sequences or dependencies
- Conditional logic or branching
- Cross-domain knowledge requirements
- Ambiguous scope or implicit requirements
</complexity_signals>

<scoring>
- 0.0-0.3: Simple, single-step task
- 0.3-0.6: Moderate, may need decomposition
- 0.6-1.0: Complex, requires multiple agents
</scoring>

<output_format>
Return JSON: {{"overall": 0.0-1.0, "signals_detected": ["list of signals"]}}
</output_format>"""
            response = await self.llm_router.completion(
                model="auto",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            import json
            data = json.loads(response.choices[0].message.content)
            return float(data.get("overall", base_complexity))
        except Exception as e:
            print(f"LLM complexity assessment failed, using heuristic: {e}")
            return base_complexity

    async def _llm_expand(self, query: str) -> Dict[str, Any]:
        """Use LLM to expand query from multiple perspectives"""
        # Default fallback response
        default_response = {
            "clarifications": [],
            "intents": [query],
            "assumptions": [],
            "sub_queries": [query],
            "complexity": 0.5,
        }
        
        try:
            prompt = f"""<role>
You are analyzing and expanding an ambiguous query for a multi-agent system.
</role>

<query>{query}</query>

<analysis_protocol>
1. AMBIGUITY DETECTION
   - Vague terms requiring clarification
   - Missing context or constraints
   - Multiple valid interpretations
   - Implicit assumptions

2. INTENT ANALYSIS
   - What is the user likely trying to achieve?
   - What outcomes would satisfy this query?

3. DECOMPOSITION
   - Break into concrete, actionable sub-questions
   - Each sub-question should be independently answerable
</analysis_protocol>

<output_format>
Return JSON:
{{
  "clarifications": ["What needs clarification?"],
  "intents": ["Possible intent 1", "Possible intent 2"],
  "assumptions": ["Implicit assumptions"],
  "sub_queries": ["Concrete sub-question 1", "Sub-question 2"],
  "complexity": 0.5
}}
</output_format>"""
            response = await self.llm_router.completion(
                model="auto",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            import json
            result = json.loads(response.choices[0].message.content)
            # Validate result has required fields
            if "sub_queries" not in result or not result["sub_queries"]:
                result["sub_queries"] = [query]
            return result
        except Exception as e:
            print(f"LLM expansion failed, using default: {e}")
            import traceback
            traceback.print_exc()
            return default_response

    def _suggest_agents(self, expansion: Dict[str, Any]) -> List[str]:
        """Suggest agent types based on expansion"""
        agents = []
        sub_queries = expansion.get("sub_queries", [])
        for sq in sub_queries:
            sq_lower = sq.lower()
            if any(word in sq_lower for word in ["research", "find", "search", "look up"]):
                agents.append("researcher")
            elif any(word in sq_lower for word in ["code", "program", "implement", "write"]):
                agents.append("coder")
            elif any(word in sq_lower for word in ["analyze", "plan", "strategy"]):
                agents.append("analyst")
            else:
                agents.append("analyst")  # Default
        return list(set(agents))  # Unique


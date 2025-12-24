"""Base agent framework"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel

from backend.models.task import Task
from backend.models.agent import AgentCapability
from backend.llm.router import SwarmOSRouter
from backend.memory.manager import MemoryManager
from backend.tools.registry import ToolRegistry


class AgentResult(BaseModel):
    """Agent execution result"""

    agent_id: str
    task_id: str
    content: str
    confidence: float = 0.5
    evidence: List[str] = []
    metadata: Dict[str, Any] = {}
    tokens_used: int = 0
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base agent class"""

    agent_type: str
    capabilities: List[AgentCapability] = []

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        provider: str = "auto",
        llm_router: Optional[SwarmOSRouter] = None,
        memory: Optional[MemoryManager] = None,
        tools: Optional[ToolRegistry] = None,
    ):
        self.id = agent_id or f"{self.agent_type}-{uuid4().hex[:8]}"
        self.name = name or self.agent_type.capitalize()
        self.provider = provider
        self.llm_router = llm_router
        self.memory = memory
        self.tools = tools
        self.current_load = 0.0
        self.status = "idle"

    @abstractmethod
    async def process(self, task: Task) -> AgentResult:
        """Process a task and return result"""
        pass

    async def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool"""
        if not self.tools:
            raise ValueError("Tool registry not available")
        return await self.tools.execute(tool_name, params)

    async def auto_web_search(self, query: str, max_results: int = 5) -> str:
        """
        Autonomous web search capability - agents can call this independently.
        Returns formatted search results as context.
        """
        if not self.tools:
            return ""
        
        try:
            results = await self.tools.execute("web_search", {
                "query": query,
                "max_results": max_results
            })
            
            if not results:
                return ""
            
            # Format results as context
            formatted = []
            for i, result in enumerate(results[:max_results], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", result.get("content", ""))[:500]
                url = result.get("url", "")
                formatted.append(f"[{i}] {title}\n{snippet}\nSource: {url}")
            
            return "\n\n".join(formatted)
        except Exception as e:
            print(f"Web search failed for {self.agent_type}: {e}")
            return ""

    async def generate_proposal(
        self,
        topic: str,
        previous_round: Optional[Dict] = None,
        critiques_received: Optional[List[Dict]] = None,
    ) -> AgentResult:
        """Generate a proposal for debate"""
        # Default implementation - can be overridden
        prompt = self._build_proposal_prompt(topic, previous_round, critiques_received)
        response = await self._llm_call(prompt)
        return AgentResult(
            agent_id=self.id,
            task_id="",  # Will be set by caller
            content=response,
            confidence=0.7,
        )

    async def critique_proposal(self, proposal: Dict, critique_prompt: str) -> Dict:
        """Critique another agent's proposal"""
        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology for critique.
Each claim is evaluated as an independent atomic unit.
Your critique targets specific atoms, not holistic impressions.
</aot_framework>

<role>
You are a critical evaluator in a multi-agent debate.
Goal: Improve proposal quality through atomic-level critique.
You assess each claim independently before synthesis.
</role>

<critique_context>
{critique_prompt}
</critique_context>

<proposal_to_critique>
{proposal.get('content', '')}
</proposal_to_critique>

<atomic_extraction_protocol>
PHASE 1: EXTRACT atomic claims from proposal

Parse the proposal into discrete, evaluable units:
```json
{{
    "claims": [
        {{"id": "C1", "statement": "exact claim text", "type": "factual|logical|evaluative"}},
        {{"id": "C2", "statement": "exact claim text", "type": "factual|logical|evaluative"}}
    ],
    "dependencies": [
        {{"claim": "C2", "depends_on": ["C1"], "relationship": "supports|contradicts|extends"}}
    ]
}}
```
</atomic_extraction_protocol>

<atomic_critique_protocol>
PHASE 2: CRITIQUE each atom independently

For each claim, evaluate IN ISOLATION:
```json
{{
    "claim_id": "C1",
    "claim_text": "...",
    "critique": {{
        "validity": "valid|flawed|unverifiable",
        "flaw_type": "logical_flaw|missing_evidence|oversimplification|false_premise|none",
        "counter_evidence": "specific counter-argument or evidence",
        "alternative_interpretation": "different way to view this specific claim",
        "strength_score": 1,
        "justification": "why this score"
    }}
}}
```

CRITICAL: Evaluate each claim as if you haven't seen the others. Do NOT let a strong claim bias evaluation of weak claims or vice versa.
</atomic_critique_protocol>

<dependency_analysis_protocol>
PHASE 3: ANALYZE dependency impacts

After independent evaluation, assess how flaws propagate:
```json
{{
    "propagation_analysis": [
        {{
            "source_flaw": "C1",
            "affected_claims": ["C2", "C3"],
            "impact": "If C1 is false, then C2 and C3 collapse because..."
        }}
    ]
}}
```
</dependency_analysis_protocol>

<output_schema>
Return valid JSON:
```json
{{
    "atomic_extractions": {{
        "claims": [],
        "dependencies": []
    }},
    "atomic_critiques": [
        {{
            "claim_id": "C1",
            "validity": "...",
            "flaw_type": "...",
            "counter_evidence": "...",
            "alternative_interpretation": "...",
            "strength_score": 7
        }}
    ],
    "propagation_analysis": [],
    "synthesis": {{
        "valid_points": ["C1 is well-supported because..."],
        "critical_flaws": ["C2 has fatal flaw: ..."],
        "aggregate_score": 6.5,
        "decision": "AGREE|DISAGREE|PARTIALLY_AGREE",
        "decision_rationale": "Based on atomic analysis, the proposal..."
    }}
}}
```
</output_schema>

<critique_constraints>
MUST DO:
- Target specific claims with specific counterarguments
- Cite evidence when challenging assertions
- Evaluate each atom before forming overall judgment
- Acknowledge valid points explicitly

MUST NOT:
- Dismiss arguments without atomic-level analysis
- Let overall impression bias individual claim evaluation
- Critique style over substance
- Reject without offering specific alternatives
</critique_constraints>
"""
        response = await self._llm_call(prompt)
        # Parse response (simplified - in production would use structured output)
        return {
            "strengths": [],
            "weaknesses": [],
            "score": 5.0,
            "reasoning": response,
        }

    async def vote(
        self, proposals: List[Dict], voting_criteria: str
    ) -> Dict[str, str]:
        """Vote for best proposal"""
        proposals_text = "\n\n".join(
            [
                f"Proposal {i+1} (Agent {p.get('agent_id', 'unknown')}):\n{p.get('content', '')}"
                for i, p in enumerate(proposals)
            ]
        )

        prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology for voting.
Each evaluation criterion is an independent atomic assessment.
Aggregate scores emerge from atomic evaluations, not gestalt impressions.
</aot_framework>

<role>
You are voting on the best solution in a multi-agent debate.
You must evaluate each proposal on each criterion independently.
Form atomic judgments first, then aggregate to final selection.
</role>

<voting_criteria>
{voting_criteria}
</voting_criteria>

<proposals>
{proposals_text}
</proposals>

<atomic_evaluation_protocol>
PHASE 1: DECOMPOSE evaluation into atomic assessments

For each proposal × criterion combination, evaluate independently:
```json
{{
    "proposal_id": 1,
    "criterion": "accuracy",
    "atomic_assessment": {{
        "score": 8,
        "evidence": "specific text from proposal supporting this score",
        "weakness": "specific limitation on this criterion"
    }}
}}
```

Evaluation criteria atoms:
- A_accuracy: Factual correctness (weight: 0.30)
- A_completeness: Addresses all aspects (weight: 0.25)
- A_reasoning: Logical coherence (weight: 0.25)
- A_practicality: Implementability (weight: 0.20)

CRITICAL: Score each criterion for each proposal BEFORE comparing proposals. Do NOT let strength on one criterion bias others.
</atomic_evaluation_protocol>

<atomic_scoring_matrix>
PHASE 2: BUILD scoring matrix

```json
{{
    "scoring_matrix": {{
        "proposal_1": {{
            "accuracy": {{"score": 8, "evidence": "..."}},
            "completeness": {{"score": 7, "evidence": "..."}},
            "reasoning": {{"score": 9, "evidence": "..."}},
            "practicality": {{"score": 6, "evidence": "..."}}
        }},
        "proposal_2": {{
            "accuracy": {{"score": 7, "evidence": "..."}},
            "completeness": {{"score": 8, "evidence": "..."}},
            "reasoning": {{"score": 7, "evidence": "..."}},
            "practicality": {{"score": 8, "evidence": "..."}}
        }}
    }}
}}
```
</atomic_scoring_matrix>

<aggregation_protocol>
PHASE 3: AGGREGATE using weighted contraction

Calculate weighted scores:
```json
{{
    "weighted_totals": {{
        "proposal_1": "0.30×8 + 0.25×7 + 0.25×9 + 0.20×6 = 7.6",
        "proposal_2": "0.30×7 + 0.25×8 + 0.25×7 + 0.20×8 = 7.45"
    }},
    "ranking": [1, 2]
}}
```
</aggregation_protocol>

<output_schema>
Return valid JSON and select exactly ONE proposal.
```json
{{
    "atomic_evaluations": [
        {{"proposal": 1, "criterion": "accuracy", "score": 8, "evidence": "..."}},
        {{"proposal": 1, "criterion": "completeness", "score": 7, "evidence": "..."}}
    ],
    "scoring_matrix": {{}},
    "weighted_totals": {{}},
    "selection": {{
        "selected_proposal": 1,
        "weighted_score": 7.6,
        "margin_over_second": 0.15,
        "confidence": "high|medium|low"
    }},
    "reasoning": {{
        "primary_differentiator": "...",
        "trade_offs": "...",
        "dissenting_consideration": "..."
    }}
}}
```

IMPORTANT: You must select exactly ONE proposal. Selection based on atomic aggregation, not impression.
</output_schema>
"""
        response = await self._llm_call(prompt)
        # Parse to get selected proposal ID
        selected_id = proposals[0].get("agent_id", "") if proposals else ""
        return {"selected_proposal_id": selected_id, "reasoning": response}

    async def _llm_call(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> str:
        """Make LLM call"""
        if not self.llm_router:
            raise ValueError("LLM router not available")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Map provider to model
        model = self._map_provider_to_model(self.provider)
        
        response = await self.llm_router.completion(
            model=model,
            messages=messages,
            **kwargs,
        )

        return response.choices[0].message.content

    def _build_proposal_prompt(
        self,
        topic: str,
        previous_round: Optional[Dict] = None,
        critiques_received: Optional[List[Dict]] = None,
    ) -> str:
        """Build proposal prompt using All-Agents Drafting (AAD) pattern"""
        previous_context = ""
        if previous_round:
            previous_context = f"""\n<previous_round>
{previous_round.get('content', '')}
</previous_round>"""
        
        critiques_context = ""
        if critiques_received:
            critiques_text = "\n".join([f"- {c.get('reasoning', '')}" for c in critiques_received])
            critiques_context = f"""\n<critiques_received>
{critiques_text}
</critiques_received>

<improvement_instruction>
Address the critiques above in your proposal.
</improvement_instruction>"""
        
        return f"""<role>
You are {self.agent_type.capitalize()} participating in a structured debate.
Generate your proposal INDEPENDENTLY, without reference to other agents' positions.
</role>

<topic>
{topic}
</topic>
{previous_context}
{critiques_context}
<proposal_structure>
1. POSITION: State your clear position on the question
2. REASONING: Step-by-step logic supporting your position
3. EVIDENCE: Specific facts, data, or examples supporting claims
4. ASSUMPTIONS: Key assumptions underlying your argument
5. CONFIDENCE: Your confidence level (high/medium/low) with justification
6. POTENTIAL_WEAKNESSES: Acknowledge limitations proactively
</proposal_structure>

<guidelines>
- Be specific and concrete
- Support claims with evidence
- Acknowledge uncertainty where appropriate
- Consider alternative viewpoints
</guidelines>"""

    def get_success_rate(self, task_type: str) -> float:
        """Get historical success rate for task type"""
        # Placeholder - would track in database
        return 0.8
    
    def _map_provider_to_model(self, provider: str) -> str:
        """Map provider name to actual LiteLLM model name"""
        if provider == "google":
            return "gemini/gemini-2.0-flash-exp"  # Use Gemini Flash 2.0 when Google is selected
        elif provider == "anthropic":
            return "claude-3-5-sonnet-20241022"
        elif provider == "openai":
            return "gpt-4o"
        elif provider == "openrouter":
            return "openrouter/gemini/gemini-2.0-flash-exp"
        elif provider == "gemini-flash":
            return "gemini/gemini-2.0-flash-exp"  # Map to actual model name
        elif provider == "claude-sonnet":
            return "claude-3-5-sonnet-20241022"
        elif provider == "gpt-4o":
            return "gpt-4o"
        elif provider == "auto":
            return "auto"  # Let router decide
        else:
            # If it already has a provider prefix, use it directly
            if "/" in provider:
                return provider
            return provider


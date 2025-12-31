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
        prompt = f"""<role>
You are a critical evaluator in a multi-agent debate.
Your goal: improve proposal quality through rigorous but constructive critique.
</role>

<critique_context>
{critique_prompt}
</critique_context>

<proposal_to_critique>
{proposal.get('content', '')}
</proposal_to_critique>

<critique_guidelines>
MUST DO:
- Target specific claims with specific counterarguments
- Cite evidence when challenging assertions
- Propose alternative interpretations
- Acknowledge valid points before critiquing

MUST NOT:
- Dismiss arguments without substantive counter-evidence
- Use ad hominem or emotional language
- Critique style over substance
- Completely reject without offering alternatives
</critique_guidelines>

<output_format>
1. VALID_POINTS: What is well-supported in this proposal?
2. CRITIQUES: Specific issues with weakness_type (logical_flaw/missing_evidence/oversimplification/false_premise)
3. COUNTER_EVIDENCE: Evidence supporting your critiques
4. ALTERNATIVE_INTERPRETATIONS: Different ways to view the topic
5. SCORE: 1-10 with justification
6. DECISION: AGREE / DISAGREE / PARTIALLY_AGREE
</output_format>"""
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

        prompt = f"""<role>
You are voting on the best solution in a multi-agent debate.
Form your judgment independently before providing reasoning.
</role>

<voting_criteria>
{voting_criteria}
</voting_criteria>

<proposals>
{proposals_text}
</proposals>

<voting_protocol>
1. Review each solution independently
2. Score each against these criteria:
   - Accuracy: Factual correctness
   - Completeness: Addresses all aspects
   - Reasoning: Logical coherence
   - Practicality: Implementability
3. Select the SINGLE best solution
4. Provide reasoning AFTER your selection

IMPORTANT: You must select exactly ONE proposal. Do not vote for multiple.
</voting_protocol>

<output_format>
1. SELECTED: Proposal number (1-{len(proposals)})
2. SCORES: Brief score for each proposal on the criteria
3. REASONING: Why the selected proposal is best
4. CONFIDENCE: Your confidence in this selection (high/medium/low)
</output_format>"""
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
        """Map provider name to actual LiteLLM model name using settings"""
        # Import here to avoid circular imports
        from backend.api.routes.settings import get_model_for_provider
        
        if provider == "auto":
            return "auto"  # Let router decide
        elif provider in ["google", "anthropic", "openai", "openrouter"]:
            return get_model_for_provider(provider)
        elif provider == "gemini-flash":
            return get_model_for_provider("google")
        elif provider == "claude-sonnet":
            return get_model_for_provider("anthropic")
        elif provider == "gpt-4o":
            return get_model_for_provider("openai")
        else:
            # If it already has a provider prefix, use it directly
            if "/" in provider:
                return provider
            return provider


"""Task delegator - plans agent creation and execution"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from backend.llm.router import SwarmOSRouter


class AgentPlan(BaseModel):
    """Plan for agent creation"""
    agent_type: str
    agent_name: str
    description: str  # What this agent type does
    subtask_description: str  # Specific subtask for this agent
    provider: str
    priority: int = 0
    capability: str = "analysis"  # Underlying capability: research, coding, analysis, review


class DelegationPlan(BaseModel):
    """Complete delegation plan"""
    task_description: str
    execution_strategy: str  # "single", "parallel", "sequential", "debate"
    agents_needed: List[AgentPlan]
    estimated_steps: int
    requires_debate: bool = False
    complexity_score: float = 0.5
    # Detailed orchestrator reasoning
    task_interpretation: str = ""  # What the orchestrator understood from the task
    main_tasks_identified: List[str] = []  # Key subtasks/goals identified
    research_approach: str = ""  # How research should be conducted
    reasoning: str = ""  # Overall reasoning for the delegation strategy


class Delegator:
    """Delegates tasks by planning agent creation and execution"""
    
    def __init__(self, llm_router: SwarmOSRouter):
        self.llm_router = llm_router
    
    async def create_delegation_plan(
        self, 
        task_description: str, 
        provider: str = "auto"
    ) -> DelegationPlan:
        """Create a plan for delegating the task to agents"""
        
        # Analyze task to determine agent needs
        analysis = await self._analyze_task(task_description, provider)
        
        # Create agent plans
        agents_needed = await self._plan_agents(task_description, analysis, provider)
        
        # Determine execution strategy
        execution_strategy = self._determine_strategy(agents_needed, analysis)
        
        return DelegationPlan(
            task_description=task_description,
            execution_strategy=execution_strategy,
            agents_needed=agents_needed,
            estimated_steps=len(agents_needed),
            requires_debate=analysis.get("requires_debate", False),
            complexity_score=analysis.get("complexity", 0.5),
            task_interpretation=analysis.get("task_interpretation", ""),
            main_tasks_identified=analysis.get("main_tasks", []),
            research_approach=analysis.get("research_approach", ""),
            reasoning=analysis.get("reasoning", ""),
        )
    
    async def _analyze_task(self, description: str, provider: str) -> Dict:
        """Analyze task to understand requirements"""
        try:
            prompt = f"""<role>
You are a task orchestrator for a multi-agent system. Analyze incoming requests 
and dynamically assign the most appropriate expert roles. You collaborate with 
other specialized agents who will execute the subtasks you define.
</role>

<task_analysis_instructions>
For the given task, perform comprehensive analysis:

1. TASK INTERPRETATION
   - What is the user actually asking for?
   - What is the desired outcome?
   - What context or constraints are implied?

2. SUBTASK IDENTIFICATION  
   - Break down into 4-6 main goals/subtasks
   - Identify dependencies between subtasks
   - Prioritize by importance

3. EXPERT PERSONA ASSIGNMENT
   - Identify at least 4 expert personas most qualified for this task
   - For each expert, define their specific domain expertise
   - Assign capability class: RESEARCH, ANALYSIS, CODING, or REVIEW
   - Example personas: "Systems Architect", "Security Auditor", "Data Scientist"

4. EXECUTION STRATEGY
   - Determine if debate/validation is needed (for controversial or high-stakes decisions)
   - Assess complexity score (0.0-1.0)
   - Define research approach if applicable
</task_analysis_instructions>

<capability_registry>
Available capability classes:
- RESEARCH: Web research, information gathering, source verification
- ANALYSIS: Data analysis, strategic planning, pattern recognition  
- CODING: Code generation, debugging, optimization
- REVIEW: Quality assessment, critique, validation
</capability_registry>

<input_task>
{description}
</input_task>

<output_format>
Return a JSON object with this exact structure:
{{
  "task_interpretation": "Clear statement of what user wants and expected outcome",
  "main_tasks": ["Subtask 1", "Subtask 2", "Subtask 3"],
  "research_approach": "How research should be conducted (if applicable)",
  "work_types": ["research", "analysis", "coding"],
  "agent_count": 4,
  "agent_config": [
    {{"role": "Expert Role Name", "capability": "RESEARCH|ANALYSIS|CODING|REVIEW", "expertise": "Specific domain knowledge"}}
  ],
  "requires_debate": false,
  "complexity": 0.6,
  "reasoning": "Detailed explanation of why this delegation strategy is optimal"
}}
</output_format>

<constraints>
- Agent count must be 4 to 15 (use as many as needed for quality)
- Each agent must have a distinct, valuable perspective
- All agents have access to web_search capability
- Prioritize outcome quality over efficiency
- Only recommend debate for controversial or high-stakes decisions
</constraints>"""
            
            # Map provider to actual model name
            model_name = "gemini/gemini-2.0-flash-exp"  # Default
            if provider == "google":
                model_name = "gemini/gemini-2.0-flash-exp"
            elif provider == "auto":
                model_name = "auto"  # Let router decide
            
            response = await self.llm_router.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Task analysis failed: {e}")
            # Fallback to simple analysis
            return {
                "task_interpretation": description,
                "main_tasks": [description],
                "research_approach": "Standard research and analysis",
                "work_types": ["analysis"],
                "agent_count": 4,
                "agent_types": ["analyst"],
                "requires_debate": False,
                "complexity": 0.5,
                "reasoning": "Single agent for straightforward task"
            }
    
    async def _plan_agents(
        self, 
        description: str,
        analysis: Dict,
        provider: str
    ) -> List[AgentPlan]:
        """Plan which agents are needed"""
        
        # Check for dynamic agent configuration
        agent_config = analysis.get("agent_config", [])
        
        # If we have dynamic config, use it
        if agent_config and isinstance(agent_config, list):
            plans = []
            agent_types_for_decomposition = []
            
            for i, config in enumerate(agent_config):
                role = config.get("role", f"Agent-{i+1}")
                capability = config.get("capability", "ANALYSIS").lower()
                
                # Standardize capability
                if "research" in capability: capability = "research"
                elif "code" in capability or "coding" in capability: capability = "coding"
                elif "review" in capability: capability = "review"
                else: capability = "analysis"
                
                agent_types_for_decomposition.append(role)
                
                # IMPORTANT: If a specific provider is selected (not "auto"), ALL agents use that provider
                agent_provider = provider
                if provider == "auto":
                    agent_provider = self._select_provider_for_agent(role, i)
                
                plans.append(AgentPlan(
                    agent_type=role,  # Dynamic role name
                    agent_name=role,
                    description=f"Acts as {role} with {capability} capabilities",
                    subtask_description="", # Will be filled after decomposition
                    provider=agent_provider,
                    priority=i,
                    capability=capability
                ))
            # Ensure at least 4 agents by padding with standard roles
            min_agents = 4
            if len(plans) < min_agents:
                defaults = ["researcher", "analyst", "coder", "reviewer", "synthesizer"]
                capability_defaults = {
                    "researcher": "research",
                    "analyst": "analysis",
                    "coder": "coding",
                    "reviewer": "review",
                    "synthesizer": "analysis",
                }
                j = len(plans)
                for default in defaults:
                    if len(plans) >= min_agents:
                        break
                    agent_types_for_decomposition.append(default)
                    agent_provider = provider if provider != "auto" else self._select_provider_for_agent(default, j)
                    plans.append(AgentPlan(
                        agent_type=default,
                        agent_name=default.capitalize(),
                        description=f"Handles {default} duties",
                        subtask_description="",
                        provider=agent_provider,
                        priority=j,
                        capability=capability_defaults.get(default, "analysis")
                    ))
                    j += 1
            
            # Decompose task for these specific roles
            subtasks = await self._decompose_task(description, agent_types_for_decomposition, provider, analysis)
            
            # Assign subtasks back to plans
            for i, plan in enumerate(plans):
                plan.subtask_description = subtasks[i] if i < len(subtasks) else description
                
            return plans

        # ---------------------------------------------------------
        # FALLBACK: Legacy logic for standard types (or if config missing)
        # ---------------------------------------------------------
        
        # Use analysis results to determine agent count and types
        agent_count = analysis.get("agent_count", 4)
        agent_count = max(4, min(agent_count, 15))  # Enforce 4-15 agents
        
        agent_types = analysis.get("agent_types", [])
        
        # Default behavior if analysis fails
        if not agent_types:
            agent_types = ["researcher", "analyst"]
            if agent_count > 2:
                agent_types.extend(["reviewer", "synthesizer"][:agent_count-2])
        
        # Ensure we have enough types for the count
        while len(agent_types) < agent_count:
            # Add sensible defaults based on typical workflow
            defaults = ["researcher", "analyst", "coder", "reviewer", "synthesizer"]
            for default in defaults:
                if default not in agent_types:
                    agent_types.append(default)
                    break
            else:
                agent_types.append("researcher") # Fallback
        
        # Truncate if we have too many
        agent_types = agent_types[:agent_count]
        
        agent_info = {
            "researcher": {
                "name": "Researcher",
                "description": "Conducts web research and information gathering using search tools",
                "capability": "research"
            },
            "analyst": {
                "name": "Analyst",
                "description": "Analyzes data and creates plans",
                "capability": "analysis"
            },
            "coder": {
                "name": "Coder",
                "description": "Generates and reviews code",
                "capability": "coding"
            },
            "reviewer": {
                "name": "Reviewer",
                "description": "Reviews and critiques solutions",
                "capability": "review"
            },
            "synthesizer": {
                "name": "Synthesizer",
                "description": "Synthesizes multiple perspectives into final output",
                "capability": "analysis"
            },
        }
        
        # Decompose the task into specific subtasks for each agent
        subtasks = await self._decompose_task(description, agent_types, provider, analysis)
        
        plans = []
        for i, agent_type in enumerate(agent_types[:agent_count]):
            info = agent_info.get(agent_type, {
                "name": agent_type.capitalize(),
                "description": f"Handles {agent_type} tasks",
                "capability": "analysis"
            })
            
            # IMPORTANT: If a specific provider is selected (not "auto"), ALL agents use that provider
            agent_provider = provider  # Always use the selected provider
            if provider == "auto":
                # Only distribute across providers if "auto" is selected
                agent_provider = self._select_provider_for_agent(agent_type, i)
            
            # Get the specific subtask for this agent
            subtask = subtasks[i] if i < len(subtasks) else description
            
            plans.append(AgentPlan(
                agent_type=agent_type,
                agent_name=info["name"],
                description=info["description"],
                subtask_description=subtask,
                provider=agent_provider,  # All agents use the same provider when specified
                priority=i,
                capability=info.get("capability", "analysis")
            ))
        
        return plans
    
    async def _decompose_task(
        self,
        description: str,
        agent_types: List[str],
        provider: str,
        analysis: Dict = None  # Added analysis parameter
    ) -> List[str]:
        """Decompose the main task into specific subtasks for each agent"""
        if len(agent_types) == 1:
            # Single agent gets the full task (or interpretation if available)
            if analysis and analysis.get("task_interpretation"):
                return [f"Execute task based on this interpretation: {analysis.get('task_interpretation')}. Original Request: {description}"]
            return [description]
        
        try:
            agent_roles = ", ".join(agent_types)
            agent_list = "\n".join([f"- {i+1}. {agent}" for i, agent in enumerate(agent_types)])
            
            prompt = f"""<role>
You are a task orchestrator decomposing work for a multi-agent team. Each agent 
will work collaboratively, building upon others' contributions toward the final answer.
</role>

<context>
Original Task: {description}

Task Interpretation: {analysis.get('task_interpretation', 'N/A') if analysis else 'N/A'}

Main Goals Identified:
{chr(10).join(['- ' + t for t in analysis.get('main_tasks', [])]) if analysis else 'N/A'}
</context>

<available_agents>
{agent_list}
</available_agents>

<instructions>
Create a specific, actionable subtask for EACH agent listed above.

SUBTASK REQUIREMENTS:
1. Each subtask must be distinct and complementary to others
2. Use direct instructions: "Your goal is to..." or "Analyze..." or "Research..."
3. Reference the agent's expertise in the instruction
4. Include specific deliverables expected
5. Note any dependencies on other agents' work

COLLABORATION PROTOCOL:
- Agents work in sequence, each building on previous work
- If an agent cannot fully complete their subtask, the next agent continues
- Include context about what previous agents will provide
</instructions>

<output_format>
Return JSON with exactly {len(agent_types)} subtasks:
{{
  "subtasks": [
    "Subtask for {agent_types[0]}: [specific instruction with deliverables]",
    {'"Subtask for ' + agent_types[1] + ': [specific instruction]"' if len(agent_types) > 1 else ''}
  ]
}}
</output_format>

<constraints>
- DO NOT repeat the original task verbatim
- Each subtask must add unique value
- Be specific about expected outputs
- Subtasks should be achievable independently but enhance each other
</constraints>"""
            
            
            model_name = self.llm_router.get_model_for_provider(provider if provider != "auto" else "google")
            response = await self.llm_router.llm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            import json
            content = response.choices[0].message.content
            # Strip markdown code blocks if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            subtasks = result.get("subtasks", [])
            
            # Ensure we have enough subtasks
            while len(subtasks) < len(agent_types):
                subtasks.append(f"Execute specific role duties for: {description[:100]}...")
            
            return subtasks[:len(agent_types)]
        except Exception as e:
            print(f"Task decomposition failed: {e}")
            
            # Fallback: Use analysis to create better instructions than just the main task
            if analysis:
                interpretation = analysis.get("task_interpretation", description)
                main_tasks = analysis.get("main_tasks", [])
                
                # If we have specific main tasks identified, try to distribute them
                if len(main_tasks) >= len(agent_types):
                    return [f"Focus on this aspect: {task}. Context: {interpretation}" for task in main_tasks[:len(agent_types)]]
                
                # General fallback using interpretation
                return [f"Role: {agent_type.capitalize()}. Objective: Using your expertise, address: {interpretation}" for agent_type in agent_types]
            
            # Absolute fallback
            return [f"Role: {agent_type.capitalize()}. Execute your specific duties to address: {description}" for agent_type in agent_types]
    
    def _select_provider_for_agent(self, agent_type: str, index: int) -> str:
        """Select provider for agent in auto mode (distribute across providers)"""
        # Simple round-robin distribution across different providers
        # Use actual provider names, not model names
        providers = ["google", "anthropic", "openai"]
        return providers[index % len(providers)]
    
    def _determine_strategy(self, agents: List[AgentPlan], analysis: Dict) -> str:
        """Determine execution strategy"""
        if len(agents) == 1:
            return "single"
        elif analysis.get("requires_debate", False):
            return "debate"
        else:
            # For complex tasks with multiple agents, use sequential to allow coordination
            # This ensures agents can build on each other's work
            # The synthesizer will combine everything at the end
            return "sequential"

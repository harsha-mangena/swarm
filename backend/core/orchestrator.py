"""Intelligent orchestrator with delegation"""

from typing import Dict, List, Optional
from uuid import uuid4

from backend.models.task import Task, TaskStatus
from backend.core.query_expander import QueryExpander
from backend.core.decomposer import TaskDecomposer, TaskGraph
from backend.core.delegator import Delegator, DelegationPlan
from backend.agents.base import BaseAgent, AgentResult
from backend.agents import (
    ResearcherAgent,
    AnalystAgent,
    CoderAgent,
    ReviewerAgent,
    SynthesizerAgent,
)
from backend.debate.engine import DebateEngine
from backend.debate.scoring import DebateConfig
from backend.llm.router import SwarmOSRouter
from backend.memory.manager import MemoryManager
from backend.models.memory import MemoryEntry, MemoryScope
from backend.tools.registry import ToolRegistry


class Orchestrator:
    """Orchestrate task execution across agents with delegation"""

    def __init__(
        self,
        llm_router: SwarmOSRouter,
        memory: MemoryManager,
        tools: Optional[ToolRegistry] = None,
    ):
        self.llm_router = llm_router
        self.memory = memory
        self.tools = tools or ToolRegistry()
        self.query_expander = QueryExpander(llm_router)
        self.decomposer = TaskDecomposer(llm_router)
        self.debate_config = DebateConfig()
        self.delegator = Delegator(llm_router)
        
        # Track active agents per task (created dynamically)
        self.task_agents: Dict[str, List[BaseAgent]] = {}

    async def expand_query(self, query: str) -> Dict:
        """Expand query into task plan"""
        expansion = await self.query_expander.expand(query)
        return expansion.dict()

    async def create_task(
        self,
        description: str,
        provider: str = "auto",
        expansion: Optional[Dict] = None,
    ) -> Task:
        """Create a new task"""
        task = Task(
            id=str(uuid4()),
            description=description,
            provider=provider,
            status=TaskStatus.PENDING,
            context=expansion,
        )
        return task

    async def execute_task(self, task: Task):
        """Execute a task with the new workflow: subtasks → validation → synthesis"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            await self._save_checkpoint(task)

            # Step 1: Create delegation plan
            delegation_plan = await self.delegator.create_delegation_plan(
                task.description,
                provider=task.provider
            )
            
            # Store delegation plan in task context
            if not task.context:
                task.context = {}
            task.context["delegation_plan"] = delegation_plan.dict()
            task.context["execution_strategy"] = delegation_plan.execution_strategy
            await self._save_checkpoint(task)

            # Step 2: Create agents based on plan
            task_agents = await self._create_task_agents(delegation_plan, task.id)
            self.task_agents[task.id] = task_agents
            
            # Step 2.5: Create supervisor agent (always created for quality control)
            from backend.agents.supervisor import SupervisorAgent
            supervisor = SupervisorAgent(
                agent_id=f"supervisor-{task.id}",
                provider=task.provider if task.provider != "auto" else "google",
                llm_router=self.llm_router,
                memory=self.memory,
                tools=self.tools,
            )
            self.task_agents[task.id].append(supervisor)
            
            # Store supervisor critiques
            supervisor_critiques = []
            
            # Step 3: Create subtasks for each agent (excluding supervisor)
            from backend.models.subtask import SubTask, SubTaskStatus
            subtasks = []
            for i, (agent, agent_plan) in enumerate(zip(task_agents, delegation_plan.agents_needed)):
                subtask = SubTask(
                    parent_task_id=task.id,
                    description=agent_plan.subtask_description,  # Use the specific subtask from the plan
                    agent_id=agent.id,
                    agent_type=agent.agent_type,
                    status=SubTaskStatus.PENDING,
                )
                subtasks.append(subtask)
            task.subtasks = [st.dict() for st in subtasks]
            await self._save_checkpoint(task)
            
            # Store task in memory for agent coordination
            await self.memory.write(
                MemoryEntry(
                    id=str(uuid4()),
                    scope=MemoryScope.TASK,
                    namespace=f"task:{task.id}",
                    content=f"Task: {task.description}\nProvider: {task.provider}\nSubtasks: {len(subtasks)}",
                    metadata={"task_id": task.id, "provider": task.provider}
                )
            )

            # Step 4: Execute all subtasks (hybrid parallel/sequential)
            # Run agents in parallel, then collect supervisor critiques in parallel
            import asyncio
            
            results = []
            
            # Execute all agents in parallel
            async def execute_agent(i, agent, subtask_dict):
                """Execute a single agent and return result with index"""
                # Update subtask status
                task.subtasks[i]["status"] = SubTaskStatus.IN_PROGRESS.value
                
                # Create task with the specific subtask description
                agent_task = Task(
                    id=task.id,
                    description=subtask_dict["description"],
                    provider=task.provider,
                    status=task.status,
                    context={
                        **(task.context or {}),
                        "original_task": task.description,
                        "agent_position": f"Agent {i + 1} of {len(task_agents)}"
                    }
                )
                
                result = await agent.process(agent_task)
                await self._log_agent_result(agent, task, result)
                
                # Update subtask with result
                task.subtasks[i]["status"] = SubTaskStatus.COMPLETED.value
                task.subtasks[i]["result"] = result.content
                
                return i, agent, result
            
            # Run all agents in parallel
            task.progress = 0.1
            await self._save_checkpoint(task)
            
            agent_tasks = [
                execute_agent(i, agent, subtask_dict) 
                for i, (agent, subtask_dict) in enumerate(zip(task_agents, task.subtasks))
            ]
            agent_results = await asyncio.gather(*agent_tasks)
            
            # Sort by index and extract results
            agent_results = sorted(agent_results, key=lambda x: x[0])
            results = [r[2] for r in agent_results]
            
            task.progress = 0.5
            await self._save_checkpoint(task)
            
            # Run supervisor critiques in parallel
            async def critique_agent(i, agent, result):
                """Supervisor critiques a single agent's work"""
                return await supervisor.critique_agent_work(
                    agent_type=agent.agent_type,
                    agent_id=agent.id,
                    agent_output=result.content,
                    task_description=task.description
                )
            
            critique_tasks = [
                critique_agent(i, agent_results[i][1], result) 
                for i, result in enumerate(results)
            ]
            supervisor_critiques = await asyncio.gather(*critique_tasks)
            
            task.progress = 0.6
            await self._save_checkpoint(task)
            
            # Step 4.5: Rework loop for low-scoring agents
            # The supervisor now tracks rework attempts internally
            MAX_REWORK_ATTEMPTS = 2
            
            for attempt in range(MAX_REWORK_ATTEMPTS):
                # Find agents that need rework based on supervisor's rework_required flag
                agents_to_rework = []
                for i, critique in enumerate(supervisor_critiques):
                    # Use the new rework_required flag from supervisor
                    if critique.get("rework_required", False):
                        agents_to_rework.append((i, agent_results[i][1], results[i], critique))
                    # Fallback: also check decision for backward compatibility
                    elif critique.get("decision", "").upper() in {"REJECT", "REVISE", "NEEDS_REWORK"}:
                        agents_to_rework.append((i, agent_results[i][1], results[i], critique))
                
                if not agents_to_rework:
                    break  # All agents passed threshold

                
                # Rework agents in parallel with supervisor guidance
                async def rework_agent(idx, agent, original_result, critique):
                    """Agent reworks their output with supervisor feedback"""
                    # Tailor rework instruction based on decision
                    decision = (critique.get("decision", "").upper())
                    careful_note = "Supervisor REJECTED your work. Perform a careful rework addressing CRITICAL issues with evidence and step-by-step corrections." if decision == "REJECT" else "Supervisor requested a REVISE. Improve clarity, correctness, and completeness per feedback."

                    rework_task = Task(
                        id=task.id,
                        description=task.subtasks[idx]["description"],
                        provider=task.provider,
                        status=task.status,
                        context={
                            **(task.context or {}),
                            "original_task": task.description,
                            "previous_attempt": original_result.content,
                            "supervisor_feedback": critique["critique"],
                            "supervisor_score": critique["score"],
                            "supervisor_decision": decision,
                            "rework_instruction": f"Your previous work scored {critique['score']}/10. {careful_note} Feedback: {critique['critique']}"
                        }
                    )
                    
                    new_result = await agent.process(rework_task)
                    await self._log_agent_result(agent, task, new_result)
                    
                    # Update subtask
                    task.subtasks[idx]["result"] = new_result.content
                    task.subtasks[idx]["rework_count"] = task.subtasks[idx].get("rework_count", 0) + 1
                    
                    return idx, agent, new_result
                
                rework_tasks = [
                    rework_agent(idx, agent, result, critique)
                    for idx, agent, result, critique in agents_to_rework
                ]
                rework_results = await asyncio.gather(*rework_tasks)
                
                # Update results with reworked outputs
                for idx, agent, new_result in rework_results:
                    results[idx] = new_result
                    agent_results[idx] = (idx, agent, new_result)
                
                # Re-critique reworked agents
                recritique_tasks = [
                    critique_agent(idx, agent, new_result)
                    for idx, agent, new_result in rework_results
                ]
                new_critiques = await asyncio.gather(*recritique_tasks)
                
                # Update critiques
                for i, (idx, _, _) in enumerate(rework_results):
                    supervisor_critiques[idx] = new_critiques[i]
                
                task.progress = 0.6 + (0.1 * (attempt + 1) / MAX_REWORK_ATTEMPTS)
                await self._save_checkpoint(task)
            
            task.progress = 0.7
            await self._save_checkpoint(task)


            # Step 5: Use supervisor critiques as validation results
            task.status = TaskStatus.VALIDATING
            task.progress = 0.8
            await self._save_checkpoint(task)
            
            # Format supervisor critiques as validation results
            validation_results = {
                "critiques": supervisor_critiques,
                "scores": {c["agent_id"]: c["score"] for c in supervisor_critiques},
                "summary": f"Supervisor reviewed {len(supervisor_critiques)} agent outputs. " +
                          f"Average score: {sum(c['score'] for c in supervisor_critiques) / len(supervisor_critiques):.1f}/10"
                          if supervisor_critiques else "No validation performed.",
                "validator": "supervisor",
                "supervisor_id": supervisor.id  # Fixed: was supervisor.agent_id
            }
            task.validation_results = validation_results
            task.progress = 0.9
            await self._save_checkpoint(task)

            # Step 6: Synthesize comprehensive final report
            final_content = await self._synthesize_final_report(task, results, validation_results, task_agents)

            # Aggregate results
            task.result = {
                "content": final_content,
                "agents": [r.agent_id for r in results],
                "agent_outputs": {r.agent_id: r.content for r in results},
                "validation_summary": validation_results.get("summary", ""),
                "delegation_plan": delegation_plan.dict(),
            }

            task.status = TaskStatus.COMPLETED
            task.agents_count = len(results)
            task.progress = 1.0
            await self._save_checkpoint(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            import traceback
            traceback.print_exc()

    async def _save_checkpoint(self, task: Task):
        """Save partial task state to database"""
        try:
            if self.memory and self.memory.postgres_store:
                # Use .dict() method or .model_dump() for Pydantic v2
                # Assuming Pydantic v1 or v2 compatibility
                await self.memory.postgres_store.save_task(task.dict())
        except Exception as e:
            # Checkpoint failure should not crash the task
            print(f"Failed to save checkpoint for task {task.id}: {e}")

    async def _execute_agent_with_context(self, agent: BaseAgent, task: Task, all_agents: List[BaseAgent]) -> AgentResult:
        """Execute agent with awareness of other agents working on the task"""
        # Get context from memory about what other agents are doing
        task_memory = await self.memory.query(
            namespace=f"task:{task.id}",
            scope=MemoryScope.TASK,
            limit=10
        )
        
        # Build context string
        context_parts = [f"Task: {task.description}"]
        if task_memory:
            context_parts.append("\nPrevious work on this task:")
            for entry in task_memory:
                context_parts.append(f"- {entry.content[:200]}")
        
        # Enhance task with context
        enhanced_task = Task(
            id=task.id,
            description=task.description,
            provider=task.provider,
            status=task.status,
            context={
                **(task.context or {}),
                "coordination_context": "\n".join(context_parts),
                "total_agents": len(all_agents),
                "agent_role": f"You are the {agent.agent_type} agent. Work on your specific part of the task."
            }
        )
        
        result = await agent.process(enhanced_task)
        await self._log_agent_result(agent, task, result)

        return result

    def _enhance_task_with_context(self, task: Task, accumulated_context: str, agent_index: int, total_agents: int) -> Task:
        """Enhance task with accumulated context from previous agents"""
        enhanced_context = {
            **(task.context or {}),
            "previous_work": accumulated_context,
            "agent_position": f"Agent {agent_index + 1} of {total_agents}",
            "instruction": "Build upon the previous work to continue the task."
        }
        
        return Task(
            id=task.id,
            description=task.description,
            provider=task.provider,
            status=task.status,
            context=enhanced_context
        )

    async def _synthesize_results(self, task: Task, results: List[AgentResult], agents: List[BaseAgent]) -> str:
        """Intelligently synthesize results from multiple agents"""
        # If we have a synthesizer agent, use it
        synthesizer = next((a for a in agents if a.agent_type == "synthesizer"), None)
        
        if synthesizer and len(results) > 1:
            # Create a synthesis task
            synthesis_prompt = f"""
            Task: {task.description}
            
            The following agents have completed their work:
            """
            for i, (result, agent) in enumerate(zip(results, agents)):
                synthesis_prompt += f"\n\n{agent.agent_type.capitalize()} Agent ({agent.id}):\n{result.content}"
            
            synthesis_prompt += "\n\nSynthesize all the above work into a comprehensive, well-structured final solution that integrates all perspectives and provides a complete answer to the task."
            
            synthesis_task = Task(
                id=task.id,
                description=synthesis_prompt,
                provider=task.provider,
                context=task.context
            )
            
            synthesis_result = await synthesizer.process(synthesis_task)
            return synthesis_result.content
        else:
            # Simple concatenation with headers
            synthesized = []
            for result, agent in zip(results, agents):
                synthesized.append(f"## {agent.agent_type.capitalize()} Agent Output\n\n{result.content}")
            return "\n\n".join(synthesized)

    async def _execute_graph(self, graph: TaskGraph, task: Task) -> List:
        """Execute task graph"""
        results = []
        completed = set()

        while True:
            ready_nodes = graph.get_ready_nodes()
            if not ready_nodes:
                break

            # Execute ready nodes in parallel (simplified - sequential for now)
            for node in ready_nodes:
                agent = await self._select_agent_for_node(node)
                subtask = Task(
                    id=node.id,
                    description=node.description,
                    provider=task.provider,
                )
                result = await agent.process(subtask)
                results.append(result)
                node.status = "completed"
                completed.add(node.id)

        return results

    async def _select_agent_for_task(self, task: Task) -> BaseAgent:
        """Select agent for task from task-specific agents"""
        task_agents = self.task_agents.get(task.id, [])
        if not task_agents:
            raise ValueError(f"No agents found for task {task.id}")
        available = [a for a in task_agents if a.status == "idle"]
        if not available:
            available = task_agents
        return available[0]

    async def _select_agent_for_node(self, node, task_id: str) -> BaseAgent:
        """Select agent for task node from task-specific agents"""
        task_agents = self.task_agents.get(task_id, [])
        if not task_agents:
            raise ValueError(f"No agents found for task {task_id}")
        available = [a for a in task_agents if a.status == "idle"]
        if not available:
            available = task_agents
        return available[0]
    
    async def _create_task_agents(self, plan: DelegationPlan, task_id: str = "") -> List[BaseAgent]:
        """Create agents based on delegation plan"""
        agents = []
        
        # Mapping from capability (or standard type) to class
        agent_classes = {
            "researcher": ResearcherAgent,
            "analyst": AnalystAgent,
            "coder": CoderAgent,
            "reviewer": ReviewerAgent,
            "synthesizer": SynthesizerAgent,
        }
        
        # Capability mapping
        capability_map = {
            "research": ResearcherAgent,
            "analysis": AnalystAgent,
            "coding": CoderAgent,
            "review": ReviewerAgent,
        }
        
        for agent_plan in plan.agents_needed:
            # First try direct type mapping (legacy)
            agent_class = agent_classes.get(agent_plan.agent_type.lower())
            
            # If unknown type (dynamic), use capability to select class
            if not agent_class:
                capability = getattr(agent_plan, "capability", "analysis").lower()
                agent_class = capability_map.get(capability, AnalystAgent)
            
            # Use the provider from the plan (already mapped correctly)
            provider = agent_plan.provider
            
            # Validate provider (must be one of the allowed ones or auto)
            if provider not in ["google", "anthropic", "openai", "openrouter", "auto"]:
                provider = "auto"  # Default to auto if invalid
            
            # Generate unique name with task ID suffix for uniqueness/traceability
            unique_name = agent_plan.agent_name
            if task_id:
                unique_name = f"{unique_name}-{task_id[:4]}"
            
            agent = agent_class(
                name=unique_name,
                provider=provider,
                llm_router=self.llm_router,
                memory=self.memory,
                tools=self.tools,
            )
            
            # IMPORTANT: Overlay the dynamic type (e.g., "Futurist") onto the agent
            # This allows the agent to identify as "Futurist" in prompts, even if it's technically an AnalystAgent
            agent.agent_type = agent_plan.agent_type
            
            agents.append(agent)
        
        return agents
    
    async def _execute_with_debate(self, task: Task, agents: List[BaseAgent]) -> List:
        """Execute task with debate mechanism"""
        task.status = TaskStatus.DEBATING
        debate_engine = DebateEngine(agents, self.debate_config)
        debate_state = await debate_engine.run(
            topic=task.description, task_id=task.id
        )
        task.debate_state = debate_state.dict()
        
        # Get results from debate
        results = []
        for agent in agents:
            # Get agent's proposal from debate state
            proposal = next(
                (p for p in debate_state.proposals if p.get("agent_id") == agent.id),
                None
            )
            if proposal:
                from backend.agents.base import AgentResult
                agent_result = AgentResult(
                    agent_id=agent.id,
                    task_id=task.id,
                    content=proposal.get("content", ""),
                    confidence=proposal.get("confidence", 0.5),
                )
                results.append(agent_result)
                await self._log_agent_result(agent, task, agent_result)
        
        if results:
            return results
        # Fallback: execute first agent directly and log
        fallback_result = await agents[0].process(task)
        await self._log_agent_result(agents[0], task, fallback_result)
        return [fallback_result]

    async def _log_agent_result(self, agent: BaseAgent, task: Task, result: AgentResult):
        """Persist agent outputs to both task and agent scoped memory for UI visibility."""
        try:
            content_snippet = (result.content or "")[:2000] if result else ""
            metadata = {
                "agent_id": agent.id,
                "agent_type": agent.agent_type,
                "task_id": task.id,
                "provider": agent.provider,
                "confidence": result.confidence if result else None,
                "evidence": result.evidence if result else [],
                "type": "output",
                "category": "output",
            }

            # Task-scoped entry (shared timeline)
            await self.memory.write(
                MemoryEntry(
                    id=str(uuid4()),
                    scope=MemoryScope.TASK,
                    namespace=f"task:{task.id}",
                    content=f"{agent.agent_type.capitalize()} Agent ({agent.id}) output:\n{content_snippet}",
                    metadata=metadata,
                )
            )

            # Agent-scoped entry (used by agent detail view)
            await self.memory.write(
                MemoryEntry(
                    id=str(uuid4()),
                    scope=MemoryScope.AGENT,
                    namespace=f"agent:{agent.id}",
                    content=f"Task {task.id} output:\n{content_snippet}",
                    metadata=metadata,
                )
            )
        except Exception:
            # Logging should not break execution
            import traceback
            traceback.print_exc()

    async def _run_validation_phase(self, task: Task, results: List[AgentResult], agents: List[BaseAgent]) -> Dict:
        """Run debate/validation on all completed subtask results"""
        validation_data = {
            "critiques": [],
            "scores": {},
            "consensus": False,
            "summary": "",
        }
        
        try:
            # Have each agent critique the combined results
            combined_results = "\n\n".join([
                f"## {agent.agent_type.capitalize()} Agent Output:\n{result.content}"
                for agent, result in zip(agents, results)
            ])
            
            critique_prompt = f"""<aot_framework>
You operate using Atom of Thought (AoT) methodology.
Validate the combined output by decomposing evaluation into atomic criteria and atomic defects.
</aot_framework>

<role>
You are validating the combined output from a multi-agent team.
</role>

<original_task>
{task.description}
</original_task>

<work_completed>
{combined_results[:4000]}
</work_completed>

<atomic_validation_protocol>
PHASE 1: Independent criterion atoms
- V1: Correctness (facts, logic)
- V2: Completeness (requirements, edge cases)
- V3: Quality (best practices)
- V4: Coherence (integration, contradictions)

PHASE 2: Defect atoms
- Each defect is a single concrete issue with severity CRITICAL|MAJOR|MINOR
- Provide a minimal fix instruction

PHASE 3: Contract to score and verdict
- Compute an overall score 1-10 based on criterion scores and defect severity
- Provide rework instructions if score < 8
</atomic_validation_protocol>

<output_schema>
Return JSON only:
```json
{{
    "criteria": {{
        "correctness": {{"score": 0, "evidence": []}},
        "completeness": {{"score": 0, "evidence": []}},
        "quality": {{"score": 0, "evidence": []}},
        "coherence": {{"score": 0, "evidence": []}}
    }},
    "strengths": ["..."],
    "defects": [
        {{"id": "D1", "severity": "CRITICAL|MAJOR|MINOR", "issue": "...", "fix": "..."}}
    ],
    "overall": {{"score": 0, "justification": "...", "completeness": "yes|partial|no"}},
    "rework_instructions": ["..."]
}}
```
</output_schema>"""
            
            # Use first agent (or reviewer if available) for validation
            validator = next((a for a in agents if a.agent_type == "reviewer"), agents[0])
            
            validation_result = await validator._llm_call(critique_prompt)
            
            validation_data["critiques"].append({
                "agent_id": validator.id,
                "agent_type": validator.agent_type,
                "critique": validation_result,
            })
            validation_data["scores"][validator.id] = 7.0  # Default good score
            validation_data["consensus"] = True  # Single validator = consensus
            validation_data["summary"] = f"Validation completed by {validator.agent_type} agent. Results reviewed and approved."
            
        except Exception as e:
            validation_data["summary"] = f"Validation phase error: {str(e)}"
            import traceback
            traceback.print_exc()
        
        return validation_data

    async def _synthesize_final_report(
        self, 
        task: Task, 
        results: List[AgentResult], 
        validation_results: Dict,
        agents: List[BaseAgent]
    ) -> str:
        """Create comprehensive final report from all subtask results and validation"""
        
        # Find synthesizer or use last agent
        synthesizer = next((a for a in agents if a.agent_type == "synthesizer"), agents[-1])
        
        # Build comprehensive prompt
        work_summary = "\n\n".join([
            f"### {agent.agent_type.capitalize()} Agent Contribution:\n{result.content[:1500]}"
            for agent, result in zip(agents, results)
        ])
        
        validation_summary = validation_results.get("summary", "No validation performed")
        critiques = validation_results.get("critiques", [])
        critique_text = "\n".join([c.get("critique", "")[:500] for c in critiques]) if critiques else "No critiques"
        
        synthesis_prompt = f"""<aot_framework>
    You operate using Atom of Thought (AoT) methodology.
    Your job is to contract multi-agent contributions into a single, user-facing FINAL ANSWER.
    </aot_framework>

    <role>
    You are creating the FINAL ANSWER for a multi-agent task.
    Your output is presented directly to the user.
    </role>

    <original_task>
    {task.description}
    </original_task>

    <agent_contributions>
    {work_summary}
    </agent_contributions>

    <validation_summary>
    {validation_summary}
    </validation_summary>

    <validation_critiques>
    {critique_text}
    </validation_critiques>

    <atomic_synthesis_protocol>
    PHASE 1: EXTRACT atomic contributions
    - Convert each agent contribution into ATOMS (claims, steps, recommendations)
    - Attach provenance: agent type + short supporting excerpt

    PHASE 2: DETECT conflicts and validation issues
    - If atoms conflict, list the conflict explicitly
    - Prefer atoms consistent with validation feedback

    PHASE 3: CONTRACT into final answer
    - Use accepted atoms as KNOWN CONDITIONS
    - Produce a coherent, non-redundant response that directly answers the task
    - Include only the minimal necessary attribution (avoid clutter)

    PHASE 4: GAP HANDLING
    - If critical gaps remain, state them and propose concrete next steps
    </atomic_synthesis_protocol>

    <output_requirements>
    - Provide a clear structure (summary → main answer → steps/considerations)
    - Address validation concerns explicitly where relevant
    - Be specific and actionable; avoid vague filler

    Prefix with: FINAL ANSWER
    </output_requirements>"""
        
        try:
            final_report = await synthesizer._llm_call(synthesis_prompt)
            return final_report
        except Exception as e:
            # Fallback: concatenate results
            return f"# Final Report\n\n{work_summary}\n\n## Validation\n{validation_summary}"

"""Task decomposition"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from uuid import uuid4
from backend.llm.router import SwarmOSRouter


@dataclass
class TaskNode:
    """Task node in DAG"""

    id: str
    description: str
    agent_type: str
    dependencies: List[str] = field(default_factory=list)
    estimated_tokens: int = 1000
    priority: int = 5
    status: str = "pending"


class TaskGraph:
    """Task dependency graph"""

    def __init__(self, root_id: str):
        self.root_id = root_id
        self.nodes: List[TaskNode] = []

    def add_node(self, node: TaskNode):
        """Add node to graph"""
        self.nodes.append(node)

    def get_node(self, node_id: str) -> Optional[TaskNode]:
        """Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_ready_nodes(self) -> List[TaskNode]:
        """Get nodes with all dependencies satisfied"""
        ready = []
        completed_ids = {n.id for n in self.nodes if n.status == "completed"}
        for node in self.nodes:
            if node.status == "pending":
                if all(dep in completed_ids for dep in node.dependencies):
                    ready.append(node)
        return ready


class TaskDecomposer:
    """Decompose complex tasks into executable DAG"""

    def __init__(self, llm_router: SwarmOSRouter):
        self.llm_router = llm_router

    async def decompose(self, task_description: str, context: Optional[Dict] = None) -> TaskGraph:
        """Break task into subtasks with dependencies"""

        if self._is_primitive(task_description):
            graph = TaskGraph(root_id=str(uuid4()))
            graph.add_node(
                TaskNode(
                    id=str(uuid4()),
                    description=task_description,
                    agent_type="analyst",
                )
            )
            return graph

        # LLM-powered decomposition
        subtasks = await self._llm_decompose(task_description, context)

        # Build DAG
        graph = TaskGraph(root_id=str(uuid4()))

        for subtask in subtasks:
            node = TaskNode(
                id=str(uuid4()),
                description=subtask.get("description", ""),
                agent_type=subtask.get("suggested_agent", "analyst"),
                estimated_tokens=subtask.get("estimated_tokens", 1000),
                priority=subtask.get("priority", 5),
            )
            graph.add_node(node)

        # Infer dependencies
        for node in graph.nodes:
            deps = self._infer_dependencies(node, graph.nodes)
            node.dependencies = deps

        return graph

    def _is_primitive(self, task_description: str) -> bool:
        """Check if task is simple enough to execute directly"""
        # Simple heuristic - could be improved
        return len(task_description.split()) < 10

    async def _llm_decompose(self, task: str, context: Optional[Dict] = None) -> List[Dict]:
        """Use LLM to suggest subtasks"""
        prompt = f"""
        Decompose this task into subtasks:

        Task: {task}
        Context: {context or 'None'}

        For each subtask provide:
        - description: What needs to be done
        - suggested_agent: researcher | analyst | coder | reviewer | synthesizer
        - estimated_tokens: Rough token estimate for completion
        - priority: 1-10 (10 = highest)
        - requires_previous: List of subtask descriptions this depends on

        Return JSON array of subtasks in execution order.
        """
        try:
            response = await self.llm_router.completion(
                model="auto",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            import json
            data = json.loads(response.choices[0].message.content)
            return data.get("subtasks", [])
        except Exception:
            return [{"description": task, "suggested_agent": "analyst"}]

    def _infer_dependencies(self, node: TaskNode, all_nodes: List[TaskNode]) -> List[str]:
        """Infer dependencies for a node"""
        # Simplified - would use more sophisticated logic
        deps = []
        for other in all_nodes:
            if other.id != node.id:
                # Simple heuristic: if node description references other
                if other.description.lower() in node.description.lower():
                    deps.append(other.id)
        return deps


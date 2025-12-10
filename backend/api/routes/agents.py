"""Agent API routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
from backend.models.agent import Agent
from backend.memory.manager import MemoryManager
from backend.models.memory import MemoryScope

router = APIRouter(prefix="/api/agents", tags=["agents"])


def get_memory() -> MemoryManager:
    """Get memory manager instance"""
    from backend.main import app
    return app.state.memory


@router.get("", response_model=List[Agent])
async def list_agents():
    """List all active agents across all tasks"""
    from backend.main import app
    orchestrator = app.state.orchestrator
    
    # Collect all agents from all tasks
    all_agents = []
    for task_id, agents in orchestrator.task_agents.items():
        for a in agents:
            all_agents.append(Agent(
                id=a.id,
                name=getattr(a, "name", a.agent_type.capitalize()),
                agent_type=a.agent_type,
                provider=getattr(a, "provider", "auto"),
                status=a.status,
                capabilities=a.capabilities,
                current_load=a.current_load,
            ))
    return all_agents


@router.get("/status")
async def get_agent_status():
    """Get agent status summary"""
    from backend.main import app
    orchestrator = app.state.orchestrator
    
    # Collect all agents from all tasks
    all_agents = []
    for agents in orchestrator.task_agents.values():
        all_agents.extend(agents)
    
    return {
        "total": len(all_agents),
        "idle": len([a for a in all_agents if a.status == "idle"]),
        "processing": len([a for a in all_agents if a.status == "processing"]),
        "error": len([a for a in all_agents if a.status == "error"]),
    }


@router.get("/{agent_id}/memory")
async def get_agent_memory(
    agent_id: str,
    scope: Optional[MemoryScope] = None,
    limit: int = 50,
    memory: MemoryManager = Depends(get_memory),
):
    """Get agent memory entries (thinking, work, output)"""
    entries = await memory.query(
        namespace=f"agent:{agent_id}", scope=scope, limit=limit
    )
    return [e.dict() for e in entries]


@router.get("/stream")
async def stream_agent_updates():
    """Stream agent activity updates via SSE"""
    async def event_generator():
        # Placeholder - would connect to Redis Streams in production
        yield f"data: {json.dumps({'type': 'agent_update', 'message': 'No updates'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

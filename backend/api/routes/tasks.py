"""Task API routes with database persistence"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
import json

from backend.models.task import (
    Task,
    CreateTaskRequest,
    TaskResponse,
    TaskSummary,
    TaskDetail,
    TaskStatus,
)
from backend.core.orchestrator import Orchestrator
from backend.memory.manager import MemoryManager
from backend.memory.postgres_store import PostgresMemoryStore
from backend.models.memory import MemoryScope

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# In-memory cache for active tasks (fast access during execution)
# Database is the source of truth for persistence
tasks_store: dict[str, Task] = {}


def get_orchestrator() -> Orchestrator:
    """Get orchestrator instance"""
    from backend.main import app
    return app.state.orchestrator


def get_memory() -> MemoryManager:
    """Get memory manager instance"""
    from backend.main import app
    return app.state.memory


def get_postgres_store() -> Optional[PostgresMemoryStore]:
    """Get PostgreSQL store for task persistence"""
    from backend.main import app
    return getattr(app.state.memory, 'postgres_store', None)


async def save_task_to_db(task: Task, postgres_store: Optional[PostgresMemoryStore]):
    """Save task to database"""
    if postgres_store:
        try:
            task_data = {
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "provider": task.provider,
                "context": task.context,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "completed_at": task.completed_at,
                "tokens_used": task.tokens_used,
                "agents_count": task.agents_count,
                "progress": task.progress,
                "debate_state": task.debate_state,
                "subtasks": task.subtasks,
                "validation_results": task.validation_results,
            }
            await postgres_store.save_task(task_data)
        except Exception as e:
            print(f"Warning: Failed to save task to database: {e}")


async def execute_task_with_persistence(
    orchestrator: Orchestrator, 
    task: Task, 
    postgres_store: Optional[PostgresMemoryStore]
):
    """Execute task and persist updates"""
    try:
        await orchestrator.execute_task(task)
    finally:
        # Always save final state to database
        await save_task_to_db(task, postgres_store)


@router.post("", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Create and optionally execute a task"""
    try:
        # Expand query with error handling
        try:
            expansion = await orchestrator.expand_query(request.description)
        except Exception as e:
            # If expansion fails, use a simple default expansion
            print(f"Query expansion failed: {e}")
            expansion = {
                "original": request.description,
                "execution_mode": "direct",
                "expanded_queries": [request.description],
                "requires_debate": False,
            }

        # Create task record
        task = await orchestrator.create_task(
            description=request.description,
            provider=request.provider,
            expansion=expansion,
        )

        # Store task in memory cache
        tasks_store[task.id] = task
        
        # Persist to database
        await save_task_to_db(task, postgres_store)

        # Start execution in background
        if request.auto_execute:
            background_tasks.add_task(
                execute_task_with_persistence, 
                orchestrator, 
                task, 
                postgres_store
            )

        return TaskResponse(
            id=task.id,
            status=task.status,
            description=task.description,
            expansion=expansion,
        )
    except Exception as e:
        print(f"Error creating task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("", response_model=List[TaskSummary])
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """List tasks with optional filtering (from database + in-memory)"""
    
    # Start with in-memory active tasks
    tasks_dict: dict[str, Task] = dict(tasks_store)
    
    # Merge with database tasks (database is source of truth for completed)
    if postgres_store:
        try:
            db_tasks = await postgres_store.list_tasks(status=status, limit=limit + offset, offset=0)
            for db_task in db_tasks:
                task_id = db_task["id"]
                # In-memory takes precedence for active tasks
                if task_id not in tasks_dict:
                    # Convert dict to Task object
                    tasks_dict[task_id] = Task(
                        id=db_task["id"],
                        description=db_task["description"],
                        status=TaskStatus(db_task["status"]),
                        provider=db_task["provider"],
                        created_at=db_task["created_at"],
                        agents_count=db_task.get("agents_count", 0),
                        tokens_used=db_task.get("tokens_used"),
                        progress=db_task.get("progress"),
                    )
        except Exception as e:
            print(f"Warning: Failed to load tasks from database: {e}")
    
    tasks = list(tasks_dict.values())

    if status:
        tasks = [t for t in tasks if t.status.value == status]

    # Sort by created_at desc
    tasks.sort(key=lambda t: t.created_at, reverse=True)

    # Paginate
    tasks = tasks[offset : offset + limit]

    return [TaskSummary.from_orm(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Get detailed task information"""

    # Check in-memory cache first (active tasks)
    task = tasks_store.get(task_id)
    
    if not task and postgres_store:
        # Try database
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task:
                task = Task(
                    id=db_task["id"],
                    description=db_task["description"],
                    status=TaskStatus(db_task["status"]),
                    provider=db_task["provider"],
                    context=db_task.get("context"),
                    result=db_task.get("result"),
                    error=db_task.get("error"),
                    created_at=db_task["created_at"],
                    updated_at=db_task.get("updated_at", db_task["created_at"]),
                    completed_at=db_task.get("completed_at"),
                    tokens_used=db_task.get("tokens_used"),
                    agents_count=db_task.get("agents_count", 0),
                    progress=db_task.get("progress"),
                    debate_state=db_task.get("debate_state"),
                    subtasks=db_task.get("subtasks", []),
                    validation_results=db_task.get("validation_results"),
                )
        except Exception as e:
            print(f"Warning: Failed to load task from database: {e}")
    
    if not task:
        raise HTTPException(404, "Task not found")

    return TaskDetail.from_orm(task)


@router.get("/{task_id}/stream")
async def stream_task_updates(
    task_id: str, memory: MemoryManager = Depends(get_memory)
):
    """Stream real-time task updates via SSE"""

    async def event_generator():
        async for update in memory.subscribe_to_task(task_id):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id}/debate")
async def get_debate_state(
    task_id: str,
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Get current debate state for a task"""

    task = tasks_store.get(task_id)
    
    if not task and postgres_store:
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task and db_task.get("debate_state"):
                return db_task["debate_state"]
        except Exception as e:
            print(f"Warning: Failed to load debate from database: {e}")
    
    if not task or not task.debate_state:
        raise HTTPException(404, "Debate not found")

    return task.debate_state


@router.get("/{task_id}/memory", response_model=List)
async def get_task_memory(
    task_id: str,
    scope: Optional[MemoryScope] = None,
    limit: int = 50,
    memory: MemoryManager = Depends(get_memory),
):
    """Query task memory"""

    entries = await memory.query(
        namespace=f"task:{task_id}", scope=scope, limit=limit
    )

    return [e.dict() for e in entries]


@router.get("/{task_id}/subtasks")
async def get_task_subtasks(
    task_id: str,
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Get subtasks for a task"""
    
    # Check in-memory cache first
    task = tasks_store.get(task_id)
    
    if task and task.subtasks:
        return {"subtasks": task.subtasks}
    
    # Try database
    if postgres_store:
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task and db_task.get("subtasks"):
                return {"subtasks": db_task["subtasks"]}
        except Exception as e:
            print(f"Warning: Failed to load subtasks from database: {e}")
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    return {"subtasks": []}


@router.get("/{task_id}/validation")
async def get_task_validation(
    task_id: str,
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Get validation results for a task"""
    
    # Check in-memory cache first
    task = tasks_store.get(task_id)
    
    if task and task.validation_results:
        return {"validation": task.validation_results}
    
    # Try database
    if postgres_store:
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task and db_task.get("validation_results"):
                return {"validation": db_task["validation_results"]}
        except Exception as e:
            print(f"Warning: Failed to load validation from database: {e}")
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    return {"validation": None}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Delete a task, stopping it if running"""
    
    task = tasks_store.get(task_id)
    
    # Also check database if not in memory
    if not task and postgres_store:
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task:
                task = Task(id=db_task["id"], description=db_task["description"])
        except Exception:
            pass
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Stop task if running
    if task_id in tasks_store:
        mem_task = tasks_store[task_id]
        if mem_task.status in [TaskStatus.IN_PROGRESS, TaskStatus.DEBATING, TaskStatus.VALIDATING]:
            mem_task.status = TaskStatus.CANCELLED
    
    # Remove from in-memory store
    if task_id in tasks_store:
        del tasks_store[task_id]
    
    # Remove from database
    if postgres_store:
        try:
            await postgres_store.delete_task(task_id)
        except Exception as e:
            print(f"Warning: Failed to delete task from database: {e}")
    
    return {"message": "Task deleted", "task_id": task_id}


from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    use_web_search: bool = False
    target_agent: Optional[str] = None
    context: Optional[dict] = None


@router.post("/{task_id}/chat")
async def chat_with_task(
    task_id: str,
    request: ChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    postgres_store: Optional[PostgresMemoryStore] = Depends(get_postgres_store),
):
    """Chat with task context using RAG - can use web search and target specific agents"""
    
    # Get task context
    task = tasks_store.get(task_id)
    if not task and postgres_store:
        try:
            db_task = await postgres_store.get_task(task_id)
            if db_task:
                task = Task(
                    id=db_task["id"],
                    description=db_task["description"],
                    result=db_task.get("result"),
                    context=db_task.get("context"),
                )
        except Exception:
            pass
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Build context for RAG
    context_parts = [
        f"Original Task: {task.description}",
    ]
    
    if task.result:
        result_content = task.result.get("content", "") if isinstance(task.result, dict) else str(task.result)
        context_parts.append(f"Task Result: {result_content[:3000]}")
    
    if request.context:
        if request.context.get("agents"):
            context_parts.append(f"Available Agents: {', '.join(request.context['agents'])}")
    
    # Web search if enabled
    sources = []
    if request.use_web_search:
        try:
            if orchestrator.tools:
                search_results = await orchestrator.tools.execute("web_search", {"query": request.message, "max_results": 3})
                if search_results:
                    for result in search_results[:3]:
                        sources.append(result.get("url", result.get("title", "Source")))
                        context_parts.append(f"Web Result: {result.get('content', result.get('snippet', ''))[:500]}")
        except Exception as e:
            print(f"Web search failed: {e}")
    
    # Build prompt
    agent_role = request.target_agent or "assistant"
    prompt = f"""<aot_framework>
You implement Atom of Thought (AoT) follow-up handling.
Parse context into atomic facts before answering.
Answer draws only from verified atomic context units.
</aot_framework>

<role>
You are a {agent_role.capitalize()} answering follow-up questions about a completed task.
Use only the provided atomic context units to give accurate, helpful responses.
</role>

<context>
{chr(10).join(context_parts)}
</context>

<user_question>
{request.message}
</user_question>

<atomic_context_protocol>
PHASE 1: PARSE context into atomic facts

```json
{{
    "context_atoms": [
        {{
            "atom_id": "CTX1",
            "fact": "specific fact from context",
            "source": "where in context this came from",
            "relevance_to_question": "high|medium|low"
        }}
    ]
}}
```

PHASE 2: MATCH question to relevant atoms

```json
{{
    "question_analysis": {{
        "question_type": "factual|clarification|extension|new_direction",
        "relevant_atoms": ["CTX1", "CTX3"],
        "missing_information": ["what's needed but not in context"]
    }}
}}
```

PHASE 3: CONSTRUCT answer from atoms

```json
{{
    "answer_construction": {{
        "supporting_atoms": ["CTX1", "CTX3"],
        "synthesis": "answer derived from atoms",
        "citations": ["from CTX1: ...", "from CTX3: ..."],
        "limitations": "what the answer doesn't cover"
    }}
}}
```
</atomic_context_protocol>

<instructions>
- Answer based ONLY on provided context atoms
- If web search results are included, cite them
- Be concise but thorough
- If information isn't in context, say so explicitly
- Do not hallucinate information not present in context
</instructions>

<output_schema>
```json
{{
    "context_parsing": {{}},
    "question_matching": {{}},
    "answer": {{
        "response": "direct answer to question",
        "sources": ["atomic sources used"],
        "confidence": "high|medium|low",
        "limitations": "what answer doesn't address"
    }}
}}
```

[Natural language answer based on atomic analysis]
</output_schema>"""

    try:
        response = await orchestrator.llm_router.completion(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        answer = response.choices[0].message.content
        
        return {
            "response": answer,
            "agent": agent_role.capitalize() if request.target_agent else None,
            "sources": sources if sources else None,
        }
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Chat failed: {str(e)}")

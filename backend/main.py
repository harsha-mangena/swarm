"""FastAPI application entry point"""

from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from backend.config import settings
from backend.llm.router import SwarmOSRouter
from backend.memory.manager import MemoryManager
from backend.memory.redis_store import RedisMemoryStore
from backend.memory.vector_store import QdrantMemoryStore
from backend.memory.postgres_store import PostgresMemoryStore
from backend.memory.context_normalizer import ContextNormalizer
from backend.tools.registry import ToolRegistry
from backend.core.orchestrator import Orchestrator
from backend.api.routes import tasks, agents, providers, files, settings
from backend.api.websocket import task_websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    llm_router = SwarmOSRouter()

    # Initialize memory stores (with error handling for missing services)
    redis_store = RedisMemoryStore()
    try:
        await redis_store.connect()
    except Exception as e:
        print(f"Warning: Redis connection failed: {e}. Continuing without Redis.")
        redis_store = None

    qdrant_store = QdrantMemoryStore()
    try:
        await qdrant_store.connect()
    except Exception as e:
        print(f"Warning: Qdrant connection failed: {e}. Continuing without Qdrant.")
        qdrant_store = None

    postgres_store = PostgresMemoryStore()
    try:
        await postgres_store.connect()
    except Exception as e:
        print(f"Warning: PostgreSQL connection failed: {e}. Continuing without PostgreSQL.")
        postgres_store = None

    normalizer = ContextNormalizer()
    memory = MemoryManager(redis_store, qdrant_store, postgres_store, normalizer)

    # Initialize tools
    tools = ToolRegistry()

    # Create orchestrator - agents are created dynamically per task via Delegator
    orchestrator = Orchestrator(llm_router, memory, tools)

    # Store in app state
    app.state.llm_router = llm_router
    app.state.memory = memory
    app.state.tools = tools
    app.state.orchestrator = orchestrator

    yield

    # Shutdown
    if redis_store:
        try:
            await redis_store.disconnect()
        except:
            pass
    if qdrant_store:
        try:
            await qdrant_store.disconnect()
        except:
            pass
    if postgres_store:
        try:
            await postgres_store.disconnect()
        except:
            pass


app = FastAPI(
    title="SwarmOS",
    description="Local-first multi-agent control plane",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Vue dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from Vue build
static_dir = Path("backend/static")
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve Vue SPA - catch all non-API routes"""
        # Don't serve SPA for API or WebSocket routes
        if path.startswith("api") or path.startswith("ws"):
            return None
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built. Run 'npm run build' in frontend directory."}

# Include routers
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(providers.router)
app.include_router(files.router)
app.include_router(settings.router)

# WebSocket route
@app.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await task_websocket(websocket, task_id)


# Frontend routes are handled by Vue router via serve_spa above


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    from backend.api.routes.tasks import tasks_store
    tasks = list(tasks_store.values())
    return {
        "total_tasks": len(tasks),
        "active_tasks": len([t for t in tasks if t.status.value in ["in_progress", "debating"]]),
        "completed_tasks": len([t for t in tasks if t.status.value == "completed"]),
        "total_tokens": sum(t.tokens_used or 0 for t in tasks),
    }


@app.get("/api/status")
async def get_status():
    """Get system status"""
    from backend.llm.providers import ProviderStatus
    provider_status = ProviderStatus()
    providers = await provider_status.check_all()
    return {
        "providers": providers,
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


# SwarmOS - AI Assistant Guide

## Quick Start

```bash
# Start infrastructure
./scripts/run.sh start

# Install dependencies
poetry install

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn backend.main:app --reload --port 8000

# In another terminal, start Vue dev server
cd frontend && npm run dev
```

## Key Files

- `backend/main.py` - FastAPI entry point
- `backend/core/orchestrator.py` - Task orchestration
- `backend/debate/engine.py` - Debate state machine
- `backend/memory/manager.py` - Memory abstraction
- `frontend/templates/base.html` - Base layout

## Common Tasks

### Add New Agent Type

1. Create `backend/agents/{name}.py`
2. Inherit from `BaseAgent`
3. Implement `process()` and `use_tool()`
4. Register in `backend/agents/__init__.py`
5. Add to agent list in `backend/main.py`

### Add New API Endpoint

1. Create route in `backend/api/routes/`
2. Add Pydantic models in `backend/models/`
3. Include router in `backend/main.py`
4. Add HTMX partial in `frontend/templates/partials/`

### Modify Debate Logic

- Scoring weights: `backend/debate/scoring.py`
- Convergence rules: `backend/debate/convergence.py`
- State machine: `backend/debate/engine.py`

## Testing

```bash
pytest backend/tests/unit/           # Unit tests
pytest backend/tests/integration/    # Integration tests
pytest backend/tests/evaluations/    # LLM evaluations
```

## Environment Variables

- `REDIS_URL` - Redis connection
- `DATABASE_URL` - PostgreSQL connection
- `QDRANT_URL` - Vector store
- `ANTHROPIC_API_KEY` - Claude
- `GOOGLE_API_KEY` - Gemini
- `OPENAI_API_KEY` - OpenAI
- `TAVILY_API_KEY` - Web search

## Architecture Notes

- Agents are stateless; state is in memory layer
- Debate engine uses LangGraph-style state machine
- Memory is three-tier: global/task/agent scopes
- LLM router handles fallbacks and circuit breakers


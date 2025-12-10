# SwarmOS

Local-first multi-agent control plane with hybrid debate mechanism.

## Quick Start

```bash
# Start infrastructure services
docker-compose up -d

# Install Python dependencies
poetry install

# Install frontend dependencies
cd frontend && npm install

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start backend (in one terminal)
uvicorn backend.main:app --reload --port 8000

# Start frontend dev server (in another terminal)
cd frontend && npm run dev

# Or build for production
cd frontend && npm run build
```

## Architecture

SwarmOS orchestrates LLM-driven agents to execute complex tasks through competitive-collaborative debate. The system supports heterogeneous providers (Ollama local + Gemini/Claude/OpenAI/OpenRouter cloud) with intelligent memory sharing across agents.

### Key Features

- **Hybrid Debate**: Agents compete AND collaborate; best option wins via voting/scoring
- **Shared Memory**: Three-tier memory (global/task/agent) with provider-aware context compression
- **Researcher Agent**: Deep web research with Tavily/Brave, iterative search refinement
- **Intelligent Orchestrator**: Autonomous query expansion, task decomposition, agent routing
- **Multi-Provider**: Unified interface for Ollama, Gemini, Claude, OpenAI, OpenRouter
- **Clean UI**: Minimalistic dashboard with HTMX + Alpine.js + Tailwind

## Project Structure

```
swarmos/
├── backend/          # FastAPI application
├── frontend/         # HTMX + Alpine.js UI
├── infrastructure/   # Docker, Terraform configs
└── scripts/          # Utility scripts
```

## Documentation

- [Implementation Guide](./IMPLEMENTATION.md) - Complete technical guide
- [AGENTS.md](./AGENTS.md) - AI assistant documentation
- [.cursor/rules/](./.cursor/rules/) - Cursor IDE rules

## Development

See [AGENTS.md](./AGENTS.md) for development guidelines and common tasks.

# swarm

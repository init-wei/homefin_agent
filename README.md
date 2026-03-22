# HomeFin Agent

HomeFin Agent is a backend-first household finance platform with an agent/tooling integration layer. It provides a unified ledger model for personal and family finance data, exposes structured analytics APIs, and can be connected to OpenClaw through MCP and audited tool calls.

## What Exists Today

The repository already contains a working backend skeleton:

- FastAPI application with core resource routers
- SQLAlchemy models and repositories
- Alembic migration scaffold with an initial schema
- Statement import pipeline for WeChat CSV and a simple bank CSV format
- Analytics services for monthly summary, category breakdown, member spending, budget status, and net worth
- `AgentToolService` with audit logging and owner/member scope enforcement
- Python MCP server for agent tool exposure
- OpenClaw bundle scaffold and CLI bridge
- Automated tests

## Project Layout

```text
homefin_agent/
├─ apps/
│  ├─ api/
│  ├─ mcp/
│  └─ worker/
├─ application/
│  ├─ dto/
│  └─ services/
├─ adapters/
│  ├─ importers/
│  └─ openclaw/
├─ domain/
│  ├─ entities/
│  ├─ enums/
│  └─ value_objects/
├─ infra/
│  ├─ config/
│  └─ db/
├─ integrations/
│  └─ openclaw/
├─ migrations/
├─ tests/
├─ AGENT.md
└─ pyproject.toml
```

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\\Scripts\\python -m pip install -e ".[dev]"
```

### 2. Configure environment

Copy `.env.example` to `.env` and adjust values if needed.

The default setup uses SQLite:

```env
HOMEFIN_DATABASE_URL=sqlite+pysqlite:///./homefin.db
HOMEFIN_OPENCLAW_CLI_COMMAND=openclaw
```

### 3. Apply schema

```bash
alembic upgrade head
```

### 4. Run the API

```bash
uvicorn apps.api.main:app --reload
```

### 5. Run tests

```bash
.venv\\Scripts\\python -m pytest
```

## Useful Commands

From `Makefile`:

```bash
make install
make run-api
make run-mcp
make db-upgrade
make test
```

## OpenClaw Integration Status

OpenClaw is optional during local backend development.

- You do not need OpenClaw installed to work on the API, DB, imports, analytics, or `AgentToolService`
- You only need OpenClaw for real chat/event integration tests
- If the CLI is missing, the API now returns a structured integration error instead of crashing

Bundle and MCP wiring live under `integrations/openclaw/`.

## Current API Surface

Implemented routes include:

- `POST /households/bootstrap`
- `GET/POST /accounts`
- `GET/POST /categories`
- `GET/POST /budgets`
- `GET/POST/PATCH /transactions`
- `POST /imports/statements`
- `GET /imports/jobs/{job_id}`
- `GET /analytics/*`
- `POST /chat/bindings`
- `POST /chat/messages`
- `GET /chat/audits`

## Current Priorities

The backend skeleton is stable enough for the next phase. The main follow-up tasks are:

1. Add real authentication and current-user injection
2. Move imports to an actual async worker flow
3. Add retry/reprocess support for failed imports
4. Implement richer finance rules such as transfer detection and auto-categorization
5. Perform real OpenClaw end-to-end integration

## Notes For Agents

`AGENT.md` is the canonical task-execution guide for Codex and other coding agents. Read it before making structural changes.

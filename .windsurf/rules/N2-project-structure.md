---
description: Project directory structure and file organization. Generic patterns for Python services and CLI tools.
alwaysApply: false
---

# Project Structure

Python ≥3.13. Build: hatchling + uv-dynamic-versioning (Git PEP 440).

## Layouts

Two supported layouts depending on project type:

### Flat layout — API services (default)

```
<project>/
├── app/                        # source code (package root)
│   ├── main.py                 # entrypoint (FastAPI/Robyn lifespan)
│   ├── core/                   # infrastructure & cross-cutting
│   │   ├── settings.py         # Settings composition (multi-inheritance)
│   │   ├── logger.py           # structured logging
│   │   ├── lifespan.py         # startup/shutdown lifecycle
│   │   ├── middlewares.py      # middleware registry (all_middlewares list)
│   │   ├── exception_handler.py # exception registry (all_exceptions list)
│   │   ├── helpers.py          # shared utilities (timers, decorators)
│   │   ├── security.py         # auth, JWT
│   │   ├── session.py          # session management
│   │   ├── store.py            # data stores (Redis, vector)
│   │   └── redis.py            # Redis client factory
│   ├── config/                 # modular settings (each is BaseSettings subclass)
│   │   ├── core.py             # CoreSettings (paths, redis, env)
│   │   ├── api.py              # ApiSettings (host, port, cors)
│   │   ├── models.py           # ModelsSettings (LLM, embeddings)
│   │   ├── vector.py           # VectorSettings (index, search)
│   │   └── ...                 # one per domain
│   ├── api/                    # REST layer
│   │   ├── deps.py             # DI chains (headers → session → schema → store)
│   │   └── router/             # route handlers (one per resource)
│   │       ├── health.py
│   │       ├── entities.py
│   │       └── documents.py
│   ├── cli/                    # Typer CLI
│   │   ├── main.py             # typer.Typer() + subcommands
│   │   ├── helpers.py
│   │   └── commands/           # grouped subcommands
│   │       └── api/
│   │           ├── main.py
│   │           └── entities.py
│   ├── models/                 # Pydantic models (domain + API DTOs)
│   │   ├── core.py             # RequestHeaders, Session
│   │   ├── api.py              # Request/Response DTOs
│   │   ├── entity.py           # re-exports from submodules
│   │   ├── node/               # complex model subdomain
│   │   │   ├── base.py         # Node, Metadata, field markers
│   │   │   ├── schema.py       # SearchIndexSchema[D]
│   │   │   ├── scored.py       # ScoredNode
│   │   │   └── matched.py      # MatchedNode[S], MatchedNodeList[M]
│   │   └── store/              # store-specific models
│   │       └── entity.py       # Entity, QueryEntity, IndexEntity
│   ├── adapters/               # external service clients
│   │   ├── base.py             # Adapter base (retry transport, healthcheck)
│   │   └── nlp.py              # NLPRuntimeAdapter
│   ├── pipelines/              # orchestration pipelines
│   │   ├── base.py             # Pipeline[T_in, T_out], IngestionPipeline[D]
│   │   ├── entities.py
│   │   └── strategies/         # pipeline strategies
│   ├── processors/             # data processors (pre/post pipeline)
│   │   ├── base.py             # Processor ABC
│   │   ├── annotator.py
│   │   ├── reranker.py
│   │   └── conditions/         # processor conditions
│   ├── operational/            # math/scoring utilities
│   │   ├── attenuator.py
│   │   ├── booster.py
│   │   ├── confidence.py
│   │   └── softmax.py
│   └── tasks/                  # background & scheduled tasks
│       └── cron/
│           └── session_cleanup.py
├── test/                       # tests (mirrors app/)
├── docs/                       # documentation
├── helm/                       # Kubernetes Helm charts
├── docker/                     # extra compose files
├── .github/workflows/          # CI/CD
├── compose.yml                 # Docker Compose
├── Dockerfile                  # multi-stage build
├── Makefile                    # dev commands
├── pyproject.toml              # config & deps
├── uv.lock                     # locked deps
├── .pre-commit-config.yaml     # git hooks
└── env.template                # env var template
```

### Src layout — packages, agents, libraries

```
<project>/
├── src/<package>/              # source code (importable package)
│   ├── __main__.py             # python -m entrypoint
│   ├── core/
│   │   ├── settings.py
│   │   └── logger.py
│   ├── api/
│   │   ├── deps.py
│   │   └── router.py           # single router (smaller projects)
│   ├── models/
│   │   ├── api.py              # Request/Response DTOs
│   │   └── agent.py            # domain models
│   ├── adapters/
│   │   ├── stt.py
│   │   └── tts.py
│   ├── agents/                 # AI agent implementations
│   │   ├── concierge.py
│   │   ├── inventory.py
│   │   └── utils.py
│   ├── sessions/               # session orchestration
│   ├── tasks/                  # background tasks
│   │   ├── models.py
│   │   ├── status.py
│   │   ├── registry.py
│   │   └── executor.py
│   ├── tools/                  # agent tools / function tools
│   ├── operations/             # domain-specific ops
│   └── cli/                    # CLI module
├── tests/                      # tests (note: tests/ not test/)
├── compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── uv.lock
```

### CLI-only layout — developer tools

```
<project>/
├── cli/
│   ├── main.py                 # cyclopts/typer entrypoint
│   ├── settings.py             # single BaseSettings
│   ├── commands/               # command modules
│   │   ├── generate.py
│   │   └── sync_instructions.py
│   └── utils/
│       └── merger.py
├── tests/
│   ├── conftest.py
│   └── unit/
├── pyproject.toml
└── Makefile
```

## Common Directories

| Directory | Purpose | Always present |
|-----------|---------|---------------|
| `core/` | Settings, logger, helpers, lifecycle, security | Yes |
| `config/` | Modular BaseSettings subclasses (one per domain) | API services |
| `api/` | REST routes, DI deps | API services |
| `models/` | Pydantic models, DTOs, domain objects | Yes |
| `adapters/` | External service clients (HTTP, gRPC, WebSocket) | When external deps |
| `cli/` | Typer/Cyclopts commands | When CLI needed |
| `tasks/` | Background jobs, cron, scheduled work | When async tasks |
| `pipelines/` | Orchestration (preprocessors → run → postprocessors) | Data processing |
| `processors/` | Individual data transform steps | Data processing |
| `operational/` / `operations/` | Math, scoring, audio, domain-specific ops | Domain-specific |
| `agents/` | AI agent implementations | Agent projects |
| `sessions/` | Session/conversation orchestration | Agent projects |
| `tools/` | Agent function tools | Agent projects |

## Config Composition

Small projects — single `core/settings.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # all settings here
```

Large projects — modular multi-inheritance:

```
config/core.py    → class CoreSettings(BaseSettings): ...
config/api.py     → class ApiSettings(BaseSettings): ...
config/models.py  → class ModelsSettings(BaseSettings): ...
config/vector.py  → class VectorSettings(BaseSettings): ...

core/settings.py  → class Settings(CoreSettings, ApiSettings, ModelsSettings, VectorSettings): ...
```

## test/

```
test/                               # flat layout
tests/                              # src layout
├── unit/
│   ├── conftest.py                 # FakeRedis, mocks, small fixtures
│   └── app/                        # mirrors app/ exactly
│       ├── core/
│       ├── models/
│       ├── adapters/
│       └── ...
├── integration/
│   ├── conftest.py                 # real Redis, HTTP clients
│   └── app/                        # mirrors app/
│       ├── api/router/
│       ├── core/store/
│       └── ...
├── evaluation/
│   └── regression/                 # polars-based regression
│       ├── <domain>/
│       │   ├── test_regression.py
│       │   ├── models.py
│       │   └── run_experiment.py
├── resources/                      # shared test data (JSON, fixtures)
│   └── <domain>/
└── notebook/                       # scratch/learning (gitignored)
```

## Makefile Common Targets

```makefile
.PHONY: install sync lint type test dev prod infra down

install:                            # system deps + uv sync + pre-commit
sync:                               # uv sync --dev
lint:                               # ruff check --fix + ruff format
type:                               # ty check
test:                               # uv run pytest
dev:                                # run dev server
prod:                               # run prod server
infra:                              # docker compose up -d (deps only)
down:                               # docker compose down
```

## Dockerfile Pattern

```dockerfile
# Builder
FROM ghcr.io/astral-sh/uv:0.8-python3.13-bookworm AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY .git pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Runtime
FROM python:3.13-slim-bookworm
RUN useradd -m -u 1000 app
COPY --from=builder /app/.venv /app/.venv
COPY app/ /app/app/
USER app
ENV PYTHONPATH="/app"
EXPOSE 8012
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]
```

## Entry Points (pyproject.toml)

```toml
[project.scripts]
cli = "app.cli.main:cli_entrypoint"     # flat layout
cli = "<package>.cli:cli"                # src layout
```

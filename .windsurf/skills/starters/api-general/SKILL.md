---
name: starter-api-general
description: |
  Starter template for general-purpose FastAPI APIs. Use when scaffolding a new API service,
  creating a new FastAPI project from scratch, or when the user asks to start a new API.
  Includes minimum stack, project tree, architecture patterns, and essential boilerplate.
  Reference projects: ai-jeff, ai-haven.
---

# Starter: General API (FastAPI)

## Minimum Stack

### pyproject.toml

```toml
[build-system]
requires = ["hatchling>=1.24", "uv-dynamic-versioning>=0.7.0"]
build-backend = "hatchling.build"

[project]
name = "<project-name>"
dynamic = ["version"]
requires-python = ">=3.13"
dependencies = [
    # Framework
    "fastapi[standard]>=0.115.0",
    "uvicorn>=0.34.0",
    # Data & Config
    "pydantic>=2.12.0",
    "pydantic-settings>=2.13.0",
    # Serialization
    "orjson>=3.10.0",
    # Logging & Observability
    "structlog>=25.0.0",
    "asgi-correlation-id>=4.3.0",
    # Type Safety
    "beartype>=0.21.0",
    # Async I/O
    "aiofiles>=24.1.0",
    # HTTP Client
    "httpx>=0.28.0",
    # Utilities
    "glom>=24.11.0",
    "gitpython>=3.1.45",
    "rich>=14.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.0.0",
    "pytest-dotenv>=0.5.2",
    "ruff>=0.14.0",
    "ty>=0.0.17",
    "pre-commit>=4.4.0",
]

[tool.hatch.version]
source = "uv-dynamic-versioning"

[tool.uv-dynamic-versioning]
enable = true

[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.ty.environment]
python-version = "3.13"

[tool.ty.rules]
possibly-unresolved-reference = "error"
unresolved-import = "error"

[tool.pytest.ini_options]
asyncio_mode = "auto"
env_files = [".env"]
testpaths = ["test"]
```

## Project Tree

```
<project>/
├── app/
│   ├── main.py                     # FastAPI app factory + lifespan
│   ├── core/
│   │   ├── settings.py             # Settings (pydantic-settings, ClassVar paths)
│   │   ├── logger.py               # structlog + LogIcon enum
│   │   ├── lifespan.py             # BaseEvent[T], Lifespan manager
│   │   ├── middlewares.py          # middleware registry
│   │   └── helpers.py              # shared utilities
│   ├── api/
│   │   ├── deps.py                 # DI chains (Depends)
│   │   └── router/
│   │       └── health.py           # GET /health
│   ├── models/
│   │   └── core.py                 # shared DTOs, enums
│   ├── adapters/                   # external service clients
│   │   └── base.py                 # Adapter ABC with retry
│   └── tasks/                      # background tasks (optional)
├── test/
│   ├── conftest.py
│   └── unit/
│       └── app/
├── .github/workflows/
│   └── ci.yml
├── compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── uv.lock
├── .pre-commit-config.yaml
└── .env.template
```

## Essential Patterns

### main.py — App Factory + Lifespan

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.settings import settings as st
from app.api.router.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    yield
    # shutdown


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=st.API_NAME,
        version=st.API_VERSION,
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
```

### core/settings.py — Unified Settings

```python
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.helpers import read_pyproject, get_version


class Settings(BaseSettings):
    """Unified settings for service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEBUG: bool = True
    ENVIRONMENT: Literal["DEV", "PROD"] = "DEV"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ClassVar prevents env var lookup
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    PROJECT: ClassVar[dict] = read_pyproject(BASE_DIR / "pyproject.toml")
    API_NAME: ClassVar[str] = PROJECT.get("project", {}).get("name", "api")
    API_VERSION: ClassVar[str] = get_version(BASE_DIR)
    DATA_PATH: ClassVar[Path] = BASE_DIR / "data"

    @computed_field
    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "DEV"


settings = Settings()
```

### core/logger.py — Structured Logging

```python
from enum import StrEnum

import structlog


class LogIcon(StrEnum):
    START = "🚀"
    SUCCESS = "✅"
    ERROR = "❌"
    WARN = "⚠️"
    HEALTH = "💚"
    DB = "🗄️"
    HTTP = "🌐"
    TOOL = "🔧"


def setup_logging(*, json_output: bool = False) -> None:
    """Configure structlog processors."""
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    match json_output:
        case True:
            processors.append(structlog.processors.JSONRenderer())
        case False:
            processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(processors=processors)
```

### api/router/health.py — Health Endpoint

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

### Dockerfile — Multi-Stage Build

```dockerfile
FROM ghcr.io/astral-sh/uv:0.8-python3.13-bookworm AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY .git pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
COPY app/ ./app/

FROM python:3.13-slim-bookworm
RUN useradd -m -u 1000 app
COPY --from=builder /app /app
WORKDIR /app
USER app
ENV PYTHONPATH="/app" PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/api/v1/health || exit 1
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Makefile — Essential Targets

```makefile
.PHONY: install sync lint type test dev prod build

install:
	@command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	@uv sync --dev
	@uv run pre-commit install

sync:
	@uv sync --dev

lint:
	@uv run ruff check --fix app/
	@uv run ruff format app/

type:
	@uv run ty check app/

test:
	@uv run pytest test/ -v

dev:
	@uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

prod:
	@uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

build:
	@docker compose build
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: typecheck
        name: ty check
        entry: uv run ty check app/
        language: system
        pass_filenames: false
        stages: [pre-push]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.0
    hooks:
      - id: gitleaks
        stages: [pre-push]
```

### ci.yml — GitHub Actions

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --frozen --dev
      - run: uv run ruff check app/
      - run: uv run ruff format --check app/

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --frozen --dev
      - run: uv run pytest test/ -v --tb=short

  docker:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Key Conventions

- **Flat layout**: `app/` as package root (no `src/`)
- **Settings import**: `from app.core.settings import settings as st`
- **ClassVar for paths**: prevents pydantic env var lookup
- **orjson**: use for all JSON serialization
- **structlog**: structured logging with icons
- **No `__init__.py`**: implicit namespace packages
- **Async-first**: all handlers async, aiofiles for file I/O
- **DI via Depends()**: chain deps in `api/deps.py`

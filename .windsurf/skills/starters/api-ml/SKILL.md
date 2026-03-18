---
name: starter-api-ml
description: |
  Starter template for high-performance ML/API services built on Robyn (Rust-backed).
  Use when scaffolding a new ML API, high-throughput service, or when the user asks for
  a Robyn-based project. Includes minimum stack, project tree, custom Router with auto
  body/file parsing, event-driven lifespan, and middleware system.
  Reference project: robyn-ml-api.
---

# Starter: ML / High-Performance API (Robyn)

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
    # Framework (Rust-backed)
    "robyn>=0.72.0",
    # Data & Config
    "pydantic>=2.12.0",
    "pydantic-settings>=2.13.0",
    # Serialization (Rust-backed)
    "orjson>=3.10.0",
    # Logging
    "structlog>=25.0.0",
    "colorama>=0.4.6",
    "asgi-correlation-id>=4.3.0",
    # Type Safety
    "beartype>=0.21.0",
    # Utilities
    "gitpython>=3.1.45",
]

[project.optional-dependencies]
ml = ["numpy>=2.0.0", "scikit-learn>=1.5.0"]

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

[tool.hatch.build.targets.wheel]
packages = ["app"]

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
root = "./app"

[tool.ty.rules]
possibly-unresolved-reference = "error"
unresolved-import = "error"

[tool.pytest.ini_options]
asyncio_mode = "auto"
env_files = [".env"]
testpaths = ["test"]

[tool.hatch.envs.default.scripts]
dev = "python -m app.main"
lint = "ruff check --fix app/"
format = "ruff format app/"
typecheck = "ty check"
test = "pytest test/unit -v"
```

## Project Tree

```
<project>/
├── app/
│   ├── main.py                     # Robyn app init, router includes, startup
│   ├── core/
│   │   ├── settings.py             # Settings (ClassVar paths, computed fields)
│   │   ├── logger.py               # structlog + LogIcon (30+ domain icons)
│   │   ├── lifespan.py             # BaseEvent[T] ABC + Lifespan manager
│   │   └── router.py               # Custom Router (auto body/file parsing)
│   ├── events/
│   │   └── process_pool.py         # ProcessPoolEvent (spawn context)
│   ├── middlewares/
│   │   ├── base.py                 # BaseMiddleware ABC + MiddlewareHandler
│   │   └── files.py                # OpenAPI file upload patching
│   ├── models/
│   │   └── core.py                 # UploadFile, BodyType enum
│   └── api/
│       └── health.py               # GET /health endpoint
├── test/
│   ├── conftest.py                 # MockRequest, State fixtures
│   └── unit/
│       └── app/
│           ├── core/
│           │   ├── test_lifespan.py
│           │   └── test_router.py
│           └── events/
│               └── test_process_pool.py
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

### main.py — Robyn App Init

```python
from robyn import Robyn, ALLOW_CORS

from app.core.settings import settings as st
from app.core.lifespan import Lifespan
from app.core.router import Router
from app.events.process_pool import ProcessPoolEvent
from app.middlewares.base import MiddlewareHandler
from app.api.health import router as health_router


app = Robyn(__file__)
ALLOW_CORS(app, origins=["*"])

# Lifespan events
lifespan = Lifespan(app)
lifespan.register(ProcessPoolEvent)

app.startup_handler(lifespan.startup)
app.shutdown_handler(lifespan.shutdown)

# Middlewares
middleware_handler = MiddlewareHandler(app)

# Routes
app.include_router(health_router)


if __name__ == "__main__":
    app.start(host=st.API_HOST, port=st.API_PORT)
```

### core/router.py — Custom Router with Auto-Parsing

```python
import inspect
from collections.abc import Callable
from functools import wraps
from typing import get_type_hints

import orjson
from pydantic import BaseModel
from robyn import Response, SubRouter

from app.models.core import BodyType, UploadFile

FILE_UPLOAD_ENDPOINTS: set[str] = set()


class Router(SubRouter):
    """Enhanced SubRouter with automatic body/file parsing."""

    def _detect_body_type(self, handler: Callable) -> BodyType | None:
        hints = get_type_hints(handler)
        for name, hint in hints.items():
            match hint:
                case t if t is UploadFile:
                    return BodyType.FILE
                case t if isinstance(t, type) and issubclass(t, BaseModel):
                    return BodyType.PYDANTIC
                case t if t is dict:
                    return BodyType.JSONABLE
        return None

    def _wrap_handler(self, handler: Callable) -> Callable:
        body_type = self._detect_body_type(handler)
        if body_type is None:
            return handler

        @wraps(handler)
        async def wrapper(request):
            match body_type:
                case BodyType.PYDANTIC:
                    hints = get_type_hints(handler)
                    model_cls = next(
                        h for h in hints.values()
                        if isinstance(h, type) and issubclass(h, BaseModel)
                    )
                    body = model_cls.model_validate_json(request.body)
                    result = await handler(body)
                case BodyType.FILE:
                    files = UploadFile(request.files)
                    result = await handler(files=files)
                case BodyType.JSONABLE:
                    body = orjson.loads(request.body)
                    result = await handler(body)
                case _:
                    result = await handler(request)

            match result:
                case Response():
                    return result
                case BaseModel():
                    return Response(
                        200, {"content-type": "application/json"},
                        result.model_dump_json(),
                    )
                case dict():
                    return Response(
                        200, {"content-type": "application/json"},
                        orjson.dumps(result),
                    )
                case _:
                    return str(result)

        return wrapper

    def get(self, endpoint: str, **kwargs):
        def decorator(handler):
            return super(Router, self).get(endpoint, **kwargs)(
                self._wrap_handler(handler)
            )
        return decorator

    def post(self, endpoint: str, **kwargs):
        def decorator(handler):
            return super(Router, self).post(endpoint, **kwargs)(
                self._wrap_handler(handler)
            )
        return decorator
```

### core/lifespan.py — Event-Driven Lifecycle

```python
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog

from app.core.logger import LogIcon

T = TypeVar("T")
logger = structlog.get_logger(__name__)


class State:
    """Mutable application state with attribute access."""

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"State has no attribute '{name}'")


class BaseEvent(ABC, Generic[T]):
    """Abstract lifecycle event."""

    @abstractmethod
    async def startup(self) -> T: ...

    async def shutdown(self, instance: T) -> None: ...


class Lifespan:
    """Manages app lifespan with event registration."""

    def __init__(self, app: Any) -> None:
        self._app = app
        self._events: list[type[BaseEvent[Any]]] = []
        self._state = State()

    def register(self, event_cls: type[BaseEvent[Any]]) -> "Lifespan":
        self._events.append(event_cls)
        return self

    async def startup(self) -> None:
        for event_cls in self._events:
            event = event_cls()
            instance = await event.startup()
            name = event_cls.__name__.removesuffix("Event").lower()
            setattr(self._state, name, instance)
            logger.info(f"{name} started", icon=LogIcon.START)
        self._app.inject_global(state=self._state)

    async def shutdown(self) -> None:
        for event_cls in reversed(self._events):
            event = event_cls()
            name = event_cls.__name__.removesuffix("Event").lower()
            instance = getattr(self._state, name, None)
            if instance is not None:
                await event.shutdown(instance)
                logger.info(f"{name} stopped", icon=LogIcon.SUCCESS)
```

### middlewares/base.py — Middleware System

```python
from abc import ABC

from robyn import Request, Response


class BaseMiddleware(ABC):
    """Abstract middleware with before/after hooks."""

    endpoints: frozenset[str] = frozenset()

    def before(self, request: Request) -> Request | Response:
        return request

    def after(self, response: Response) -> Response:
        return response


class MiddlewareHandler:
    """Manages middleware registration for Robyn."""

    def __init__(self, app: object) -> None:
        self._app = app
        self._middlewares: list[BaseMiddleware] = []

    def register(self, middleware_cls: type[BaseMiddleware]) -> "MiddlewareHandler":
        self._middlewares.append(middleware_cls())
        return self

    def apply(self) -> None:
        for mw in self._middlewares:
            self._app.before_request(mw.endpoints)(mw.before)
            self._app.after_request(mw.endpoints)(mw.after)
```

### events/process_pool.py — ProcessPool Event

```python
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

from app.core.lifespan import BaseEvent
from app.core.settings import settings as st


class ProcessPoolEvent(BaseEvent[ProcessPoolExecutor]):
    """Manages ProcessPoolExecutor lifecycle."""

    async def startup(self) -> ProcessPoolExecutor:
        ctx = get_context("spawn")
        return ProcessPoolExecutor(max_workers=st.MAX_WORKERS, mp_context=ctx)

    async def shutdown(self, pool: ProcessPoolExecutor) -> None:
        pool.shutdown(wait=False, cancel_futures=True)
```

### core/settings.py — Settings

```python
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.helpers import read_pyproject, get_version


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEBUG: bool = True
    ENVIRONMENT: Literal["DEV", "PROD"] = "DEV"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    MAX_WORKERS: int = 4

    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    PROJECT: ClassVar[dict] = read_pyproject(BASE_DIR / "pyproject.toml")
    API_NAME: ClassVar[str] = PROJECT.get("project", {}).get("name", "api")
    API_VERSION: ClassVar[str] = get_version(BASE_DIR)
    DATA_PATH: ClassVar[Path] = BASE_DIR / "data"
    MODELS_PATH: ClassVar[Path] = DATA_PATH / "models"

    @computed_field
    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "DEV"


settings = Settings()
```

### api/health.py — Health Endpoint

```python
from pydantic import BaseModel

from app.core.router import Router

router = Router(__file__, prefix="/api/v1")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


@router.get("/health")
async def health() -> HealthResponse:
    from app.core.settings import settings as st
    return HealthResponse(version=st.API_VERSION)
```

## Key Conventions

- **Robyn framework**: Rust-backed, high-throughput HTTP
- **Custom Router**: auto body parsing (Pydantic, dict, files) + auto response serialization
- **Event-driven lifespan**: `BaseEvent[T]` for typed startup/shutdown resources
- **State injection**: `app.inject_global(state=...)` for DI
- **Middleware ABC**: `BaseMiddleware` with `before()`/`after()` hooks
- **ProcessPool**: spawn context for ML model inference in separate processes
- **orjson**: mandatory for all JSON ops
- **No `__init__.py`**: implicit namespace packages
- **`[ml]` optional deps**: numpy, scikit-learn separated from core

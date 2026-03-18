---
name: architecture
description: Architecture patterns and reference implementations. Multi-inheritance, generics, type-hint DI, adapters, pipelines, factories, concurrency, multiple dispatch, class decorators. Use when designing features, modules, stores, or pipelines.
---

# Architecture Patterns

## Multi-Inheritance Composition

Settings — compose from domain config modules:

```python
import tomllib
from pathlib import Path
from typing import ClassVar, Literal

import glom
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.core import Settings as CoreSettings
from app.config.api import Settings as ApiSettings

def read_pyproject(pyproject_path: Path) -> dict:
    with pyproject_path.open("rb") as fh:
        return tomllib.load(fh)

class Settings(CoreSettings, ApiSettings):
    ENVIRONMENT: Literal["PROD", "DEV"] = "PROD"
    SYSTEM_BASE_DIR: ClassVar[Path] = CoreSettings().BASE_DIR
    SYSTEM_PROJECT: ClassVar[dict] = read_pyproject(SYSTEM_BASE_DIR / "pyproject.toml")
    SYSTEM_API_NAME: ClassVar[str] = glom.glom(SYSTEM_PROJECT, "project.name")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

ClassVar prevents env var lookup. Import as: `from app.core.settings import settings as st`.

Store — CRUD + vector ops:

```python
from beartype import beartype
from app.core.helpers import decorate_methods

@decorate_methods(beartype)
class BaseStore[D: Node]:
    __slots__ = ("_redis", "_schema", "_ttl")
    def __init__(self, redis: AsyncRedis, schema: SearchIndexSchema[D], ttl: int):
        self._redis, self._schema, self._ttl = redis, schema, ttl

@decorate_methods(beartype)
class NodeStore[D: Node](BaseStore[D]):
    __slots__ = ()

@decorate_methods(beartype)
class IndexStore[D: Node](BaseStore[D]):
    __slots__ = ("_index", "_embed")

@decorate_methods(beartype)
class KnowledgeStore[D: Node](NodeStore[D], IndexStore[D]):
    __slots__ = ()
```

Models — cross-hierarchy: `class ScoredEntity(Entity, ScoredNode): ...`

## Generics & Type-Safe Layering

Generic classes parameterized by node type. Propagate through: schema → store → pipeline → API.

```python
class BaseStore[D: Node]:
    __slots__ = ("_redis", "_schema", "_ttl")
```

## Type-Hint Auto-Wiring

Introspect signatures to auto-inject dependencies by type:

```python
from functools import partial, update_wrapper
from typing import get_type_hints
import inspect

def _wire_conditions(conditions: list[Callable], dependency_map: dict[type, Any]) -> list[Callable]:
    wired = []
    for func in conditions:
        hints = get_type_hints(func)
        sig = inspect.signature(func).parameters
        injects = {n: dependency_map[hints[n]] for n in sig if n in hints and hints[n] in dependency_map}
        if injects:
            w = partial(func, **injects)
            update_wrapper(w, func)
            wired.append(w)
        else:
            wired.append(func)
    return wired
```

For FastAPI Depends() chains → see fastapi skill.

## Adapter Pattern

Choose the adapter style based on **service complexity**. The decision is about how much state the adapter must hold and how many operations it exposes.

### Decision

| Criteria | → Style |
|----------|---------|
| 1-2 focused methods, config-only deps, no shared state | Async context manager (ephemeral client) |
| Many methods sharing client, retry/auth/middleware state, lifecycle management | Instance-held client (long-lived) |

### Ephemeral — async context manager

For adapters with few concrete methods and no complex state. The client lives only for the call. No `__init__` client, no `close()`.

```python
class SearXNGAdapter:
    """Lightweight adapter — few methods, config-only deps."""

    __slots__ = ("_base_url", "_timeout", "_headers")

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self._base_url = base_url
        self._timeout = httpx.Timeout(timeout)
        self._headers = {"Accept": "application/json"}

    async def query(self, query: str, *, categories: str = "general", max_results: int = 5) -> str:
        async with httpx.AsyncClient(
            base_url=self._base_url, timeout=self._timeout, headers=self._headers,
        ) as client:
            response = await client.get("/search", params={"q": query, "format": "json", "categories": categories})
            response.raise_for_status()
            data: dict[str, Any] = orjson.loads(response.content)
            return _format_results(data, max_results)
```

No `close()` needed — the client is scoped to the call. Config is stored, client is not.

### Persistent — instance-held client

For complex adapters with many methods, retry transport, auth state, healthcheck, or connection pooling. Lazy init with explicit lifecycle:

```python
class NLPRuntimeAdapter:
    """Complex adapter — many methods, shared client, retry, healthcheck."""

    __slots__ = ("_client", "_base_url")

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                transport=RetryTransport(max_retries=3),
            )
        return self._client

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        client = await self._get_client()
        response = await client.post("/rerank", json={"query": query, "documents": documents})
        response.raise_for_status()
        return orjson.loads(response.content)["scores"]

    async def categorize(self, text: str) -> list[Entity]:
        client = await self._get_client()
        response = await client.post("/categorize", json={"text": text})
        response.raise_for_status()
        return [Entity(**e) for e in orjson.loads(response.content)["entities"]]

    async def health(self) -> bool:
        client = await self._get_client()
        response = await client.get("/health")
        return response.status_code == 200

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
```

Justified because: many methods share the client, retry transport needs reuse, lazy init avoids startup cost, explicit lifecycle for lifespan management.

## Pipeline Pattern

```python
@dataclass
class Pipeline[T_in, T_out]:
    preprocessors: list[Processor[T_in]]
    postprocessors: list[Processor[T_out]]
    conditions: list[Callable[..., bool]]

    async def execute(self, data: T_in) -> T_out:
        for proc in self.preprocessors:
            data = await proc._preprocess(data)
        result = await self._core(data)
        for proc in self.postprocessors:
            result = await proc._postprocess(result)
        return result
```

## Factory Pattern

```python
class SessionFactory:
    __slots__ = ("_redis",)
    def __init__(self, redis: AsyncRedis):
        self._redis = redis
    async def create(self, tenant_id: str, session_id: str) -> Session: ...
```

## Concurrency

```python
# parallel I/O
results = await asyncio.gather(store.node_create(node), store.index_add(node))

# bounded concurrency
semaphore = asyncio.Semaphore(10)
async with semaphore:
    await process_request(data)

# redis pipeline
async with redis.pipeline() as pipe:
    pipe.hset(key, mapping=data)
    pipe.hexpire(key, ttl, *fields)
    await pipe.execute()
```

## Data Flow

Pydantic models at every boundary. Namespace isolation via tenant key prefixing `t:{tenant_id}:vec:`.

```
Request → Headers → Session → Schema → Store → Redis
                                          ↓
                              Pipeline → Processors → Response
```

## Multiple Dispatch (OVLD)

Runtime dispatch, not typing.overload:

```python
from ovld import ovld
from typing import Literal

@ovld
def build_query(query_type: Literal["vector"], text: str, vector: list[float]) -> VectorQuery:
    return VectorQuery(...)

@ovld
def build_query(query_type: Literal["hybrid"], text: str, vector: list[float]) -> HybridQuery:
    return HybridQuery(...)
```

Suppress in pyproject.toml: `[tool.ty.rules]` → `useless-overload-body = "ignore"`, `invalid-overload = "ignore"`.

## decorate_methods

Apply a decorator to all non-dunder methods of a class:

```python
import inspect
from typing import Any, Callable

type C = type

def decorate_methods(
    decorator: Callable[..., Any],
    *,
    skip: frozenset[str] = frozenset({"__init__", "__new__", "__del__"}),
) -> Callable[[C], C]:
    def class_wrapper(cls: C) -> C:
        for name, value in list(vars(cls).items()):
            if name.startswith("__") or name in skip:
                continue
            if isinstance(value, (property, staticmethod, classmethod)):
                continue
            if inspect.isfunction(value):
                setattr(cls, name, decorator(value))
        return cls
    return class_wrapper
```

Primary usage: `@decorate_methods(beartype)` for runtime type enforcement.

---
name: fastapi
description: FastAPI application patterns. Lifespan, middleware, DI chains, exception handling, structured logging. Use when working with FastAPI routers, middleware, exceptions, or lifecycle.
---

# FastAPI Patterns

## Lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = await RedisConnection.get()
    app.state.redis = redis
    app.state.embed = AzureOpenAITextVectorizer(...)
    scheduler = AsyncIOScheduler()
    scheduler.start()
    yield
    if (s := getattr(app.state, "scheduler", None)) is not None:
        s.shutdown(wait=True)
    if (r := getattr(app.state, "redis", None)) is not None:
        await r.client.close()
```

Walrus (:=) for cleanup null-checks. All state on app.state. Scheduler via APScheduler.

## Middleware

```python
all_middlewares = [
    {"middleware": RequestTimerMiddleware, "kwargs": {}},
    {"middleware": CorrelationIdMiddleware, "kwargs": {"header_name": "x-irius-traceid"}},
    {"middleware": CORSMiddleware, "kwargs": {"allow_origins": st.CORS_ORIGINS}},
]

for middleware in all_middlewares:
    app.add_middleware(middleware["middleware"], **middleware["kwargs"])
```

## DI Chains

Depends() chaining: headers → session → schema → store.

```python
async def get_tenant_id(x_haven_tenant_id: str = Header()) -> str:
    return x_haven_tenant_id

async def get_session(
    tenant_id: str = Depends(get_tenant_id),
    session_id: str = Header(alias="x-haven-session-id"),
    redis: AsyncRedis = Depends(get_redis),
) -> Session:
    return await SessionFactory(redis).create(tenant_id, session_id)

async def get_store(session: Session = Depends(get_session)) -> KnowledgeStore:
    return session.store
```

Chain linearly: simple → complex. Never bypass (no direct Redis in routers).

## Exception Handling

Hierarchy:

```
BaseException
├── BusinessLogicError       (400)
├── TenantLockError          (409)
├── ConfigurationError       (500)
├── ExternalServiceError     (502)
├── VectorStoreError         (500)
└── RetrieverError           (500)
```

Implementation:

```python
from enum import StrEnum
from fastapi import status

class ErrorTitles(StrEnum):
    INTERNAL_SERVER_ERROR = "Internal Server Error"
    BAD_REQUEST = "Bad Request"
    CONFLICT = "Conflict"
    BAD_GATEWAY = "Bad Gateway"

class BaseException(Exception):
    def __init__(self, *args, message: str | None = None,
                 status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
                 title: str | None = None, **kwargs):
        self.message = args[0] if args else message
        self.status_code = status_code
        self.title = title or ErrorTitles.INTERNAL_SERVER_ERROR
        super().__init__(self.message)

class BusinessLogicError(BaseException):
    def __init__(self, message: str, title: str | None = None, **kwargs):
        kwargs.setdefault("status_code", status.HTTP_400_BAD_REQUEST)
        super().__init__(message, title=title or ErrorTitles.BAD_REQUEST, **kwargs)
```

Auto-collection and registration:

```python
all_exceptions = [
    obj for obj in globals().values()
    if isinstance(obj, type) and issubclass(obj, BaseException) and obj is not BaseException
]

for exc in all_exceptions:
    app.add_exception_handler(exc, structured_error_handler)
```

Response format: `{"type": "...", "status": N, "title": "...", "detail": "...", "traceId": "..."}`.

## Structured Logging

TrackerLogger extending logging.Logger with @logger.automate decorator:
- Auto-times method execution
- Extracts extra context from args/self
- Supports sync, async, async-generators

Log format — emoji + UPPERCASE_EVENT, context in extra={}:

```python
logger.info("📦 INDEX_CREATED", extra={"index": name})
logger.info("✅ INGEST_COMPLETE", extra={"doc_count": n})
logger.warning("⚠️ TTL_EXPIRED", extra={"key": key, "tenant": tenant_id})
logger.error("❌ STORE_ERROR", extra={"error": str(e), "operation": "search"})
```

PROD: python-json-logger (JSON). DEV: rich.logging.RichHandler (pretty).
Correlation ID via asgi-correlation-id — auto-attached to all logs.

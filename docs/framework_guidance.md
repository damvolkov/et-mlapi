# Framework Guidance

> Instructions for AI agents and human developers building on the **et-mlapi** template.

---

## Overview

**et-mlapi** is a production-ready ML API template built on [Robyn](https://robyn.tech) — a Rust-backed, async-first Python web framework.  The template wraps Robyn with a declarative layer that brings Pydantic-powered routing, typed WebSockets, middleware chains, and event-driven lifecycle management.

The documentation is generated with **MkDocs Material** (the style used by FastAPI, Pydantic, and the modern Python ecosystem).  All public classes and functions use Google-style docstrings so they render correctly in `mkdocstrings`.

---

## Architecture at a Glance

```
src/et_mlapi/
├── main.py              # Entrypoint — assembles app, registers everything
├── core/                # Framework infrastructure (DO NOT put business logic here)
│   ├── settings.py      # YAML-based pydantic-settings, singleton `settings`
│   ├── logger.py        # structlog with ANSI color renderer
│   ├── lifespan.py      # Event-based startup/shutdown lifecycle
│   ├── router.py        # Enhanced Router with auto body/file parsing
│   └── websocket.py     # Declarative WebSocket architecture
├── api/                 # HTTP route handlers (one file per resource)
│   ├── health.py
│   └── sample.py        # Demonstrates HTTP, SSE, streaming transports
├── websockets/          # WebSocket endpoint definitions
│   └── sample.py        # Demonstrates echo/upper/reverse actions
├── models/              # Pydantic schemas (request, response, domain)
│   ├── core.py          # BodyType enum, UploadFile container
│   ├── api.py           # Transport-specific request/response models
│   └── error.py         # Error response models and factory
├── adapters/            # External service clients
│   ├── base.py          # BaseAdapter ABC
│   └── sample.py        # httpx-based sample adapter
├── events/              # Lifespan events (startup/shutdown resources)
│   ├── process_pool.py  # ProcessPoolExecutor lifecycle
│   └── sample_adapter.py
├── middlewares/          # Before/after request hooks
│   ├── base.py          # BaseMiddleware ABC + MiddlewareHandler
│   ├── files.py         # OpenAPI multipart patching
│   └── swagger.py       # Swagger UI branding
└── data/config/
    └── config.yaml      # Runtime configuration (YAML)
```

---

## Registration Pattern — Lazy & Explicit

The template uses **explicit registration** in `main.py` — no decorators that couple modules to the app instance.  Components are defined independently and registered centrally.

### Routers

```python
# api/my_resource.py — knows NOTHING about the app
from et_mlapi.core.router import Router

router = Router(__file__, prefix="/my-resource")

@router.get("/items")
async def list_items() -> list[dict]:
    return [{"id": 1}]

# main.py — the ONLY place that knows about the app
from et_mlapi.api.my_resource import router as my_resource_router
app.include_router(my_resource_router)
```

### WebSockets

```python
# websockets/my_ws.py — knows NOTHING about the app
from et_mlapi.core.websocket import BaseWebSocket

ws_my = BaseWebSocket("/ws/my")

@ws_my.on("message")
async def on_message(ws, msg: str) -> str:
    return msg.upper()

# main.py
from et_mlapi.websockets.my_ws import ws_my
websockets = WebSocketHandler(app)
websockets.register(ws_my)
```

### Lifespan Events

```python
# events/my_service.py
from et_mlapi.core.lifespan import BaseEvent

class MyServiceEvent(BaseEvent[MyService]):
    name = "my_service"

    async def startup(self) -> MyService:
        svc = MyService()
        await svc.connect()
        return svc

    async def shutdown(self, instance: MyService) -> None:
        await instance.disconnect()

# main.py
lifespan.register(MyServiceEvent)
```

After startup, the service is available as `state.my_service` in any handler that receives the injected `state` dependency.

### Middlewares

```python
# middlewares/cors.py
from et_mlapi.middlewares.base import BaseMiddleware

class CORSMiddleware(BaseMiddleware):
    def before(self, request):
        return request

    def after(self, response):
        response.headers["access-control-allow-origin"] = "*"
        return response

# main.py
middlewares = MiddlewareHandler(app)
middlewares.register(CORSMiddleware)
```

---

## The Router — How It Works

`et_mlapi.core.router.Router` extends Robyn's `SubRouter` with automatic:

1. **Body parsing** — Pydantic models in the handler signature are auto-validated from JSON.  `dict` parameters are parsed as raw JSON.  `UploadFile` parameters extract multipart files.
2. **Path parameters** — `:param_name` in the route path is matched against handler parameters.
3. **Response serialization** — Return a `BaseModel`, `dict`, `str`, `Response`, or `StreamingResponse` and the router converts it to a proper `Response` with correct headers.
4. **Aliases** — `router.alias("/original", "/alt1", "/alt2")` registers the same handler on multiple paths without re-wrapping.

### Signature introspection

The router inspects `inspect.Signature` of your handler at **registration time** (not per-request).  It classifies parameters as:

| Annotation | Classification | Parsing |
|---|---|---|
| `BaseModel` subclass | `BodyType.PYDANTIC` | `model_validate_json(raw)` with 422 on `ValidationError` |
| `dict` | `BodyType.JSONABLE` | `orjson.loads(raw)` with 422 on `JSONDecodeError` |
| `UploadFile` | File parameter | `request.files` extraction |
| `request` (name) | Raw Robyn `Request` | Passed through |
| Path param (`:name`) | Path parameter | Extracted from `PathParams` |

---

## Transport Types

The template supports four transports out of the box:

| Transport | Protocol | Use case | Example endpoint |
|---|---|---|---|
| **HTTP** | Request → Response | Standard JSON APIs | `POST /sample/http` |
| **SSE** | Server-Sent Events | Real-time push (one-way) | `GET /sample/sse` |
| **Streaming** | Chunked NDJSON | Progressive data delivery | `POST /sample/stream` |
| **WebSocket** | Bidirectional | Real-time bidirectional | `ws://host/ws/sample` |

### SSE / Streaming

Return a `StreamingResponse` with an async generator:

```python
from robyn import StreamingResponse

async def generate():
    for i in range(10):
        yield f"data: {i}\n\n"

return StreamingResponse(
    content=generate(),
    status_code=200,
    headers={"content-type": "text/event-stream"},
)
```

---

## Settings — YAML Configuration

Settings use `pydantic-settings` with the YAML plugin.  The configuration file lives at `data/config/config.yaml`.

```yaml
system:
  debug: true
  environment: dev
  host: "0.0.0.0"
  port: 8012
  max_workers: 4
```

To add a new config section:

1. Create a `BaseModel` subclass in `core/settings.py`.
2. Add it as a field on `Settings`.
3. Add the corresponding YAML section to `config.yaml`.

```python
class DatabaseConfig(BaseModel):
    url: str = "redis://localhost:6379"
    pool_size: int = 10

class Settings(BaseSettings):
    system: SystemConfig = SystemConfig()
    database: DatabaseConfig = DatabaseConfig()  # new section
```

---

## Adapters — External Service Clients

Adapters wrap external HTTP/gRPC/WebSocket services.  They follow a strict lifecycle:

1. Implement `BaseAdapter` with `startup()`, `shutdown()`, and `health()`.
2. Create a `BaseEvent` subclass that instantiates the adapter on startup.
3. Register the event in `main.py`.
4. Access the adapter via `state.adapter_name` in your handlers.

---

## Logging

The logger uses `structlog` with an ANSI color renderer for development.  Log calls use a `step` keyword to categorize the log visually:

```python
from et_mlapi.core.logger import logger

logger.info("processing request", step="HTTP", path="/api/data")
logger.error("connection failed", step="ERROR", service="redis")
```

Available steps: `START`, `STOP`, `OK`, `HTTP`, `WS`, `SSE`, `STREAM`, `ADAPTER`, `MODEL`, `DOWNLOAD`, `ERROR`, `WARN`.

---

## Testing

### Unit tests

```bash
make test          # or: uv run pytest tests/unit -n auto -v --cov
```

Unit tests mock all external dependencies.  Coverage target: **>90%**.

### Integration tests

```bash
make test-integration   # or: uv run pytest tests/integration -v -m slow
```

Integration tests use a **session-scoped server fixture** that starts the real Robyn app on a random port:

```python
@pytest.fixture(scope="session")
def mlapi_server():
    port = _find_free_port()
    process = multiprocessing.Process(target=_run_server, args=(port,), daemon=True)
    process.start()
    # ... wait for health check ...
    yield {"base_url": base_url, "host": host, "port": port}
    process.terminate()
```

---

## Docker

```bash
make docker-up      # Build + start on :8012
make docker-down    # Stop
```

The Dockerfile uses a multi-stage build with `uv` for fast, reproducible installs.  The `data/config/` directory is mounted as a volume so configuration can be changed without rebuilding.

---

## CI/CD

GitHub Actions runs on every push/PR to `main`:

| Job | Description | Condition |
|---|---|---|
| **Lint** | `ruff check` + `ruff format --check` | Always |
| **Type Check** | `ty check` (Astral Rust type checker) | Always |
| **Unit Tests** | `pytest tests/unit -n auto --cov` | Always |
| **Integration Tests** | `pytest tests/integration -m slow` | Always |
| **Docker Build** | Build image (no push by default) | `DOCKER_PUBLISH == 'true'` |

### Enabling Docker builds in CI

The Docker build job is **disabled by default**.  To enable it:

1. Go to **GitHub → Settings → Secrets and variables → Actions → Variables**
2. Create a new **repository variable**: `DOCKER_PUBLISH` = `true`

This is a GitHub Actions **repository variable** (not a secret), configured via `vars.DOCKER_PUBLISH` in the workflow.  When set to `true`, the Docker job runs after lint + typecheck + unit tests pass.

To push images to GHCR, extend the Docker job with `docker/login-action` and set `push: true`.

---

## Adding a New Feature — Checklist

1. **Models** — Define request/response schemas in `models/`.
2. **Adapter** (if external) — Implement in `adapters/`, create event in `events/`.
3. **Route handler** — Create router in `api/` or WebSocket in `websockets/`.
4. **Register** — Add to `main.py`: router, event, middleware.
5. **Config** (if needed) — Add section to `config.yaml` and `Settings`.
6. **Tests** — Unit tests in `tests/unit/`, integration in `tests/integration/`.
7. **Docstrings** — Google-style for MkDocs generation.

---

## Documentation Style

All documentation is designed for **MkDocs Material** with `mkdocstrings`.  Follow these rules:

- **Google-style docstrings** on all public classes and functions.
- `Args:` section for parameters, `Returns:` for return values.
- `Attributes:` section on classes for public fields.
- `Raises:` section when exceptions are explicitly raised.
- Keep docstrings concise — one-liner for trivial items, full block for complex ones.

```python
class BaseEvent[T](ABC):
    """Abstract base class for lifespan events.

    Subclass this to define startup/shutdown behavior for resources
    that need to be initialized when the application starts and
    cleaned up when it stops.

    Attributes:
        name: Unique identifier used as the key in app state.
        state: Reference to the shared application state container.
    """
```

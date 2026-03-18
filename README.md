<p align="center">
  <img src="assets/eager.png" alt="et-mlapi" width="200">
</p>

<h1 align="center">et-mlapi</h1>

<p align="center">
  <strong>Production-ready ML API template</strong> — Robyn + Pydantic + WebSockets + SSE + Streaming
</p>

<p align="center">
  <em>Part of the <strong>Eager Templates</strong> series by <a href="https://github.com/damvolkov">Damien Volkov</a></em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#transports">Transports</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#development">Development</a> •
  <a href="docs/framework_guidance.md">Framework Guide</a>
</p>

---

## What is this?

**et-mlapi** is a batteries-included template for building Machine Learning and AI APIs.  It wraps [Robyn](https://robyn.tech) (a Rust-backed async Python framework) with a declarative layer that brings:

- **Pydantic-powered routing** — auto body parsing, validation, and response serialization
- **Four transport types** — HTTP, SSE, Streaming, WebSockets
- **Event-driven lifecycle** — typed startup/shutdown events for ML models, pools, and connections
- **Middleware chains** — before/after hooks with endpoint filtering
- **YAML configuration** — typed settings via `pydantic-settings` with YAML plugin
- **Adapter pattern** — structured external service integration with health checks

> **Eager Templates** (`et-*`) are production-ready project starters designed for ML/AI services.  They prioritize type safety, async performance, and clean architecture.

---

## Features

| Feature | Description |
|---|---|
| **Custom Router** | Auto body/file parsing, path params, Pydantic validation, response serialization |
| **WebSockets** | Declarative `BaseWebSocket` with connect/message/close handlers and DI |
| **SSE & Streaming** | `StreamingResponse` support for real-time push and progressive delivery |
| **Lifespan Events** | Generic `BaseEvent[T]` with typed startup/shutdown and state injection |
| **Middleware System** | `BaseMiddleware` ABC with `__init_subclass__` enforcement and chainable registration |
| **Adapter Pattern** | `BaseAdapter` ABC for external services with health checks |
| **YAML Config** | `pydantic-settings` with YAML plugin — typed sub-models, no raw `os.environ` |
| **Structured Logging** | `structlog` with ANSI color renderer, step-based categorization |
| **Docker** | Multi-stage build with `uv`, config volumes, health checks |
| **CI/CD** | GitHub Actions — lint, typecheck, unit tests, integration tests, Docker build |
| **Testing** | `pytest` + `pytest-asyncio` + `pytest-cov` + `pytest-xdist` — 90%+ coverage |

---

## Quick Start

```bash
# Clone
git clone <your-repo-url>
cd et-mlapi

# Install
make install

# Run
make dev
# API: http://localhost:8012
# Docs: http://localhost:8012/docs
```

### Test the endpoints

```bash
# Health
curl http://localhost:8012/health

# HTTP POST
curl -X POST http://localhost:8012/sample/http \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello world", "repeat": 3}'

# SSE
curl http://localhost:8012/sample/sse
```

---

## Transports

| Transport | Protocol | Endpoint | Use case |
|---|---|---|---|
| **HTTP** | JSON request/response | `POST /sample/http` | Standard APIs |
| **SSE** | Server-Sent Events | `GET /sample/sse` | Real-time push |
| **Streaming** | Chunked NDJSON | `POST /sample/stream` | Progressive delivery |
| **WebSocket** | Bidirectional | `ws://host/ws/sample` | Real-time bidirectional |

---

## Architecture

```
src/et_mlapi/
├── main.py              # Entrypoint — registers routers, events, middlewares, websockets
├── core/                # Framework infrastructure
│   ├── settings.py      # YAML-based pydantic-settings
│   ├── logger.py        # structlog with ANSI colors
│   ├── lifespan.py      # Event-based startup/shutdown
│   ├── router.py        # Enhanced Router with auto parsing
│   └── websocket.py     # Declarative WebSocket system
├── api/                 # HTTP route handlers
├── websockets/          # WebSocket endpoint definitions
├── models/              # Pydantic schemas
├── adapters/            # External service clients
├── events/              # Lifespan events
└── middlewares/          # Before/after request hooks
```

See [docs/framework_guidance.md](docs/framework_guidance.md) for the full framework guide.

---

## Development

```bash
make install          # Install deps + pre-commit
make dev              # Dev server with reload
make lint             # Ruff check + format
make type             # ty type checker
make test             # Unit tests with coverage
make test-integration # Integration tests
make check            # lint + type + test
make docker-up        # Docker build + run
make clean            # Remove caches
```

---

## Configuration

Settings are loaded from `data/config/config.yaml`:

```yaml
system:
  debug: true
  environment: dev
  host: "0.0.0.0"
  port: 8012
  max_workers: 4
```

Add new sections by creating `BaseModel` sub-configs in `core/settings.py`.

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

| Job | Description |
|---|---|
| **Lint** | `ruff check` + `ruff format --check` |
| **Type Check** | `ty check` (Astral Rust type checker) |
| **Unit Tests** | `pytest tests/unit` with coverage (>90%) |
| **Integration Tests** | `pytest tests/integration -m slow` |
| **Docker Build** | Conditional — only runs when enabled |

### Enabling Docker publish

The Docker build job is **disabled by default**.  To enable it, create a **GitHub repository variable**:

1. Go to **Settings → Secrets and variables → Actions → Variables**
2. Create a new repository variable: `DOCKER_PUBLISH` = `true`

When `DOCKER_PUBLISH` is set to `true`, the CI will build the Docker image after lint + typecheck + unit tests pass.  To push to GHCR, add a `docker/login-action` step with a `GITHUB_TOKEN` or PAT.

---

## Pre-commit hooks

The pre-commit configuration runs the same quality checks locally:

| Hook | Description |
|---|---|
| `ruff` | Lint with auto-fix |
| `ruff-format` | Code formatting |
| `ty-check` | Type checking |
| `pytest-unit` | Unit tests with coverage |
| `gitleaks` | Secret scanning |

---

## License

MIT License

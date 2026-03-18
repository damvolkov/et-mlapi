---
name: testing-mocking
description: Mocking patterns. Test clients, mock libraries, pytest-httpserver, respx, custom mock servers, factory fixtures, live service tests. Use when mocking services or building test infrastructure.
---

# Mocking & Test Infrastructure

## Resolution Hierarchy

When you need to test against an external dependency, follow this resolution order. **Never skip a level.**

### Level 1 — Framework Test Client

Use the framework's own test tooling. It handles middleware, routing, DI, and lifecycle correctly.

```python
# FastAPI — httpx.ASGITransport (async)
from httpx import ASGITransport, AsyncClient

@pytest.fixture(scope="session")
async def http_client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await client.aclose()

async def test_health_endpoint_returns_ok(http_client: AsyncClient) -> None:
    response = await http_client.get("/health")
    assert response.status_code == 200
```

If the framework has no test client, search for one. If nothing exists, build a minimal one that wraps the ASGI/WSGI app.

### Level 2 — Purpose-Built Mock Library

For third-party services, search for a dedicated mock library BEFORE writing custom mocks:

| Service | Mock library | Scope | Notes |
|---------|-------------|-------|-------|
| Redis | `fakeredis` | unit | Drop-in `FakeRedis(decode_responses=True)` |
| HTTP (real mock server) | `pytest-httpserver` | unit | Werkzeug-based, function-scoped, random port |
| HTTP (transport mock) | `respx` | integration | httpx transport-level, no real server |
| HTTP (alternative) | `pytest-httpx` | unit/integration | httpx mock, simpler API |
| S3 / MinIO | `moto` | unit | `@mock_aws` decorator |
| PostgreSQL | `pytest-postgresql` | unit | Managed temp DB |
| MongoDB | `mongomock` | unit | Drop-in client replacement |

Always explore PyPI and GitHub for `fake-*`, `pytest-*`, `mock-*` packages. Only proceed to Level 3 when nothing viable exists.

### Level 3 — Custom Mock Server

When no library exists (proprietary APIs, niche protocols, custom gRPC/GraphQL/WebSocket), build a minimal mock server that returns **expected output shapes** for your business logic to parse.

**Principles:**
- Only produce realistic output your code will parse. No real business logic.
- Lives in conftest as a fixture (session or module scope).
- Must be deterministic and fast.

```python
from aiohttp import web

async def _nlp_handler(request: web.Request) -> web.Response:
    body = await request.json()
    return web.json_response({
        "entities": [{"text": body["text"][:20], "label": "ORG", "score": 0.95}],
        "language": "en",
    })

@pytest.fixture(scope="session")
async def nlp_mock_server() -> AsyncGenerator[str]:
    app = web.Application()
    app.router.add_post("/analyze", _nlp_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://localhost:{port}"
    await runner.cleanup()
```

## pytest-httpserver — Unit Test Mock Server

For unit tests that need a real HTTP server on a random port. The `httpserver` fixture is function-scoped (fresh per test).

### create_mock_server helper

Reusable function in conftest for configuring endpoints:

```python
from pytest_httpserver import HTTPServer

def create_mock_server(
    httpserver: HTTPServer,
    *,
    path: str,
    data: dict[str, Any],
    status: int = 200,
) -> HTTPServer:
    """Configure a mock endpoint on the given server."""
    httpserver.expect_request(path).respond_with_json(data, status=status)
    return httpserver
```

### Factory Fixtures — Mock External Services

Each external service mock is a **factory fixture** that returns a callable. The callable configures the mock server and returns the generated fake data for assertion:

```python
@pytest.fixture
def mock_searxng(httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch) -> Callable[..., SearxSearchResponse]:
    """Factory fixture: configure SearXNG mock on /search endpoint."""
    monkeypatch.setattr(SearXNGAdapter, "_BASE_URL", httpserver.url_for(""))

    def _setup(*, num_results: int = 3, status: int = 200) -> SearxSearchResponse:
        fake = SearxSearchResponseFactory.build(
            results=SearxResultResponseFactory.batch(num_results),
        )
        create_mock_server(httpserver, path="/search", data=fake.model_dump(mode="json"), status=status)
        return fake

    return _setup
```

Key patterns:
- `monkeypatch.setattr` redirects adapter's `_BASE_URL` to `httpserver.url_for("")` (random port).
- Fixture returns a **callable** — each test controls the number of results and HTTP status.
- Callable returns the **fake data object** — tests assert against expected values.
- `pytest-httpserver` provides `httpserver` automatically (function-scoped, fresh per test).

### Usage

```python
async def test_query_returns_search_responses(mock_searxng) -> None:
    mock_searxng(num_results=3)
    results = await SearXNGAdapter.query("test")
    assert len(results) == 3

async def test_query_maps_factory_data(mock_searxng) -> None:
    fake = mock_searxng(num_results=1)
    results = await SearXNGAdapter.query("test")
    assert results[0].title == fake.results[0].title
```

### Direct httpserver access

For tests needing custom response shapes not covered by factory fixtures:

```python
async def test_query_truncates_long_snippets(
    httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(SearXNGAdapter, "_BASE_URL", httpserver.url_for(""))
    long_result = SearxResultResponseFactory.build(content="x" * 500)
    httpserver.expect_request("/search").respond_with_json(
        {"results": [long_result.model_dump(mode="json")]},
    )
    results = await SearXNGAdapter.query("test", max_results=1)
    assert len(results[0].snippet) == 200
```

## respx — Integration Transport Mocking

For integration tests that mock at the httpx transport level (no real server):

```python
import respx
import httpx
import orjson

_FAKE_RESPONSE: dict[str, Any] = {
    "results": [
        {"title": "Python docs", "url": "https://docs.python.org", "content": "Official docs."},
    ],
}

def _mock_search(data: dict[str, Any], status: int = 200) -> respx.Route:
    return respx.route(method="GET", path="/search").mock(
        return_value=httpx.Response(status, content=orjson.dumps(data)),
    )

@respx.mock
async def test_query_returns_search_results() -> None:
    _mock_search(_FAKE_RESPONSE)
    results = await SearXNGAdapter.query("python")
    assert len(results) == 1
```

Key rules:
- `@respx.mock` decorator on each test function.
- Match by `path="/search"` (NOT full URL — avoids trailing-slash issues).
- Module-level helper `_mock_search(data, status)` per service to avoid repetition.
- Use `route.calls[0].request.url.params[...]` to assert query parameters.

## Live Service Tests

Tests that hit real external services are marked `@pytest.mark.slow` and excluded by default:

```python
@pytest.mark.slow
async def test_query_live_searxng() -> None:
    """Hit real SearXNG — requires service on SEARXNG_URL."""
    results = await SearXNGAdapter.query("python programming", max_results=3)
    assert isinstance(results, list)
    assert all(isinstance(r, SearchResponse) for r in results)
    assert len(results) <= 3
```

Run with: `uv run python -m pytest -m slow -v`

## Strategy by Layer

| Layer | Unit test | Integration test |
|-------|-----------|-----------------|
| Own API (FastAPI, Robyn) | — | `ASGITransport` / `TestClient` |
| Redis | `FakeRedis` | Real Redis (fixture with cleanup) |
| External HTTP API | `pytest-httpserver` + factory fixture | `respx` transport mock |
| Proprietary API | Custom mock server | Custom mock server |
| Database (Postgres) | `pytest-postgresql` or mock | Real DB (fixture with cleanup) |
| Embeddings | Fixed vectors `[0.1] * 768` | Real model |
| WebSocket | Custom mock server | Real server |
| File storage (S3/MinIO) | `moto` | Real MinIO (fixture) |
| Live external service | — | `@pytest.mark.slow` direct call |

## Mocker Usage

ONLY `mocker` from `pytest-mock` for patching. Never `unittest.mock` directly:

```python
async def test_adapter_fetch_retries_on_failure(mocker: MockerFixture) -> None:
    mock_response = mocker.AsyncMock(return_value={"status": "ok"})
    mocker.patch(
        "app.adapters.nlp.httpx.AsyncClient.post",
        side_effect=[httpx.HTTPError("fail"), mock_response],
    )
    result = await adapter.fetch()
    assert result == {"status": "ok"}
```

## Checklist — Adding Tests for a New Adapter

1. **`confmodels.py`**: Add `{Model}Factory` for domain models. Add `{Service}{Concept}Response` Pydantic schemas + `{Service}{Concept}ResponseFactory` for the external API.
2. **`conftest.py`**: Import from confmodels. Add a factory fixture `mock_{service}` using `create_mock_server` + `monkeypatch` to redirect `_BASE_URL`.
3. **Unit test file**: Sections for dataclass validation, class attributes, and mock server queries (using `pytest-httpserver`).
4. **Integration test file**: `@respx.mock` tests for transport-level mocking + `@pytest.mark.slow` for live service test.
5. Run `uv run python -m pytest tests/ -v --import-mode=importlib` to verify both suites pass.

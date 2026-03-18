---
name: testing
description: Testing setup. Pytest config, plugins, markers, regression, commands. Use when setting up tests or running test suites.
---

# Testing Setup

Hard rules, structure, naming, and parametrize live in `rules/N6-testing.md`. Fixture patterns in `skills/testing/fixtures`. Mocking patterns in `skills/testing/mocking`. This skill covers config, plugins, and commands.

## Config

All config in `pyproject.toml`. Never create `pytest.ini` or conftest-level config.

```toml
[tool.pytest.ini_options]
env_files = [".env"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
filterwarnings = ["ignore::DeprecationWarning"]
markers = [
    "integration: requires external services",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
addopts = "--import-mode=importlib -m 'not slow'"
```

Key points:
- `asyncio_mode = "auto"` — every test is async by default, no `@pytest.mark.asyncio` needed.
- `addopts = "-m 'not slow'"` — slow (live service) tests excluded by default.
- `--import-mode=importlib` — avoids module name collisions between unit/integration.
- Always run via `uv run python -m pytest`, never bare `pytest`.

## Mandatory Plugins

- `pytest-asyncio`: async test support.
- `pytest-mock`: `mocker` fixture. NEVER import `unittest.mock` directly.
- `pytest-xdist`: parallel execution (`-n auto`).
- `pytest-rerunfailures`: flaky test retry (`--reruns 2`).
- `pytest-cov`: coverage enforcement.
- `polyfactory`: model factories (`DataclassFactory`, `ModelFactory`). MANDATORY for data fixtures.
- `pytest-httpserver`: real mock HTTP server (werkzeug-based, function-scoped) for unit tests.
- `respx`: httpx transport-level mocking (no real server) for integration tests.
- `fakeredis`: in-memory Redis mock.

## Markers

```python
@pytest.mark.integration
async def test_knowledge_store_search_returns_results(knowledge_store) -> None:
    results = await knowledge_store.search("test query")
    assert len(results) > 0

@pytest.mark.slow
async def test_query_live_searxng() -> None:
    """Hit real SearXNG — requires service running."""
    results = await SearXNGAdapter.query("python", max_results=3)
    assert isinstance(results, list)
    assert len(results) <= 3
```

## Regression

`tests/evaluation/regression/` with polars. Run: `make regression` or `make regression ID=<id>`.

## Commands

```bash
# Unit tests only
uv run python -m pytest tests/unit/ -v

# Integration tests only (excludes @slow)
uv run python -m pytest tests/integration/ -v

# Both unit + integration
uv run python -m pytest tests/ -v --import-mode=importlib

# Live service tests only
uv run python -m pytest -m slow -v

# Single file
uv run python -m pytest tests/unit/shared/test_searxng.py -v

# With coverage
uv run python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-fail-under=90

# Parallel
uv run python -m pytest -v -n auto

# With retries
uv run python -m pytest --reruns 2 -v
```

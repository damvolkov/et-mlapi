---
name: testing-fixtures
description: Fixture patterns. Conftest ordering, confmodels.py, Polyfactory, external API schemas, resource loading. Use when writing fixtures or conftest files.
---

# Fixture Patterns

## Conftest Ordering Convention

Fixtures in every `conftest.py` MUST follow this declaration order. Sections separated by `##### SECTION #####` headers:

```python
"""Unit test fixtures for <domain> module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# confmodels import (sys.path for no-__init__.py discovery)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from confmodels import SearchResponseFactory, SearxSearchResponseFactory  # noqa: E402

##### PATHS & RESOURCES #####

_RESOURCES = Path(__file__).parents[3] / "resources" / "entities"

##### PRIVATE HELPERS #####

def _make_node(name: str = "test", score: float = 0.5) -> Node:
    return Node(name=name, score=score)

##### MOCK SERVER UTILITIES #####

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

##### FIXTURES — MOCK SERVERS #####

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

##### FIXTURES — INFRASTRUCTURE #####

@pytest.fixture(scope="session")
def fake_redis() -> FakeRedis:
    return FakeRedis(decode_responses=True)

##### FIXTURES — DATA #####

@pytest.fixture
def sample_entities() -> list[SearchResponse]:
    return SearchResponseFactory.batch(10)

@pytest.fixture(scope="module")
def match_sample_data() -> str:
    return (_RESOURCES / "match_sample.json").read_text()
```

**Order:** paths/resources → helpers → mock utilities → mock server fixtures → infrastructure → data. Always.

## confmodels.py — Factory + API Schema Definitions

Each domain test subdirectory that needs test data has a `confmodels.py` co-located with its `conftest.py`. It contains **Polyfactory factories** for domain models AND **Pydantic schemas + factories** for external API responses.

Location: `tests/unit/<package>/<domain>/confmodels.py`

### Naming Conventions

| Concept | Pattern | Example |
|---|---|---|
| Domain model factory | `{Model}Factory` | `SearchResponseFactory` |
| External API response schema | `{Service}{Concept}Response` | `SearxResultResponse`, `SearxSearchResponse` |
| External API response factory | `{Service}{Concept}ResponseFactory` | `SearxResultResponseFactory` |

### Structure

```python
"""Polyfactory factories for domain models and external API response schemas."""

from __future__ import annotations

from pydantic import BaseModel
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from e_agents.shared.models import LLMConfig, SearchResponse


##### DOMAIN MODEL FACTORIES #####


class SearchResponseFactory(DataclassFactory):
    """Factory for SearchResponse dataclass."""
    __model__ = SearchResponse


class LLMConfigFactory(ModelFactory):
    """Factory for LLMConfig pydantic model."""
    __model__ = LLMConfig


##### SEARXNG API SCHEMAS #####


class SearxResultResponse(BaseModel):
    """Raw result item as returned by the SearXNG API."""
    title: str
    url: str
    content: str
    engine: str = "google"


class SearxSearchResponse(BaseModel):
    """Raw SearXNG /search JSON response."""
    query: str
    results: list[SearxResultResponse]


##### SEARXNG API FACTORIES #####


class SearxResultResponseFactory(ModelFactory):
    """Factory for SearxResultResponse."""
    __model__ = SearxResultResponse


class SearxSearchResponseFactory(ModelFactory):
    """Factory for SearxSearchResponse."""
    __model__ = SearxSearchResponse
```

### Importing confmodels

Since test directories have no `__init__.py`, add this at the top of the corresponding `conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from confmodels import SearxSearchResponseFactory, SearxResultResponseFactory  # noqa: E402
```

Test files in the same directory can import directly: `from confmodels import SearchResponseFactory`.

## Polyfactory — MANDATORY

Every Pydantic model, dataclass, or domain object that represents data from storage or external sources MUST have a Polyfactory factory.

### Library Reference

- `polyfactory.factories.dataclass_factory.DataclassFactory` — for `@dataclasses.dataclass` models.
- `polyfactory.factories.pydantic_factory.ModelFactory` — for `pydantic.BaseModel` subclasses.
- Set `__model__` on each factory. Polyfactory auto-generates realistic random data from field types.
- Override specific fields: `Factory.build(field_name=value)`.
- Generate batches: `Factory.batch(n)`.

### Usage in Fixtures and Tests

```python
# Single instance
@pytest.fixture
def sample_entity() -> Entity:
    return EntityFactory.build()

# Batch
@pytest.fixture
def sample_entities() -> list[Entity]:
    return EntityFactory.batch(20)

# With overrides
@pytest.fixture
def high_confidence_entity() -> Entity:
    return EntityFactory.build(confidence=0.99)

# In parametrize — use factory inside the test
@pytest.mark.parametrize("category", ["organisation", "person", "location"], ids=["org", "person", "loc"])
async def test_categorize_processes_all_types(category: str) -> None:
    entity = EntityFactory.build(category=category)
    result = await categorize(entity)
    assert result.category == category
```

### Key Rules

- `build()` for unit tests (no persistence). `create()` only for integration with real storage.
- One factory per model. Polyfactory auto-generates from field types — no manual Faker providers needed.
- Factory classes go in `confmodels.py`, NOT in conftest or test modules.

## Scope Strategy

| Scope | When | Examples |
|-------|------|---------|
| `session` | Expensive, shared across ALL tests | FakeRedis, HTTP client, app instance |
| `module` | Loaded once per file | Large sample data, parsed configs |
| `function` (default) | Isolation per test | Mocks, small dicts, per-test state, factory batches |

- Scope always explicit when not `function`.
- Fixture naming: noun-based, descriptive — `fake_redis`, `sample_entity_data`, `match_sample_path`.

## Resource Loading

Large test data (JSON, audio, CSV) lives in `tests/resources/<domain>/` and is loaded via fixtures:

```python
_RESOURCES = Path(__file__).parents[3] / "resources" / "entities"

@pytest.fixture(scope="module")
def match_sample_data() -> str:
    return (_RESOURCES / "match_sample.json").read_text()

@pytest.fixture(scope="module")
def match_sample_records() -> list[dict]:
    import orjson as json
    return json.loads((_RESOURCES / "match_sample.json").read_bytes())
```

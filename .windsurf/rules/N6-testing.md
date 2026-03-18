---
description: Testing standards. Hard rules, directory structure, conftest hierarchy, naming, coverage, parametrize. Applies to all test code.
globs: "**/test*/**/*.py"
alwaysApply: false
---

# Testing Standards

Framework: `pytest` + `pytest-asyncio`. Coverage standard: **>90%** across all suites.

## Hard Rules

1. **Conftest exclusivity**: ALL shared resources — fixtures, objects, types, classes, instances, loaded files, paths, helper functions, mocks, fake services, parametrize case constants — MUST live in `conftest.py`. NEVER in test modules. Test modules contain ONLY `async def test_*` functions and file-local parametrize constants.
2. **Atomic async functions only**: Every test is `async def test_...() -> None`. NEVER test classes. NEVER sync tests.
3. **Parametrize first**: `@pytest.mark.parametrize` is the DEFAULT choice for covering multiple scenarios of the same function. Only create separate test functions when parametrize is genuinely impossible (fundamentally different setup/teardown per case).
4. **All parametrize with `ids=`**: Always. For IDE test discovery and readable output.
5. **Coverage >90%**: Standard across all test suites. No exceptions.
6. **Mocking**: ONLY `mocker` fixture from `pytest-mock`. NEVER `from unittest.mock import Mock/AsyncMock/patch`.
7. **Discoverable**: Tests must be discoverable via VSCode/Cursor pytest discovery.
8. **Fixture ordering**: Conftest fixtures MUST follow a strict declaration order — paths/resources → factories → infrastructure → services/adapters → data → helpers. See `skills/testing/fixtures` for the full ordering convention.
9. **Test clients — framework first**: When testing APIs (REST, GraphQL, WebSocket), always use the framework's own test client (FastAPI `TestClient`/`ASGITransport`, etc.). If none exists, search for a third-party test client. Only create a custom one as last resort. See `skills/testing/mocking`.
10. **Mock libraries — search before building**: When mocking third-party services, always search for purpose-built mock libraries first (e.g., `FakeRedis` for Redis, `pytest-httpserver` for HTTP). Only build custom mock servers when nothing exists. See `skills/testing/mocking`.
11. **Data generation — Polyfactory**: MANDATORY for all data modeling, storage models, and domain fixtures. Every Pydantic model and dataclass that represents data from storage or external sources MUST have a Polyfactory factory. No hand-written dicts for domain data. See `skills/testing/fixtures`.
12. **confmodels.py**: Each domain test subdirectory that needs test data has a `confmodels.py` file containing Polyfactory factories AND external API response schemas (Pydantic models). Factories and schemas are co-located. See `skills/testing/fixtures` for structure and naming.
13. **Slow marker**: Tests that hit real external services are marked `@pytest.mark.slow` and excluded by default via `addopts`. Run explicitly with `uv run python -m pytest -m slow -v`.

## Directory Structure

Tests mirror source exactly. The test type is the first level:

```
tests/
├── conftest.py                          # session-scoped, shared by ALL
├── unit/
│   ├── conftest.py                      # unit-wide (FakeRedis, mock utilities)
│   └── <package>/                       # mirrors source package exactly
│       ├── conftest.py                  # package-wide unit fixtures
│       ├── confmodels.py                # Polyfactory factories + external API schemas
│       ├── core/
│       │   ├── conftest.py
│       │   └── test_settings.py
│       ├── adapters/
│       │   ├── confmodels.py            # adapter-specific factories + API schemas
│       │   ├── conftest.py              # mock server fixtures (create_mock_server)
│       │   └── test_nlp.py
│       └── pipelines/
│           └── test_entities.py
├── integration/
│   ├── conftest.py                      # shared resources (audio, sample data)
│   └── <package>/
│       ├── conftest.py
│       └── adapters/
│           └── test_searxng.py          # respx-mocked + @slow live tests
├── evaluation/
│   └── regression/
│       └── <domain>/
│           └── test_regression.py
├── acceptance/
│   └── ...
└── resources/                           # shared test assets (JSON, audio, CSV)
    └── <domain>/
```

**Rule**: source at `app/adapters/nlp.py` → test at `tests/unit/app/adapters/test_nlp.py`. Always. No shortcuts.

### Aspect Files

When a module has many test scenarios, split into aspect files — one per logical area:

```
tests/unit/app/pipelines/
├── test_entities_ingest.py
├── test_entities_match.py
└── test_entities_delete.py
```

## Conftest Hierarchy

Conftest files form a scope tree. A fixture lives at the **narrowest** level that needs it:

| Scope | conftest.py location | Contains |
|-------|---------------------|----------|
| ALL tests | `tests/conftest.py` | Session fixtures (event loop, app instance) |
| All unit | `tests/unit/conftest.py` | FakeRedis, `create_mock_server`, common mock utilities |
| Package-wide | `tests/unit/<package>/conftest.py` | Package-level fixtures, factory imports from confmodels |
| Domain-specific | `tests/unit/<package>/<domain>/conftest.py` | Mock server factory fixtures, domain fixtures |

### What goes in conftest (EVERYTHING reusable)

- `@pytest.fixture` definitions
- Imports from sibling `confmodels.py` (factories, API schemas)
- Private helper functions: `_make_node()`, `_build_sample()`
- Loaded resource paths: `_RESOURCES = Path(__file__).parents[N] / "resources" / "<domain>"`
- Mock server utilities (`create_mock_server`)
- Fake/mock service instances
- Parametrize case constants shared across files

### What goes in confmodels.py (factories + API schemas)

- Polyfactory factory classes for domain models
- Pydantic models representing external API response shapes
- Polyfactory factories for those external API schemas
- **Nothing else. No fixtures. No test functions.**

### What goes in test modules (ONLY tests)

- `async def test_*() -> None` functions
- Module-level parametrize constants ONLY if used exclusively in that one file
- **Nothing else. No fixtures. No helpers. No types. No factories.**

## Test Naming

Pattern: `async def test_<target>_<scenario>() -> None`

- `<target>`: the function, method, or class being tested (snake_case always).
- `<scenario>`: the specific behavior. Nested suffixes mirror nested coverage depth.

### Flat coverage — single level

```python
async def test_loop_returns_results() -> None: ...
async def test_loop_empty_input() -> None: ...
async def test_loop_timeout() -> None: ...
```

### Nested coverage — suffixes cascade with depth

When a function has branching behavior, suffixes mirror the behavior tree left-to-right:

`test_<target>_<aspect>_<specific>_<edge_case>`

```python
# Level 1: aspect of loop
async def test_loop_recursivity_success() -> None: ...
async def test_loop_recursivity_error() -> None: ...
async def test_loop_recursivity_max_depth() -> None: ...

# Level 2: deeper into a specific aspect
async def test_loop_recursivity_error_timeout() -> None: ...
async def test_loop_recursivity_error_invalid_state() -> None: ...
```

Reading `test_loop_recursivity_error_timeout`: "testing `loop`, specifically the recursivity aspect, specifically the error path, specifically the timeout edge case."

### Class methods

```python
# test_<class_snake>_<method>_<scenario>
async def test_knowledge_store_search_empty_query() -> None: ...
async def test_entity_annotator_annotate_valid_node() -> None: ...
```

### Module-level functions

```python
# test_<function>_<scenario>
async def test_calculate_confidence_high_score() -> None: ...
async def test_build_tenant_namespace_missing_tenant() -> None: ...
```

### Section headers in test files

Separate logical groups within a test file:

```python
##### SEARCH RESPONSE DATACLASS #####

async def test_search_response_frozen() -> None: ...
async def test_search_response_str_format() -> None: ...

##### CLASS ATTRIBUTES #####

async def test_adapter_name() -> None: ...

##### QUERY — MOCK HTTP SERVER #####

async def test_query_returns_search_responses(mock_searxng) -> None: ...
```

## Parametrize

**DEFAULT choice.** Always use parametrize when a function can be tested with different inputs/outputs. Only fall back to separate test functions when the setup/teardown is fundamentally different between cases.

### Small case sets — inline

```python
@pytest.mark.parametrize(
    ("input_text", "expected"),
    [("Apple Inc", Category.ORG), ("John Doe", Category.PERSON), ("NYC", Category.LOCATION)],
    ids=["org", "person", "location"],
)
async def test_categorize_entity_resolves(input_text: str, expected: Category) -> None:
    assert categorize(input_text) == expected
```

### Large case sets — module-level constant

```python
_TRUNCATION_CASES: list[tuple[int, int]] = [(200, 200), (500, 200), (10, 10)]

@pytest.mark.parametrize(
    ("input_len", "expected_len"), _TRUNCATION_CASES, ids=["exact", "over", "under"],
)
async def test_snippet_truncation(input_len: int, expected_len: int) -> None: ...
```

### When NOT to parametrize

Only when cases require fundamentally different fixture setup, different assertions, or different side effects that parametrize cannot express. In that case, create separate atomic test functions.

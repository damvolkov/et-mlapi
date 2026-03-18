---
description: Naming conventions for modules, classes, functions, tests, constants, and type aliases. Applies everywhere.
alwaysApply: true
---

# Naming Conventions

**Pipeline node: N3** — Prerequisite: `N1-taxonomy.md` (domain vocabulary must be established first).

Every name must be self-explanatory. If you need a comment to explain the name, rename it.

## Naming Philosophy

Names are not labels — they are contracts. A name must reveal **what it does**, **who owns it**, and **how it relates** to the names around it.

### Simplicity First

Choose the simplest, most intuitive verb that directly maps to the action. Public methods on a class mirror the class's core responsibility with minimal words:

```python
class Scanner:
    async def scan(self, source: Path) -> list[Match]: ...

class Retriever:
    async def retrieve(self, query: Query) -> list[Document]: ...

class Evaluator:
    def evaluate(self, candidates: list[Candidate]) -> Score: ...
```

`scan`, `retrieve`, `evaluate`, `run`, `process`, `resolve` — these are the right verbs. Not `perform_scanning_operation` or `execute_retrieval_process`.

### Names Reflect Dependencies

Names are genealogical. When functions depend on each other, their names must share roots that reveal the call tree. Reading a name should tell you what family of logic it belongs to, which siblings exist, and what it descends from. If you can't infer the dependency structure from the names alone, the naming is wrong.

### Visibility Drives Structure

A function's visibility determines its naming structure:

- **Public on a class** → simple verb, no prefix, tied to the class identity: `scan()`, `annotate()`.
- **Private on a class** → domain suffix from owning class + genealogical root: `_sc_extract_func()`.
- **Public at module level (helper/utility)** → simple, reusable name with no suffix: `recursive_mapper()`, `flatten_tree()`.
- **Private at module level** → `_` prefix, no suffix needed (the module IS the domain): `_parse_header()`, `_normalize_score()`.

## Modules & Files

- `snake_case.py`. Short, descriptive of what they contain.
- Domain directories group by responsibility: `adapters/`, `models/`, `core/`, `api/`, `tasks/`, `pipelines/`, `processors/`, `operations/`.
- Reserved names:
  - `base.py` — ABC / base class for the domain.
  - `main.py` — entrypoint (app or CLI).
  - `deps.py` — DI dependency chains.
  - `settings.py` — pydantic-settings config.
  - `helpers.py` / `utils.py` — small domain utilities.
  - `router.py` — API route handlers.
  - `conftest.py` — pytest fixtures.
- One concept per module. If a module grows, split into a subdirectory with `base.py` + specific files.

## Classes

PascalCase. Noun-based. Name reflects what it IS, not what it does.

| Pattern | Convention | Examples |
|---------|-----------|----------|
| Base/ABC | `Base{Concept}` or just `{Concept}` | `Adapter`, `Pipeline`, `Processor`, `BaseExtractor` |
| Domain subclass | `{Specialty}{Base}` | `ConciergeAgent`, `InventoryAgent`, `NLPRuntimeAdapter` |
| Pydantic models | `{Concept}` | `Entity`, `Node`, `Session`, `RequestHeaders` |
| API DTOs | `{Concept}Request` / `{Concept}Response` | `TokenRequest`, `DispatchResponse` |
| Config models | `{Concept}Config` | `AgentConfig`, `AgentsConfig` |
| Settings | `Settings` (always, multi-inheritance for composition) | `Settings(CoreSettings, ApiSettings, ...)` |
| Adapters | `{Tech}{Role}` or `{Domain}Adapter` | `PiperTTS`, `WhisperSTT`, `NLPRuntimeAdapter` |
| Registries | `{Concept}Registry` | `TaskRegistry` |
| Enums | `{Concept}` (StrEnum) | `TaskStatus`, `RequestMethod`, `LogIcon` |
| Processors | `{Domain}{Action}` | `EntityAnnotator`, `LogitProcessor` |

## Functions & Methods

snake_case. Verb-first. Name reflects what it DOES.

| Pattern | Prefix | Examples |
|---------|--------|----------|
| Builders | `build_` | `build_tenant_namespace()`, `build_ws_url()` |
| Factories | `create_` | `create_merger()`, `create_session()` |
| Loaders | `load_` | `load_agents_config()`, `load_template()` |
| Accessors | `get_` | `get_version()`, `get_pending_notifications()` |
| Validators | `validate_` | `validate_routes()`, `validate_not_empty()` |
| Event handlers | `on_` | `on_enter()`, `on_agent_state()` |
| Formatters | `_format_` (private) | `_format_result()`, `_format_task_result()` |
| Internal heavy ops | `_heavy_` or `_run_` (private) | `_heavy_search()`, `_run_task()` |
| Classmethods | `from_` | `from_yaml()`, `from_dict()` |
| Computed props | `@property` / `@computed_field` | `is_dev`, `log_level`, `duration_seconds`, `system_prompt` |

Private: single `_` prefix. Never `__` dunder (except magic methods).

### Private Methods — Genealogical Naming

Private methods that belong to a class's business logic use a **domain suffix** from the owning class and **genealogical roots** that mirror the call tree.

**Format:** `_<suffix>_<root>_<action>` or `_<suffix>_<action>` when no shared root exists.

- `<suffix>`: 2-4 char abbreviation derived from the owning class (e.g., `sc` = Scanner, `ann` = Annotator, `idx` = Indexer, `rr` = Reranker).
- `<root>`: shared stem that groups sibling methods with a common dependency. Methods that call the same helper share the same root.
- `<action>`: short, agnostic verb describing the specific step.

#### Basic — flat privates, no shared dependencies

When private methods are independent steps with no call relationships between them:

```python
# Scanner owns the suffix "sc"
class Scanner:
    async def scan(self, source: Path) -> list[Match]:
        candidates = self._sc_collect_paths(source)
        return self._sc_filter_matches(candidates)

    def _sc_collect_paths(self, source: Path) -> list[Path]: ...
    def _sc_filter_matches(self, paths: list[Path]) -> list[Match]: ...
```

#### Genealogical — shared roots reveal the call tree

When multiple private methods depend on a common helper, they share a root that immediately reveals the relationship. The name tree mirrors the call tree:

```python
class Scanner:
    """Extracts function and class definitions from source files."""

    async def scan(self, source: Path) -> list[Definition]:
        funcs = self._sc_extract_func(source)      # ← sibling: shares root "extract"
        classes = self._sc_extract_class(source)    # ← sibling: shares root "extract"
        return funcs + classes

    # Siblings — both use _sc_extract_recursive_mapper, both share root "extract"
    def _sc_extract_func(self, source: Path) -> list[Definition]:
        tree = ast.parse(source.read_text())
        return self._sc_extract_recursive_mapper(tree, ast.FunctionDef)

    def _sc_extract_class(self, source: Path) -> list[Definition]:
        tree = ast.parse(source.read_text())
        return self._sc_extract_recursive_mapper(tree, ast.ClassDef)

    # Deepest helper — the shared root "extract" + specific role "recursive_mapper"
    def _sc_extract_recursive_mapper(
        self, node: ast.AST, target: type[ast.AST],
    ) -> list[Definition]:
        results = [node] if isinstance(node, target) else []
        return results + list(
            chain.from_iterable(
                self._sc_extract_recursive_mapper(child, target)
                for child in ast.iter_child_nodes(node)
            )
        )
```

**Reading the dependency tree from names alone:**

```
scan()                              ← public: simple verb, no prefix
├── _sc_extract_func()              ← private: suffix "sc" + root "extract"
│   └── _sc_extract_recursive_mapper()
└── _sc_extract_class()             ← sibling: same root "extract" = same family
    └── _sc_extract_recursive_mapper()
```

The shared `_sc_extract_` tells you these methods are siblings in the same family. The deeper `_recursive_mapper` is their shared child.

#### Visibility decision — suffix vs no suffix

The domain suffix exists because the method is **bound to a specific class**. If the logic is reusable, it should not be private and should not carry a suffix:

```python
# WRONG — recursive_mapper is generic, not Scanner-specific
class Scanner:
    def _sc_extract_recursive_mapper(self, node, target): ...

# RIGHT — if it's reusable, extract to module-level with a simple name
def recursive_mapper(node: ast.AST, target: type[ast.AST]) -> list[ast.AST]:
    """Generic AST recursive mapper. Reusable by any module."""
    results = [node] if isinstance(node, target) else []
    return results + list(
        chain.from_iterable(
            recursive_mapper(child, target) for child in ast.iter_child_nodes(node)
        )
    )

class Scanner:
    def _sc_extract_func(self, source: Path) -> list[Definition]:
        tree = ast.parse(source.read_text())
        return recursive_mapper(tree, ast.FunctionDef)  # ← no suffix, no self
```

**Decision tree:**

| Question | → Name structure |
|----------|-----------------|
| Is it only used inside this class's private logic? | `_<suffix>_<root>_<action>` |
| Is it potentially reusable by other classes/modules? | Public module-level, simple name: `recursive_mapper()` |
| Is it a module-level helper used only in this file? | `_<action>()` (no suffix, the module is the domain) |

**Rules:**
- Every private method in a class MUST carry the domain suffix from the owning class.
- The suffix is consistent within the entire class.
- Methods that share a dependency MUST share a naming root. The name tree mirrors the call tree.
- Names after the suffix/root must be agnostic and simple — no redundant domain references.
- Do NOT extract private methods for trivial logic (1-3 lines) or when two methods share nearly identical logic. Inline instead.

## Constants

- Module-level public: `UPPER_SNAKE_CASE` → `AGENT_CLASSES`, `MATCH_SAMPLE_PATH`
- Module-level private: `_UPPER_SNAKE_CASE` → `_RESOURCES`, `_ZERO_WIDTH`, `_FAKE_MARKDOWN`
- ClassVar in Settings: `UPPER_SNAKE_CASE` → `BASE_DIR`, `API_VERSION`, `DATA_PATH`
- Enum members: `UPPER_SNAKE_CASE` with `auto()` → `PENDING = auto()`, `RUNNING = auto()`

## Singletons (module-level)

lowercase, no prefix: `settings = Settings()`, `logger = IconLogger(...)`, `router = APIRouter(...)`.

## Type Aliases & TypeVars

- Type aliases: PascalCase via `type` statement → `type FieldType = Literal[...]`, `type TaskCallback = Callable[...]`
- Annotated types: PascalCase → `TagField`, `TextField`, `RedisUrlStr`, `RoundedScore`
- TypeVars: single letter or short `T`-prefixed → `T`, `D`, `S`, `TRaw`, `TNode`
- TypeVars always bound: `D = TypeVar("D", bound=Node)`

## Tests

See `rules/N6-testing.md` for the complete testing standard (directory structure, conftest hierarchy, fixtures, coverage, parametrize). Test naming summary:

- Pattern: `async def test_<target>_<scenario>() -> None`
- Nested suffixes mirror coverage depth: `test_loop_recursivity_error_timeout`
- Class methods: `test_<class_snake>_<method>_<scenario>`
- Fixtures: noun-based (`fake_redis`, `sample_entity_data`). Always in `conftest.py`.

## Section Headers

Use section headers to visually separate logical blocks within a module. Format:

```python
##### SECTION NAME #####
```

- 5 `#` on each side, one space padding.
- Name in UPPERCASE.
- Exactly one blank line before the header.
- Use in source and test files alike.

Common sections by file type:

| File type | Typical sections |
|---|---|
| Models | `ENUMS`, `COMPOSE`, `SYSTEMD`, `BASE`, `YAML`, `INI`, `TOML` |
| Commands | `HELPERS`, `COMMANDS`, `SCANNERS` |
| Settings | `PATHS`, `SERVICE MANAGEMENT`, `REGISTRIES`, provider names |
| Tests | Named after the unit under test: `MODEL VALIDATION`, `INSTALL / UNINSTALL` |

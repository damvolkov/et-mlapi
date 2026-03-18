---
name: starter-library
description: |
  Starter template for Python libraries and reusable packages. Use when scaffolding a new
  library, shared utility package, or SDK. Includes minimum stack, src layout, model patterns
  with multi-format serialization, and async utility patterns.
  Reference project: e-core (ecore lib).
---

# Starter: Python Library

## Minimum Stack

### pyproject.toml

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "<lib-name>"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    # Data Validation
    "pydantic>=2.12.0",
    # Serialization
    "pyyaml>=6.0.3",
    "tomli-w>=1.2.0",
    # Terminal UI (optional)
    "rich>=14.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.0.0",
    "ruff>=0.14.0",
    "ty>=0.0.17",
]

[tool.hatch.build.targets.wheel]
packages = ["src/<lib_name>"]

[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["<lib_name>"]

[tool.ty.environment]
python-version = "3.13"

[tool.ty.rules]
possibly-unresolved-reference = "error"
unresolved-import = "error"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## Project Tree

```
<lib-name>/
├── src/<lib_name>/
│   ├── models/
│   │   ├── base.py                 # BaseModel with multi-format serialization
│   │   ├── service.py              # domain models
│   │   └── config.py               # config/schema models
│   └── utils/
│       ├── file.py                 # async file operations
│       └── merger.py               # template/data merging utilities
├── tests/
│   ├── conftest.py                 # fixtures, test resources
│   ├── resources/                  # test data files (YAML, JSON, TOML)
│   └── unit/
│       ├── models/
│       │   └── test_base.py
│       └── utils/
│           └── test_file.py
├── pyproject.toml
├── Makefile
└── uv.lock
```

## Essential Patterns

### models/base.py — Multi-Format Serialization

```python
from typing import TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound="BaseModelFormat")


class BaseModelFormat(BaseModel):
    """Base model with multi-format serialization."""

    @classmethod
    def model_validate_yaml(cls: type[T], data: str | bytes) -> T:
        parsed = yaml.safe_load(data)
        return cls.model_validate(parsed)

    def model_dump_yaml(self, **kwargs) -> str:
        return yaml.dump(
            self.model_dump(**kwargs),
            default_flow_style=False,
            sort_keys=False,
        )

    @classmethod
    def model_validate_toml(cls: type[T], data: str | bytes) -> T:
        import tomllib
        parsed = tomllib.loads(data if isinstance(data, str) else data.decode())
        return cls.model_validate(parsed)

    def model_dump_toml(self, **kwargs) -> str:
        import tomli_w
        return tomli_w.dumps(self.model_dump(**kwargs))


class BaseModelYAML(BaseModelFormat):
    """Model with YAML serialization."""
    ...


class BaseModelTOML(BaseModelFormat):
    """Model with TOML serialization."""
    ...


class BaseModelUniversal(BaseModelYAML, BaseModelTOML):
    """Model supporting YAML + TOML + JSON serialization."""
    ...
```

### models/service.py — Domain Models

```python
from enum import StrEnum

from pydantic import BaseModel

from <lib_name>.models.base import BaseModelYAML


class FileExtension(StrEnum):
    YML = "yml"
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    MD = "md"
    PY = "py"


class ServiceConfig(BaseModelYAML):
    """Service configuration model."""

    name: str
    image: str
    ports: list[str] = []
    volumes: list[str] = []
    environment: dict[str, str] = {}
```

### utils/file.py — Async File Operations

```python
import asyncio
from pathlib import Path

import aiofiles

from <lib_name>.models.service import FileExtension


async def scan_files(
    directory: Path,
    *,
    pattern: str = "*",
    ext: FileExtension | None = None,
    recursive: bool = True,
) -> list[Path]:
    """Async file scanner with extension filtering."""

    def _scan() -> list[Path]:
        glob_fn = directory.rglob if recursive else directory.glob
        files = sorted(glob_fn(pattern))
        if ext is not None:
            files = [f for f in files if f.suffix == f".{ext.value}"]
        return files

    return await asyncio.to_thread(_scan)


async def read_file(path: Path) -> str:
    async with aiofiles.open(path, "r") as f:
        return await f.read()


async def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w") as f:
        await f.write(content)


async def find_subdirectories(
    directory: Path,
    *,
    containing: str | None = None,
) -> list[Path]:
    """List subdirectories, optionally filter by child file."""

    def _find() -> list[Path]:
        dirs = [d for d in sorted(directory.iterdir()) if d.is_dir()]
        if containing is not None:
            dirs = [d for d in dirs if (d / containing).exists()]
        return dirs

    return await asyncio.to_thread(_find)
```

### utils/merger.py — Abstract Merger Pattern

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import asyncio

import aiofiles
import yaml


class BaseMerger(ABC):
    """Abstract merger for composing templates."""

    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir

    @abstractmethod
    def get_base_content(self) -> dict[str, Any]: ...

    async def _load_template(self, name: str) -> dict[str, Any]:
        path = self._find_template(name)
        async with aiofiles.open(path) as f:
            return yaml.safe_load(await f.read())

    def _find_template(self, name: str) -> Path:
        for path in self._templates_dir.rglob(f"*{name}*"):
            if path.is_file():
                return path
        msg = f"Template not found: {name}"
        raise FileNotFoundError(msg)

    async def merge(self, names: list[str]) -> dict[str, Any]:
        """Merge multiple templates in parallel."""
        base = self.get_base_content()
        templates = await asyncio.gather(
            *(self._load_template(n) for n in names)
        )
        for template in templates:
            self._deep_merge(base, template)
        return base

    def _deep_merge(self, base: dict, overlay: dict) -> None:
        for key, value in overlay.items():
            match (base.get(key), value):
                case (dict() as existing, dict()):
                    self._deep_merge(existing, value)
                case _:
                    base[key] = value

    async def save(self, content: dict[str, Any], output: Path) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(output, "w") as f:
            await f.write(yaml.dump(content, default_flow_style=False))
```

### conftest.py — Test Fixtures

```python
from pathlib import Path

import pytest


@pytest.fixture
def resources_dir() -> Path:
    return Path(__file__).parent / "resources"


@pytest.fixture
def sample_yaml(resources_dir: Path) -> str:
    return (resources_dir / "sample.yml").read_text()


@pytest.fixture
def tmp_templates(tmp_path: Path) -> Path:
    templates = tmp_path / "templates"
    templates.mkdir()
    return templates
```

### Makefile

```makefile
.PHONY: lint type test check

lint:
	@uv run ruff check --fix src/
	@uv run ruff format src/

type:
	@uv run ty check src/

test:
	@uv run pytest -v

check: lint type test
```

## Key Conventions

- **Src layout**: `src/<lib_name>/` for proper package isolation
- **Multi-format models**: `BaseModelYAML`, `BaseModelTOML`, `BaseModelUniversal`
- **Async-first utils**: `asyncio.to_thread()` for sync-to-async bridging
- **Abstract merger**: factory pattern for composable template merging
- **No `__init__.py`**: implicit namespace packages (PEP 420)
- **hatchling**: build backend with explicit `packages` in wheel config
- **Test resources**: `tests/resources/` for shared test data
- **No runtime deps on frameworks**: library stays framework-agnostic
- **Workspace-compatible**: can be a member of `[tool.uv.workspace]`

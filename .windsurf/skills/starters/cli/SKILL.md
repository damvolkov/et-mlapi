---
name: starter-cli
description: |
  Starter template for async CLI applications built on Cyclopts. Use when scaffolding a
  new CLI tool, developer utility, or command-line application. Includes minimum stack,
  project tree, command registration patterns, and settings.
  Reference project: e-core (ecli).
---

# Starter: CLI Application (Cyclopts)

## Minimum Stack

### pyproject.toml

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    # CLI Framework
    "cyclopts>=3.0.0",
    # Data & Config
    "pydantic>=2.12.0",
    "pydantic-settings>=2.13.0",
    # Serialization
    "pyyaml>=6.0.3",
    "tomli-w>=1.2.0",
    # Async I/O
    "aiofiles>=24.1.0",
    # Terminal UI
    "rich>=14.0.0",
]

[project.scripts]
<cli-name> = "<package>.main:app"

[dependency-groups]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.0.0",
    "ruff>=0.14.0",
    "ty>=0.0.17",
    "pre-commit>=4.4.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/<package>"]

[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["<package>"]

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

### Monorepo layout (libs + services)

```
<project>/
├── pyproject.toml                      # workspace root
├── libs/<lib-name>/
│   ├── pyproject.toml
│   └── src/<lib_name>/
│       ├── models/
│       │   └── base.py                 # shared Pydantic models
│       └── utils/
│           └── file.py                 # async file operations
├── services/<cli-name>/
│   ├── pyproject.toml
│   └── src/<cli_name>/
│       ├── main.py                     # cyclopts App + command registration
│       ├── settings.py                 # pydantic-settings
│       └── commands/
│           ├── generate.py             # subcommand App
│           └── sync.py                 # subcommand App
├── tests/
│   ├── conftest.py
│   └── unit/
│       ├── libs/<lib_name>/
│       └── services/<cli_name>/
├── Makefile
└── uv.lock
```

### Standalone layout

```
<project>/
├── src/<package>/
│   ├── main.py                         # cyclopts App entrypoint
│   ├── settings.py                     # pydantic-settings
│   └── commands/
│       ├── init.py                     # subcommand: init project
│       ├── build.py                    # subcommand: build
│       └── deploy.py                   # subcommand: deploy
├── tests/
│   ├── conftest.py
│   └── unit/
│       └── commands/
├── pyproject.toml
├── Makefile
└── uv.lock
```

## Essential Patterns

### main.py — Cyclopts App Entry

```python
from cyclopts import App

from <package>.commands.generate import generate_app
from <package>.commands.sync import sync_app

main_app = App(name="<cli-name>", help="Description of CLI tool.")

# Register subcommands
main_app.command(generate_app)
main_app.command(sync_app)

app = main_app  # entry point for pyproject.toml
```

### commands/generate.py — Subcommand

```python
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from <package>.settings import settings as st

generate_app = App(name="generate", help="Generate configuration files.")
console = Console()


@generate_app.default
async def default() -> None:
    """Show generate help."""
    console.print("[bold]Available generators:[/bold]")
    console.print("  docker   — Generate Docker Compose stack")
    console.print("  config   — Generate config files")


@generate_app.command(name="docker")
async def generate_docker(
    services: Annotated[
        list[str],
        Parameter(help="Services to include in the stack"),
    ],
    output: Annotated[
        Path,
        Parameter(name="--output", help="Output directory"),
    ] = Path("artifacts"),
) -> None:
    """Generate a Docker Compose stack from templates."""
    console.print(f"Generating stack for: {', '.join(services)}")
    # ... generation logic
    console.print(f"[green]Output written to {output}[/green]")
```

### settings.py — CLI Settings

```python
from pathlib import Path
from typing import ClassVar

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="<PREFIX>_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ClassVar: not from env
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    TEMPLATES_ROOT: ClassVar[Path] = BASE_DIR / "templates"

    # Env-configurable
    home_dir: Path = Path.home()
    config_dir: Path = Path.home() / ".config" / "<cli-name>"

    @computed_field
    @property
    def output_dir(self) -> Path:
        return self.BASE_DIR / "artifacts"


settings = Settings()
```

### Async File Utils

```python
from pathlib import Path

import aiofiles


async def read_file(path: Path) -> str:
    """Read file content asynchronously."""
    async with aiofiles.open(path, "r") as f:
        return await f.read()


async def write_file(path: Path, content: str) -> None:
    """Write content to file asynchronously."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w") as f:
        await f.write(content)
```

### conftest.py — Test Fixtures

```python
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def tmp_templates(tmp_path: Path) -> Path:
    """Create temporary templates directory."""
    templates = tmp_path / "templates"
    templates.mkdir()
    return templates


@pytest.fixture
def mock_settings(monkeypatch, tmp_path, tmp_templates):
    """Override settings for testing."""
    from <package> import settings as settings_module
    from <package>.settings import Settings

    s = Settings(
        home_dir=tmp_path,
        config_dir=tmp_path / ".config" / "<cli-name>",
    )
    monkeypatch.setattr(settings_module, "settings", s)
    return s
```

### Makefile

```makefile
.PHONY: install sync lint type test check

install:
	@command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	@uv sync --dev
	@uv run pre-commit install

sync:
	@uv sync --dev

lint:
	@uv run ruff check --fix .
	@uv run ruff format .

type:
	@uv run ty check services/ libs/

test:
	@uv run pytest -v

check: lint type test
```

## Key Conventions

- **Cyclopts** over Typer: native async, better type support, `Annotated[T, Parameter()]`
- **Subcommand pattern**: one `App()` per command file, registered via `main_app.command(sub_app)`
- **`@app.default`**: shows help/info when subcommand called without arguments
- **Async commands**: all command handlers are `async def`
- **Settings via `pydantic-settings`**: `ClassVar` for static paths, env vars for runtime config
- **`rich.Console`**: for styled terminal output
- **aiofiles**: mandatory for all file I/O
- **No `__init__.py`**: implicit namespace packages
- **Monorepo-friendly**: `[tool.uv.workspace] members = ["services/*", "libs/*"]`
- **Test isolation**: monkeypatch settings in fixtures

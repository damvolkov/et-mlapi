"""Unified settings for et-mlapi — YAML-based configuration with typed sub-models."""

import importlib.metadata
import tomllib
from contextlib import suppress
from enum import StrEnum, auto
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource

_HAS_GIT = False
with suppress(ImportError):
    import git

    _HAS_GIT = True


##### HELPERS #####


def read_pyproject(pyproject_path: Path) -> dict:
    """Read pyproject.toml and return parsed contents.

    Args:
        pyproject_path: Absolute path to pyproject.toml.

    Returns:
        Parsed TOML as a dictionary.
    """
    with pyproject_path.open("rb") as fh:
        return tomllib.load(fh)


def get_version(base_dir: Path) -> str:
    """Resolve project version from git tags or package metadata.

    Attempts git tag resolution first (via GitPython), then falls back
    to ``importlib.metadata``.  Returns ``"0.0.0"`` when neither source
    is available.

    Args:
        base_dir: Repository root directory.

    Returns:
        Semantic version string.
    """
    if _HAS_GIT:
        with suppress(Exception):
            repo = git.Repo(base_dir, search_parent_directories=True)
            if latest_tag := max(repo.tags, key=lambda t: t.commit.committed_datetime, default=None):
                return str(latest_tag)
    with suppress(Exception):
        return importlib.metadata.version("et-mlapi")
    return "0.0.0"


##### ENUMS #####


class EnvironmentType(StrEnum):
    """Application environment selector."""

    DEV = auto()
    PROD = auto()


##### CONFIG SUB-MODELS #####


class SystemConfig(BaseModel):
    """Server and application runtime settings.

    Attributes:
        debug: Enable debug mode (verbose logging, auto-reload).
        environment: Target environment — ``DEV`` or ``PROD``.
        host: Bind address for the HTTP server.
        port: Bind port for the HTTP server.
        max_workers: ProcessPoolExecutor worker count.
    """

    debug: bool = True
    environment: EnvironmentType = EnvironmentType.DEV
    host: str = "0.0.0.0"
    port: int = Field(default=8012, ge=1, le=65535)
    max_workers: int = Field(default=4, ge=1)


##### SETTINGS #####


class Settings(BaseSettings):
    """Root settings — loaded from ``data/config/config.yaml``.

    Class-level constants (``ClassVar``) are derived from the repository
    structure and ``pyproject.toml``.  Instance fields are populated from
    the YAML configuration file at startup.

    Attributes:
        BASE_DIR: Repository root (resolved at import time).
        PROJECT: Parsed ``pyproject.toml`` contents.
        API_NAME: Project name from ``pyproject.toml``.
        API_DESCRIPTION: Project description from ``pyproject.toml``.
        API_VERSION: Resolved version (git tag or package metadata).
        DATA_PATH: Path to the ``data/`` directory.
        CONFIG_PATH: Path to the ``data/config/`` directory.
        system: Server and runtime configuration sub-model.
    """

    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent.parent
    PROJECT: ClassVar[dict] = read_pyproject(BASE_DIR / "pyproject.toml")
    API_NAME: ClassVar[str] = PROJECT.get("project", {}).get("name", "et-mlapi")
    API_DESCRIPTION: ClassVar[str] = PROJECT.get("project", {}).get("description", "ML API Template")
    API_VERSION: ClassVar[str] = get_version(BASE_DIR)
    DATA_PATH: ClassVar[Path] = BASE_DIR / "data"
    CONFIG_PATH: ClassVar[Path] = DATA_PATH / "config"

    system: SystemConfig = SystemConfig()

    model_config = SettingsConfigDict(
        yaml_file=str(BASE_DIR / "data" / "config" / "config.yaml"),
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Load from init kwargs first, then YAML config file."""
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    @property
    def api_url(self) -> str:
        """Compute the full API base URL."""
        return f"http://{self.system.host}:{self.system.port}"


settings = Settings()

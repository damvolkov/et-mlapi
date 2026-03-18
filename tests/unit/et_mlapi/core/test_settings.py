"""Tests for core/settings.py."""

from pathlib import Path

import pytest

from et_mlapi.core.settings import EnvironmentType, Settings, SystemConfig, get_version, read_pyproject, settings

##### READ PYPROJECT #####


async def test_read_pyproject_returns_dict() -> None:
    base_dir = Path(__file__).resolve().parents[4]
    result = read_pyproject(base_dir / "pyproject.toml")
    assert isinstance(result, dict)
    assert "project" in result


async def test_read_pyproject_has_name() -> None:
    base_dir = Path(__file__).resolve().parents[4]
    result = read_pyproject(base_dir / "pyproject.toml")
    assert result["project"]["name"] == "et-mlapi"


##### GET VERSION #####


async def test_get_version_returns_string() -> None:
    base_dir = Path(__file__).resolve().parents[4]
    version = get_version(base_dir)
    assert isinstance(version, str)
    assert len(version) > 0


async def test_get_version_fallback_no_git(tmp_path: Path) -> None:
    version = get_version(tmp_path)
    assert isinstance(version, str)


##### ENVIRONMENT TYPE ENUM #####


@pytest.mark.parametrize(
    ("value", "expected"),
    [("dev", EnvironmentType.DEV), ("prod", EnvironmentType.PROD)],
    ids=["dev", "prod"],
)
async def test_environment_type_values(value: str, expected: EnvironmentType) -> None:
    assert EnvironmentType(value) == expected


##### SYSTEM CONFIG #####


async def test_system_config_defaults() -> None:
    cfg = SystemConfig()
    assert cfg.debug is True
    assert cfg.environment == EnvironmentType.DEV
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 8012
    assert cfg.max_workers == 4


async def test_system_config_custom() -> None:
    cfg = SystemConfig(debug=False, environment=EnvironmentType.PROD, port=9000)
    assert cfg.debug is False
    assert cfg.environment == EnvironmentType.PROD
    assert cfg.port == 9000


##### SETTINGS SINGLETON #####


async def test_settings_singleton_exists() -> None:
    assert settings is not None
    assert isinstance(settings, Settings)


async def test_settings_has_classvars() -> None:
    assert isinstance(Settings.BASE_DIR, Path)
    assert isinstance(Settings.API_NAME, str)
    assert isinstance(Settings.API_VERSION, str)
    assert isinstance(Settings.DATA_PATH, Path)
    assert isinstance(Settings.CONFIG_PATH, Path)


async def test_settings_system_config() -> None:
    assert isinstance(settings.system, SystemConfig)
    assert settings.system.port == 8012


async def test_settings_api_url() -> None:
    url = settings.api_url
    assert url == f"http://{settings.system.host}:{settings.system.port}"
    assert url.startswith("http://")

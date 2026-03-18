"""Tests for core/logger.py."""

import pytest

from et_mlapi.core.logger import (
    _DEFAULT_COLOR,
    _LEVEL_COLORS,
    _MAX_TEXT_LEN,
    _RESET,
    _STEP_COLORS,
    ColorRenderer,
    configure_logging,
    logger,
)

##### COLOR CONSTANTS #####


async def test_step_colors_not_empty() -> None:
    assert len(_STEP_COLORS) > 0
    assert "START" in _STEP_COLORS
    assert "ERROR" in _STEP_COLORS


async def test_level_colors_has_error() -> None:
    assert "error" in _LEVEL_COLORS
    assert "critical" in _LEVEL_COLORS


async def test_default_color_is_string() -> None:
    assert isinstance(_DEFAULT_COLOR, str)
    assert ";" in _DEFAULT_COLOR


async def test_max_text_len_is_120() -> None:
    assert _MAX_TEXT_LEN == 120


##### COLOR RENDERER #####


async def test_color_renderer_basic() -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "test message"})
    assert "test message" in result
    assert _RESET in result


async def test_color_renderer_with_step() -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "starting", "step": "START"})
    assert "[START]" in result
    assert "starting" in result


async def test_color_renderer_with_extras() -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "test", "key": "value", "num": 42})
    assert "key=value" in result
    assert "num=42" in result


async def test_color_renderer_truncates_long_event() -> None:
    renderer = ColorRenderer()
    long_event = "x" * 200
    result = renderer(None, "info", {"event": long_event})
    assert "x" * _MAX_TEXT_LEN in result
    assert "x" * (_MAX_TEXT_LEN + 1) not in result


async def test_color_renderer_error_level_color() -> None:
    renderer = ColorRenderer()
    error_color = _LEVEL_COLORS["error"]
    result = renderer(None, "error", {"event": "failure"})
    assert error_color in result


async def test_color_renderer_step_color_override() -> None:
    renderer = ColorRenderer()
    ok_color = _STEP_COLORS["OK"]
    result = renderer(None, "info", {"event": "done", "step": "OK"})
    assert ok_color in result


async def test_color_renderer_skips_none_extras() -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "test", "key": None})
    assert "key=" not in result


async def test_color_renderer_skips_internal_keys() -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "test", "timestamp": "123", "level": "info", "logger": "x"})
    assert "timestamp=" not in result
    assert "level=" not in result
    assert "logger=" not in result


##### CONFIGURE LOGGING #####


async def test_configure_logging_does_not_raise() -> None:
    configure_logging("info")


async def test_configure_logging_custom_level() -> None:
    configure_logging("debug")
    configure_logging("warning")


##### LOGGER SINGLETON #####


async def test_logger_exists() -> None:
    assert logger is not None


@pytest.mark.parametrize(
    "step",
    list(_STEP_COLORS.keys()),
    ids=list(_STEP_COLORS.keys()),
)
async def test_color_renderer_all_steps(step: str) -> None:
    renderer = ColorRenderer()
    result = renderer(None, "info", {"event": "test", "step": step})
    assert f"[{step}]" in result
    assert _STEP_COLORS[step] in result

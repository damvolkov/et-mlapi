"""Tests for events/sample_adapter.py."""

from unittest.mock import AsyncMock, patch

from et_mlapi.core.lifespan import State
from et_mlapi.events.sample_adapter import SampleAdapterEvent

##### SAMPLE ADAPTER EVENT #####


async def test_sample_adapter_event_name() -> None:
    assert SampleAdapterEvent.name == "sample_adapter"


async def test_sample_adapter_event_has_shutdown() -> None:
    assert SampleAdapterEvent.has_shutdown() is True


async def test_sample_adapter_event_startup() -> None:
    event = SampleAdapterEvent()
    event.state = State()

    with patch("et_mlapi.adapters.sample.SampleHTTPAdapter.startup", new_callable=AsyncMock):
        adapter = await event.startup()
        assert adapter is not None


async def test_sample_adapter_event_shutdown() -> None:
    event = SampleAdapterEvent()
    event.state = State()

    mock_adapter = AsyncMock()
    await event.shutdown(mock_adapter)
    mock_adapter.shutdown.assert_awaited_once()

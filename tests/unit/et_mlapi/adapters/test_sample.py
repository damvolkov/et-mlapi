"""Tests for adapters/sample.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from et_mlapi.adapters.sample import SampleHTTPAdapter

##### SAMPLE HTTP ADAPTER #####


async def test_sample_adapter_init() -> None:
    adapter = SampleHTTPAdapter(base_url="https://example.com", timeout=5.0)
    assert adapter._base_url == "https://example.com"
    assert adapter._timeout == 5.0
    assert adapter._client is None


async def test_sample_adapter_startup() -> None:
    adapter = SampleHTTPAdapter()
    await adapter.startup()
    assert adapter._client is not None
    await adapter.shutdown()


async def test_sample_adapter_shutdown() -> None:
    adapter = SampleHTTPAdapter()
    await adapter.startup()
    await adapter.shutdown()
    assert adapter._client is None


async def test_sample_adapter_shutdown_no_client() -> None:
    adapter = SampleHTTPAdapter()
    await adapter.shutdown()
    assert adapter._client is None


async def test_sample_adapter_health_disconnected() -> None:
    adapter = SampleHTTPAdapter()
    result = await adapter.health()
    assert result["status"] == "disconnected"


async def test_sample_adapter_health_connected() -> None:
    adapter = SampleHTTPAdapter()
    adapter._client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    adapter._client.get = AsyncMock(return_value=mock_resp)

    result = await adapter.health()
    assert result["status"] == "healthy"
    assert result["status_code"] == 200


async def test_sample_adapter_health_error() -> None:
    import httpx

    adapter = SampleHTTPAdapter()
    adapter._client = AsyncMock()
    adapter._client.get = AsyncMock(side_effect=httpx.ConnectError("failed"))

    result = await adapter.health()
    assert result["status"] == "unhealthy"
    assert "error" in result


async def test_sample_adapter_get_not_started() -> None:
    adapter = SampleHTTPAdapter()
    with pytest.raises(RuntimeError, match="Adapter not started"):
        await adapter.get("/test")


async def test_sample_adapter_get_success() -> None:
    adapter = SampleHTTPAdapter()
    adapter._client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"key": "value"}
    mock_resp.raise_for_status = MagicMock()
    adapter._client.get = AsyncMock(return_value=mock_resp)

    result = await adapter.get("/test")
    assert result == {"key": "value"}

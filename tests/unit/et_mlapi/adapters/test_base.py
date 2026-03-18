"""Tests for adapters/base.py."""

import pytest

from et_mlapi.adapters.base import BaseAdapter

##### BASE ADAPTER #####


async def test_base_adapter_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseAdapter()  # type: ignore


async def test_base_adapter_subclass() -> None:
    class ConcreteAdapter(BaseAdapter):
        async def startup(self) -> None:
            pass

        async def shutdown(self) -> None:
            pass

        async def health(self) -> dict:
            return {"status": "ok"}

    adapter = ConcreteAdapter()
    await adapter.startup()
    result = await adapter.health()
    assert result["status"] == "ok"
    await adapter.shutdown()

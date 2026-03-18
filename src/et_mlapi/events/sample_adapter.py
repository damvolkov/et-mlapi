"""Sample adapter lifespan event — demonstrates adapter in app state."""

from et_mlapi.adapters.sample import SampleHTTPAdapter
from et_mlapi.core.lifespan import BaseEvent


class SampleAdapterEvent(BaseEvent[SampleHTTPAdapter]):
    """Manages SampleHTTPAdapter lifecycle in app state."""

    name = "sample_adapter"

    async def startup(self) -> SampleHTTPAdapter:
        """Create and start the sample adapter."""
        adapter = SampleHTTPAdapter()
        await adapter.startup()
        return adapter

    async def shutdown(self, instance: SampleHTTPAdapter) -> None:
        """Shutdown the sample adapter."""
        await instance.shutdown()

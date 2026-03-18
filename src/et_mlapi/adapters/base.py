"""Base adapter for external service clients."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Abstract base for adapters that manage external service connections."""

    @abstractmethod
    async def startup(self) -> None:
        """Initialize the adapter (open connections, warm caches)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup the adapter (close connections, release resources)."""
        ...

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return health status of the external service."""
        ...

"""Sample HTTP adapter — demonstrates adapter lifecycle and httpx usage."""

from typing import Any

import httpx

from et_mlapi.adapters.base import BaseAdapter
from et_mlapi.core.logger import logger


class SampleHTTPAdapter(BaseAdapter):
    """HTTP adapter using httpx.AsyncClient for external API calls."""

    def __init__(self, base_url: str = "https://httpbin.org", timeout: float = 10.0) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def startup(self) -> None:
        """Create the httpx async client."""
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        logger.info("sample adapter started", step="ADAPTER", base_url=self._base_url)

    async def shutdown(self) -> None:
        """Close the httpx async client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("sample adapter stopped", step="ADAPTER")

    async def health(self) -> dict[str, Any]:
        """Check if the external service is reachable."""
        if not self._client:
            return {"status": "disconnected", "base_url": self._base_url}
        try:
            resp = await self._client.get("/get")
            return {"status": "healthy", "base_url": self._base_url, "status_code": resp.status_code}
        except httpx.HTTPError as exc:
            return {"status": "unhealthy", "base_url": self._base_url, "error": str(exc)}

    async def get(self, path: str) -> dict[str, Any]:
        """Perform a GET request to the external service."""
        if not self._client:
            raise RuntimeError("Adapter not started. Call startup() first.")
        resp = await self._client.get(path)
        resp.raise_for_status()
        return resp.json()

"""Integration tests for health endpoint."""

import httpx
import pytest


@pytest.mark.slow
async def test_health_returns_200(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


@pytest.mark.slow
async def test_health_content_type(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health")
    assert "application/json" in resp.headers.get("content-type", "")

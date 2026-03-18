"""Integration tests for sample API endpoints."""

import httpx
import pytest


@pytest.mark.slow
async def test_sample_http_post(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.post("/sample/http", json={"message": "hello", "repeat": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "hello hello"
    assert data["transport"] == "http"


@pytest.mark.slow
async def test_sample_http_get_path_param(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/sample/http/test-item")
    assert resp.status_code == 200
    data = resp.json()
    assert "test-item" in data["result"]


@pytest.mark.slow
async def test_sample_sse(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/sample/sse")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


@pytest.mark.slow
async def test_sample_stream(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.post("/sample/stream", json={"message": "hello world"})
    assert resp.status_code == 200

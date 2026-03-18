"""Tests for api/health.py."""

from et_mlapi.models.api import HealthResponse

##### HEALTH ENDPOINT MODEL #####


async def test_health_response_model() -> None:
    resp = HealthResponse(status="healthy", service="et-mlapi", version="0.0.0")
    assert resp.status == "healthy"
    assert resp.service == "et-mlapi"
    assert resp.version == "0.0.0"


async def test_health_response_serialization() -> None:
    resp = HealthResponse(status="healthy", service="test", version="1.0")
    data = resp.model_dump()
    assert data == {"status": "healthy", "service": "test", "version": "1.0"}

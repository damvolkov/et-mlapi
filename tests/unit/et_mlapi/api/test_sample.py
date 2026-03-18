"""Tests for api/sample.py — endpoint handler logic."""

from et_mlapi.models.api import SampleRequest, SampleResponse

##### SAMPLE HTTP HANDLER LOGIC #####


async def test_sample_http_handler_logic() -> None:
    req = SampleRequest(message="hello", repeat=3)
    result = " ".join([req.message] * req.repeat)
    resp = SampleResponse(result=result, transport="http")
    assert resp.result == "hello hello hello"
    assert resp.transport == "http"


async def test_sample_http_handler_single_repeat() -> None:
    req = SampleRequest(message="test")
    result = " ".join([req.message] * req.repeat)
    resp = SampleResponse(result=result, transport="http")
    assert resp.result == "test"

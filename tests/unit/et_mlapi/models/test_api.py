"""Tests for models/api.py."""

import pytest
from pydantic import ValidationError

from et_mlapi.models.api import (
    HealthResponse,
    SampleRequest,
    SampleResponse,
    SSEEvent,
    StreamChunk,
    WSMessage,
    WSResponse,
)

##### HEALTH RESPONSE #####


async def test_health_response() -> None:
    resp = HealthResponse(status="healthy", service="test", version="1.0.0")
    assert resp.status == "healthy"
    assert resp.service == "test"


##### SAMPLE REQUEST #####


async def test_sample_request_defaults() -> None:
    req = SampleRequest(message="hello")
    assert req.repeat == 1


async def test_sample_request_validation_empty_message() -> None:
    with pytest.raises(ValidationError):
        SampleRequest(message="")


async def test_sample_request_validation_repeat_bounds() -> None:
    with pytest.raises(ValidationError):
        SampleRequest(message="test", repeat=0)
    with pytest.raises(ValidationError):
        SampleRequest(message="test", repeat=11)


##### SAMPLE RESPONSE #####


async def test_sample_response() -> None:
    resp = SampleResponse(result="ok", transport="http")
    assert resp.transport == "http"


##### SSE EVENT #####


async def test_sse_event_defaults() -> None:
    event = SSEEvent(data="payload")
    assert event.event == "message"
    assert event.data == "payload"


##### STREAM CHUNK #####


async def test_stream_chunk_defaults() -> None:
    chunk = StreamChunk(index=0, content="word")
    assert chunk.done is False


async def test_stream_chunk_done() -> None:
    chunk = StreamChunk(index=5, content="", done=True)
    assert chunk.done is True


##### WS MESSAGE #####


async def test_ws_message_defaults() -> None:
    msg = WSMessage()
    assert msg.action == "echo"
    assert msg.payload == ""


async def test_ws_message_custom() -> None:
    msg = WSMessage(action="upper", payload="hello")
    assert msg.action == "upper"


##### WS RESPONSE #####


async def test_ws_response_transport() -> None:
    resp = WSResponse(action="echo", payload="test")
    assert resp.transport == "websocket"

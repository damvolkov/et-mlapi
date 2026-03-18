"""Tests for websockets/sample.py — handler logic."""

import orjson

from et_mlapi.models.api import WSMessage
from et_mlapi.websockets.sample import on_close, on_connect, on_message, ws_sample

##### WEBSOCKET DEFINITION #####


async def test_ws_sample_endpoint() -> None:
    assert ws_sample.endpoint == "/ws/sample"


async def test_ws_sample_has_handlers() -> None:
    assert "connect" in ws_sample.handlers
    assert "message" in ws_sample.handlers
    assert "close" in ws_sample.handlers


##### CONNECT / CLOSE HANDLERS #####


async def test_ws_on_connect() -> None:
    result = await on_connect(None)
    assert result == ""


async def test_ws_on_close() -> None:
    result = await on_close(None)
    assert result == ""


##### MESSAGE HANDLER #####


async def test_ws_on_message_echo() -> None:
    msg = WSMessage(action="echo", payload="hello").model_dump_json()
    result = await on_message(None, msg)
    data = orjson.loads(result)
    assert data["action"] == "echo"
    assert data["payload"] == "hello"


async def test_ws_on_message_upper() -> None:
    msg = WSMessage(action="upper", payload="hello").model_dump_json()
    result = await on_message(None, msg)
    data = orjson.loads(result)
    assert data["action"] == "upper"
    assert data["payload"] == "HELLO"


async def test_ws_on_message_reverse() -> None:
    msg = WSMessage(action="reverse", payload="abc").model_dump_json()
    result = await on_message(None, msg)
    data = orjson.loads(result)
    assert data["action"] == "reverse"
    assert data["payload"] == "cba"


async def test_ws_on_message_unknown_action() -> None:
    msg = WSMessage(action="unknown", payload="x").model_dump_json()
    result = await on_message(None, msg)
    data = orjson.loads(result)
    assert data["action"] == "error"
    assert "unknown action" in data["payload"]


async def test_ws_on_message_invalid_json() -> None:
    result = await on_message(None, "not json{")
    data = orjson.loads(result)
    assert "error" in data


async def test_ws_on_message_empty_payload() -> None:
    msg = WSMessage(action="echo", payload="").model_dump_json()
    result = await on_message(None, msg)
    data = orjson.loads(result)
    assert data["action"] == "echo"
    assert data["payload"] == ""

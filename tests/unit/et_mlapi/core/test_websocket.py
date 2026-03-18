"""Tests for core/websocket.py."""

from unittest.mock import MagicMock

import pytest

from et_mlapi.core.websocket import BaseWebSocket, WebSocketHandler

##### BASE WEBSOCKET #####


async def test_base_websocket_endpoint() -> None:
    ws = BaseWebSocket("/ws/test")
    assert ws.endpoint == "/ws/test"
    assert ws.handlers == {}


async def test_base_websocket_register_handler() -> None:
    ws = BaseWebSocket("/ws/test")

    @ws.on("connect")
    async def on_connect(ws_conn):
        return ""

    assert "connect" in ws.handlers
    assert ws.handlers["connect"] is on_connect


async def test_base_websocket_register_multiple_handlers() -> None:
    ws = BaseWebSocket("/ws/test")

    @ws.on("connect")
    async def on_connect(ws_conn):
        return ""

    @ws.on("message")
    async def on_message(ws_conn, msg):
        return msg

    @ws.on("close")
    async def on_close(ws_conn):
        return ""

    assert len(ws.handlers) == 3
    assert "connect" in ws.handlers
    assert "message" in ws.handlers
    assert "close" in ws.handlers


async def test_base_websocket_invalid_event() -> None:
    ws = BaseWebSocket("/ws/test")
    with pytest.raises(ValueError, match="Invalid event type"):

        @ws.on("invalid")  # type: ignore
        async def handler(ws_conn):
            return ""


async def test_base_websocket_handlers_property() -> None:
    ws = BaseWebSocket("/ws/test")

    @ws.on("message")
    async def on_message(ws_conn, msg):
        return msg

    handlers = ws.handlers
    assert isinstance(handlers, dict)
    assert "message" in handlers


##### WEBSOCKET HANDLER #####


async def test_websocket_handler_register_missing_message() -> None:
    app = MagicMock()
    handler = WebSocketHandler(app)
    ws = BaseWebSocket("/ws/test")

    @ws.on("connect")
    async def on_connect(ws_conn):
        return ""

    with pytest.raises(ValueError, match="must have a 'message' handler"):
        handler.register(ws)


async def test_websocket_handler_register_success() -> None:
    app = MagicMock()
    mock_ws_instance = MagicMock()
    mock_ws_instance.methods = {}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("et_mlapi.core.websocket.WebSocket", lambda app, ep: mock_ws_instance)

        handler = WebSocketHandler(app)
        ws = BaseWebSocket("/ws/test")

        @ws.on("message")
        async def on_message(ws_conn, msg):
            return msg

        @ws.on("connect")
        async def on_connect(ws_conn):
            return ""

        result = handler.register(ws)
        assert result is handler
        assert len(handler._registered) == 1
        app.add_web_socket.assert_called_once()


async def test_websocket_handler_prefix() -> None:
    app = MagicMock()
    mock_ws_instance = MagicMock()
    mock_ws_instance.methods = {}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("et_mlapi.core.websocket.WebSocket", lambda app, ep: mock_ws_instance)

        handler = WebSocketHandler(app, prefix="/v1")
        ws = BaseWebSocket("/ws/test")

        @ws.on("message")
        async def on_message(ws_conn, msg):
            return msg

        handler.register(ws)
        app.add_web_socket.assert_called_once_with("/v1/ws/test", mock_ws_instance)


async def test_websocket_handler_inject_dependencies() -> None:
    app = MagicMock()
    mock_ws = MagicMock()
    mock_func_info = MagicMock()
    mock_func_info.args = {"state": None}
    mock_func_info.kwargs = {}
    mock_ws.methods = {"message": mock_func_info}
    mock_ws.dependencies.get_dependency_map.return_value = {"state": "test_state"}

    app.dependencies.get_global_dependencies.return_value = {"state": "test_state"}

    handler = WebSocketHandler(app)
    handler._registered = [mock_ws]
    handler.inject_dependencies()

    mock_ws.dependencies.add_global_dependency.assert_called()

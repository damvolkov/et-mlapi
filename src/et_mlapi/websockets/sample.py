"""Sample WebSocket endpoint — echo with action dispatch."""

import orjson

from et_mlapi.core.logger import logger
from et_mlapi.core.websocket import BaseWebSocket
from et_mlapi.models.api import WSMessage, WSResponse

ws_sample = BaseWebSocket("/ws/sample")


@ws_sample.on("connect")
async def on_connect(ws) -> str:
    logger.info("websocket connected", step="WS", endpoint="/ws/sample")
    return ""


@ws_sample.on("message")
async def on_message(ws, msg: str) -> str:
    """Parse inbound JSON, dispatch by action, return JSON response."""
    try:
        parsed = WSMessage.model_validate_json(msg)
    except Exception:
        return orjson.dumps({"error": "invalid_message", "detail": "Expected JSON with action and payload"}).decode()

    match parsed.action:
        case "echo":
            response = WSResponse(action="echo", payload=parsed.payload)
        case "upper":
            response = WSResponse(action="upper", payload=parsed.payload.upper())
        case "reverse":
            response = WSResponse(action="reverse", payload=parsed.payload[::-1])
        case _:
            response = WSResponse(action="error", payload=f"unknown action: {parsed.action}")

    return response.model_dump_json()


@ws_sample.on("close")
async def on_close(ws) -> str:
    logger.info("websocket disconnected", step="WS", endpoint="/ws/sample")
    return ""

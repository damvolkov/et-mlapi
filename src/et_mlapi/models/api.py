"""API models — transport-specific request/response schemas."""

from pydantic import BaseModel, Field

##### HEALTH #####


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


##### HTTP TRANSPORT #####


class SampleRequest(BaseModel):
    """Sample HTTP request body for demonstration."""

    message: str = Field(min_length=1, max_length=500)
    repeat: int = Field(default=1, ge=1, le=10)


class SampleResponse(BaseModel):
    """Sample HTTP response body."""

    result: str
    transport: str


##### SSE TRANSPORT #####


class SSEEvent(BaseModel):
    """Single Server-Sent Event payload."""

    event: str = "message"
    data: str


##### STREAMING TRANSPORT #####


class StreamChunk(BaseModel):
    """Single chunk in a streaming response."""

    index: int
    content: str
    done: bool = False


##### WEBSOCKET TRANSPORT #####


class WSMessage(BaseModel):
    """WebSocket inbound message schema."""

    action: str = "echo"
    payload: str = ""


class WSResponse(BaseModel):
    """WebSocket outbound message schema."""

    action: str
    payload: str
    transport: str = "websocket"

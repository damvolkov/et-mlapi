"""Sample endpoints demonstrating all HTTP transports: HTTP, SSE, and streaming."""

import asyncio
from collections.abc import AsyncGenerator

import orjson
from robyn import StreamingResponse, status_codes
from robyn.robyn import Headers

from et_mlapi.core.router import Router
from et_mlapi.models.api import SampleRequest, SampleResponse

router = Router(__file__, prefix="/sample")


##### HTTP TRANSPORT #####


@router.post("/http")
async def sample_http(body: SampleRequest) -> SampleResponse:
    """Standard HTTP request/response — JSON in, JSON out."""
    result = " ".join([body.message] * body.repeat)
    return SampleResponse(result=result, transport="http")


@router.get("/http/:item_id")
async def sample_http_get(item_id: str) -> SampleResponse:
    """GET with path parameter — demonstrates Router path param extraction."""
    return SampleResponse(result=f"item={item_id}", transport="http")


##### SSE TRANSPORT #####


@router.get("/sse")
async def sample_sse() -> StreamingResponse:
    """Server-Sent Events — periodic event stream."""

    async def generate() -> AsyncGenerator[str, None]:
        for i in range(5):
            data = orjson.dumps({"index": i, "content": f"event-{i}"}).decode()
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.3)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        content=generate(),
        status_code=status_codes.HTTP_200_OK,
        headers=Headers({"content-type": "text/event-stream", "cache-control": "no-cache"}),
    )


##### STREAMING TRANSPORT #####


@router.post("/stream")
async def sample_stream(body: SampleRequest) -> StreamingResponse:
    """Chunked streaming — sends chunks of data progressively."""

    async def generate() -> AsyncGenerator[str, None]:
        words = body.message.split()
        for i, word in enumerate(words):
            chunk = orjson.dumps({"index": i, "content": word, "done": False}).decode()
            yield chunk + "\n"
            await asyncio.sleep(0.2)
        yield orjson.dumps({"index": len(words), "content": "", "done": True}).decode() + "\n"

    return StreamingResponse(
        content=generate(),
        status_code=status_codes.HTTP_200_OK,
        headers=Headers({"content-type": "application/x-ndjson"}),
    )

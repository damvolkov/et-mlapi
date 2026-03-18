---
name: robyn
description: Robyn web framework patterns. App init, SubRouters, middleware, WebSockets, Pydantic integration, auth guards, DI, exception handling, const routes, scaling, logging. Use when working with Robyn.
---

# Robyn Patterns

## App Init & Lifespan

```python
from robyn import Robyn, ALLOW_CORS
from app.core.settings import settings as st

app = Robyn(__file__)
ALLOW_CORS(app, origins=st.CORS_ORIGINS)

@app.startup_handler
async def startup():
    app.inject_global(
        REDIS=await RedisConnection.get(),
        EMBED=AzureOpenAITextVectorizer(model=st.EMBED_MODEL),
    )

@app.shutdown_handler
async def shutdown():
    if (r := app.dependencies.get("REDIS")) is not None:
        await r.client.close()
```

Global state via inject_global() — accessible in handlers via global_dependencies.

## SubRouters

One per domain. Prefix includes API version. __file__ required as first arg.

```python
from robyn import SubRouter

router = SubRouter(__file__, prefix="/api/v1/tokens")

@router.post("/")
async def create_token(request: Request, body: RequestBody) -> dict:
    payload = TokenRequest.model_validate_json(body)
    token = generate_token(payload.identity, payload.room_name)
    return TokenResponse(token=token).model_dump()
```

Register: `app.include_router(router)`. Specific routes before generic (:id last).

## Middleware

before_request receives Request, must return Request (or Response to short-circuit).
after_request receives (Request, Response), must return Response.

```python
import time
from robyn import Request, Response

@app.before_request()
async def request_timer(request: Request) -> Request:
    request.headers.set("x-start-time", str(time.monotonic()))
    return request

@app.after_request()
async def response_timer(request: Request, response: Response) -> Response:
    if (start := request.headers.get("x-start-time")):
        duration = time.monotonic() - float(start)
        response.headers.set("x-response-time", f"{duration:.4f}s")
    return response

@app.before_request()
async def correlation_id(request: Request) -> Request:
    trace_id = request.headers.get("x-trace-id") or str(uuid4())
    request.headers.set("x-trace-id", trace_id)
    return request
```

Path-scoped: `@app.before_request("/admin")`.

## Auth Guards

```python
from robyn.authentication import AuthenticationHandler, BearerGetter, Identity
from app.core.security import verify_jwt

class JWTAuthHandler(AuthenticationHandler):
    def authenticate(self, request: Request) -> Identity | None:
        token = self.token_getter.get_token(request)
        if not token:
            return None
        if (claims := verify_jwt(token)) is None:
            return None
        return Identity(claims=claims)

app.configure_authentication(JWTAuthHandler(token_getter=BearerGetter()))
```

Protected routes: `@router.get("/protected", auth_required=True)`.
Access claims: `request.identity.claims`. Per-SubRouter: `router.configure_authentication(...)`.

## Dependency Injection

Global (app-wide) and router-scoped. Reserved param names: global_dependencies, router_dependencies.

```python
# global
app.inject_global(REDIS=redis_client, SETTINGS=settings)

@app.get("/health")
async def health(request: Request, global_dependencies: dict) -> dict:
    redis = global_dependencies["REDIS"]
    return {"status": "healthy" if await redis.ping() else "degraded"}

# router-scoped
router = SubRouter(__file__, prefix="/api/v1/store")
router.inject(STORE=knowledge_store)

@router.get("/search")
async def search(request: Request, query_params: QueryParams, router_dependencies: dict) -> dict:
    store = router_dependencies["STORE"]
    return {"results": await store.search(query_params.get("q", ""))}
```

inject_global for cross-cutting (redis, settings). inject for domain-scoped.

## WebSocket

```python
from robyn import WebSocket

websocket = WebSocket(app, "/ws/events")

@websocket.on("connect")
async def ws_connect(ws) -> str:
    logger.info("🔌 WS_CONNECT", extra={"ws_id": ws.id})
    return "connected"

@websocket.on("message")
async def ws_message(ws, msg: str, global_dependencies: dict) -> str:
    redis = global_dependencies["REDIS"]
    match orjson.loads(msg):
        case {"type": "broadcast", "data": data}:
            await ws.async_broadcast(orjson.dumps(data).decode())
            return ""
        case {"type": "direct", "target": target_id, "data": data}:
            await ws.async_send_to(target_id, orjson.dumps(data).decode())
            return ""
        case _:
            return orjson.dumps({"error": "unknown_message_type"}).decode()

@websocket.on("close")
async def ws_close(ws) -> None:
    logger.info("🔌 WS_CLOSE", extra={"ws_id": ws.id})
```

Return str to auto-reply, None to silently process. ws.close() for server-initiated disconnect.

## Pydantic Integration

Manual validation via model_validate_json on body:

```python
from robyn import Response
from robyn.types import RequestBody

@router.post("/tokens")
async def create_token(request: Request, body: RequestBody) -> Response:
    try:
        payload = TokenRequest.model_validate_json(body)
    except ValidationError as exc:
        return Response(
            status_code=422,
            description=orjson.dumps({"errors": exc.errors()}).decode(),
            headers={"content-type": "application/json"},
        )
    token = await generate_token(payload)
    result = TokenResponse(token=token.jwt, expires_at=token.exp)
    return Response(
        status_code=201,
        description=result.model_dump_json(),
        headers={"content-type": "application/json"},
    )
```

## Exception Handling

Single @app.exception handler with match-case dispatch:

```python
@app.exception
def handle_exception(error: Exception) -> Response:
    match error:
        case BaseAppException():
            return Response(
                status_code=error.status_code,
                description=orjson.dumps({
                    "type": type(error).__name__,
                    "status": error.status_code,
                    "title": error.title,
                    "detail": error.message,
                }).decode(),
                headers={"content-type": "application/json"},
            )
        case _:
            logger.error("❌ UNHANDLED_ERROR", extra={"error": str(error)})
            return Response(
                status_code=500,
                description=orjson.dumps({
                    "type": "InternalServerError",
                    "status": 500,
                    "title": "Internal Server Error",
                    "detail": "An unexpected error occurred",
                }).decode(),
                headers={"content-type": "application/json"},
            )
```

Never leak stack traces in production.

## Parameter Injection

Robyn introspects handler signatures — inject only what you need:

```python
from robyn import Request, Headers
from robyn.types import PathParams, QueryParams, RequestBody, FormData, RequestFiles, RequestIP

@router.post("/users/:user_id/posts")
async def create_post(
    request: Request, path_params: PathParams,
    query_params: QueryParams, headers: Headers, body: RequestBody,
) -> dict:
    user_id = path_params["user_id"]
    draft = query_params.get("draft", "false") == "true"
    return {"user_id": user_id, "draft": draft}
```

PathParams is dict[str, str] — always string values, cast explicitly.

## Const Routes & Scaling

```python
@app.get("/health", const=True)
async def health_check() -> dict:
    return {"status": "healthy", "version": st.API_VERSION}
```

const=True: response cached in Rust memory, zero Python at runtime. Only for truly static responses.

Scaling: --dev (single, hot-reload), --fast (auto-optimized), --processes N --workers M (CPU vs I/O).

## Full Assembly

```python
app = Robyn(__file__)
ALLOW_CORS(app, origins=st.CORS_ORIGINS)
app.configure_authentication(JWTAuthHandler(token_getter=BearerGetter()))
app.before_request()(request_timer)
app.before_request()(correlation_id)
app.after_request()(response_timer)
app.exception(handle_exception)
app.include_router(health_router)
app.include_router(token_router)
app.startup_handler(startup)
app.shutdown_handler(shutdown)

if __name__ == "__main__":
    app.start(host=st.HOST, port=st.PORT)
```

Order: app + CORS → auth → middleware → exceptions → routers → lifecycle → start.

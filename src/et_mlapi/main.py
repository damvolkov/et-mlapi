"""et-mlapi — Production-ready ML API template powered by Robyn."""

from robyn import Robyn

from et_mlapi.api.health import router as health_router
from et_mlapi.api.sample import router as sample_router
from et_mlapi.core.lifespan import create_lifespan
from et_mlapi.core.logger import logger
from et_mlapi.core.settings import settings as st
from et_mlapi.core.websocket import WebSocketHandler
from et_mlapi.events.process_pool import ProcessPoolEvent
from et_mlapi.events.sample_adapter import SampleAdapterEvent
from et_mlapi.middlewares.base import MiddlewareHandler
from et_mlapi.middlewares.files import FileUploadOpenAPIMiddleware
from et_mlapi.middlewares.swagger import SwaggerBrandingMiddleware
from et_mlapi.websockets.sample import ws_sample

app = Robyn(__file__)

##### LIFESPAN #####

lifespan = create_lifespan(app)
lifespan.register(ProcessPoolEvent)
lifespan.register(SampleAdapterEvent)

##### WEBSOCKETS #####

websockets = WebSocketHandler(app)
websockets.register(ws_sample)


##### STARTUP / SHUTDOWN #####


async def startup() -> None:
    """Startup: lifespan events, then inject WS dependencies."""
    await lifespan.startup()
    websockets.inject_dependencies()


app.startup_handler(startup)
app.shutdown_handler(lifespan.shutdown)

##### MIDDLEWARES #####

middlewares = MiddlewareHandler(app)
middlewares.register(FileUploadOpenAPIMiddleware)
middlewares.register(SwaggerBrandingMiddleware)

##### ROUTERS #####

app.include_router(health_router)
app.include_router(sample_router)


##### ENTRYPOINT #####


def main() -> None:
    logger.info("starting server", name=st.API_NAME, host=st.system.host, port=st.system.port, step="START")
    app.start(host=st.system.host, port=st.system.port)


if __name__ == "__main__":
    main()

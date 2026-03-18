"""Health check endpoint."""

from et_mlapi.core.logger import logger
from et_mlapi.core.router import Router
from et_mlapi.core.settings import settings as st
from et_mlapi.models.api import HealthResponse

router = Router(__file__)


@router.get("/health")
async def health_check() -> HealthResponse:
    logger.info("health check requested", step="OK")
    return HealthResponse(status="healthy", service=st.API_NAME, version=st.API_VERSION)

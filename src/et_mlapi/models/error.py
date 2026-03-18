"""Error response models — structured and simple formats."""

from pydantic import BaseModel
from robyn import Response

##### STRUCTURED #####


class ErrorDetail(BaseModel):
    """Inner error object for structured error responses."""

    message: str
    type: str = "invalid_request_error"
    param: str | None = None
    code: str | None = None


class ErrorEnvelope(BaseModel):
    """Structured error wrapper: {"error": {"message": ...}}."""

    error: ErrorDetail


##### SIMPLE #####


class ErrorResponse(BaseModel):
    """Simple error response for internal endpoints."""

    error: str
    detail: str | None = None


##### FACTORY #####


def error_response(
    status_code: int,
    message: str,
    *,
    error_type: str = "invalid_request_error",
    detail: str | None = None,
    simple: bool = False,
) -> Response:
    """Build error Response — structured by default, simple if flagged."""
    if simple:
        body = ErrorResponse(error=message, detail=detail).model_dump_json()
    else:
        body = ErrorEnvelope(
            error=ErrorDetail(message=message, type=error_type),
        ).model_dump_json()

    return Response(status_code=status_code, headers={"content-type": "application/json"}, description=body)

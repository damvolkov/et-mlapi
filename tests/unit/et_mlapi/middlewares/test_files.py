"""Tests for middlewares/files.py."""

from unittest.mock import MagicMock

import orjson
from robyn import Response

from et_mlapi.core.router import FILE_UPLOAD_ENDPOINTS
from et_mlapi.middlewares.files import FileUploadOpenAPIMiddleware

##### FILE UPLOAD OPENAPI MIDDLEWARE #####


async def test_files_middleware_before_passthrough() -> None:
    app = MagicMock()
    mw = FileUploadOpenAPIMiddleware(app)
    request = MagicMock()
    result = mw.before(request)
    assert result is request


async def test_files_middleware_after_no_endpoints() -> None:
    app = MagicMock()
    mw = FileUploadOpenAPIMiddleware(app)
    FILE_UPLOAD_ENDPOINTS.clear()
    response = Response(status_code=200, headers={}, description='{"paths": {}}')
    result = mw.after(response)
    assert result is response


async def test_files_middleware_after_patches_spec() -> None:
    app = MagicMock()
    mw = FileUploadOpenAPIMiddleware(app)
    FILE_UPLOAD_ENDPOINTS.clear()
    FILE_UPLOAD_ENDPOINTS.add("/upload")

    spec = {"paths": {"/upload": {"post": {"summary": "Upload"}}}}
    response = Response(status_code=200, headers={}, description=orjson.dumps(spec).decode())
    result = mw.after(response)

    patched = orjson.loads(result.description)
    assert "requestBody" in patched["paths"]["/upload"]["post"]
    rb = patched["paths"]["/upload"]["post"]["requestBody"]
    assert "multipart/form-data" in rb["content"]

    FILE_UPLOAD_ENDPOINTS.clear()


async def test_files_middleware_after_invalid_json() -> None:
    app = MagicMock()
    mw = FileUploadOpenAPIMiddleware(app)
    FILE_UPLOAD_ENDPOINTS.clear()
    FILE_UPLOAD_ENDPOINTS.add("/upload")

    response = Response(status_code=200, headers={}, description="not json")
    result = mw.after(response)
    assert result.description == "not json"

    FILE_UPLOAD_ENDPOINTS.clear()


async def test_files_middleware_endpoints() -> None:
    assert FileUploadOpenAPIMiddleware.endpoints == frozenset(["/openapi.json"])

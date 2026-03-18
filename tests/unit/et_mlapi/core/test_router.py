"""Tests for core/router.py."""

import inspect

import orjson
import pytest
from pydantic import BaseModel
from robyn import Response, StreamingResponse, status_codes
from robyn.robyn import Headers

from et_mlapi.core.router import (
    FILE_UPLOAD_ENDPOINTS,
    parse_endpoint_signature,
    parse_request_body,
    parse_request_files,
    parse_response,
)
from et_mlapi.models.core import BodyType, UploadFile

##### PARSE ENDPOINT SIGNATURE #####


class SampleModel(BaseModel):
    name: str
    age: int


async def test_parse_signature_pydantic_model() -> None:
    async def handler(body: SampleModel) -> None: ...

    sig = inspect.signature(handler)
    body_config, file_params = parse_endpoint_signature(sig)
    assert "body" in body_config
    assert body_config["body"][0] == BodyType.PYDANTIC
    assert len(file_params) == 0


async def test_parse_signature_dict_type() -> None:
    async def handler(body: dict) -> None: ...

    sig = inspect.signature(handler)
    body_config, file_params = parse_endpoint_signature(sig)
    assert "body" in body_config
    assert body_config["body"][0] == BodyType.JSONABLE


async def test_parse_signature_upload_file() -> None:
    async def handler(files: UploadFile) -> None: ...

    sig = inspect.signature(handler)
    body_config, file_params = parse_endpoint_signature(sig)
    assert "files" in file_params
    assert "files" not in body_config


async def test_parse_signature_body_param_name() -> None:
    async def handler(body) -> None: ...

    sig = inspect.signature(handler)
    body_config, file_params = parse_endpoint_signature(sig)
    assert "body" in body_config
    assert body_config["body"][0] == BodyType.JSONABLE


async def test_parse_signature_no_special_params() -> None:
    async def handler(request, some_str: str) -> None: ...

    sig = inspect.signature(handler)
    body_config, file_params = parse_endpoint_signature(sig)
    assert len(body_config) == 0
    assert len(file_params) == 0


##### PARSE REQUEST BODY #####


async def test_parse_body_pydantic_valid() -> None:
    body_config = {"data": (BodyType.PYDANTIC, SampleModel)}
    kwargs = {"data": '{"name": "test", "age": 25}'}
    result = parse_request_body(body_config, kwargs)
    assert result is None
    assert isinstance(kwargs["data"], SampleModel)
    assert kwargs["data"].name == "test"


async def test_parse_body_pydantic_invalid() -> None:
    body_config = {"data": (BodyType.PYDANTIC, SampleModel)}
    kwargs = {"data": '{"name": "test"}'}
    result = parse_request_body(body_config, kwargs)
    assert isinstance(result, Response)
    assert result.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


async def test_parse_body_jsonable_valid() -> None:
    body_config = {"data": (BodyType.JSONABLE, None)}
    kwargs = {"data": '{"key": "value"}'}
    result = parse_request_body(body_config, kwargs)
    assert result is None
    assert kwargs["data"] == {"key": "value"}


async def test_parse_body_jsonable_invalid() -> None:
    body_config = {"data": (BodyType.JSONABLE, None)}
    kwargs = {"data": "not json{"}
    result = parse_request_body(body_config, kwargs)
    assert isinstance(result, Response)
    assert result.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


async def test_parse_body_raw_passthrough() -> None:
    body_config = {"data": (BodyType.RAW, None)}
    kwargs = {"data": "raw content"}
    result = parse_request_body(body_config, kwargs)
    assert result is None
    assert kwargs["data"] == "raw content"


async def test_parse_body_missing_param() -> None:
    body_config = {"data": (BodyType.PYDANTIC, SampleModel)}
    kwargs = {}
    result = parse_request_body(body_config, kwargs)
    assert result is None


async def test_parse_body_non_string_value() -> None:
    body_config = {"data": (BodyType.PYDANTIC, SampleModel)}
    kwargs = {"data": SampleModel(name="test", age=25)}
    result = parse_request_body(body_config, kwargs)
    assert result is None


async def test_parse_body_bytes_input() -> None:
    body_config = {"data": (BodyType.JSONABLE, None)}
    kwargs = {"data": b'{"key": "value"}'}
    result = parse_request_body(body_config, kwargs)
    assert result is None
    assert kwargs["data"] == {"key": "value"}


##### PARSE REQUEST FILES #####


async def test_parse_files_no_file_params(make_mock_request) -> None:
    request = make_mock_request()
    result = parse_request_files(set(), request, {})  # type: ignore[arg-type]
    assert result is None


async def test_parse_files_missing_files(make_mock_request) -> None:
    request = make_mock_request()
    kwargs: dict = {}
    result = parse_request_files({"file"}, request, kwargs)
    assert isinstance(result, Response)
    assert result.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


async def test_parse_files_present(make_mock_request) -> None:
    request = make_mock_request(files={"upload": b"filedata"})
    kwargs: dict = {}
    result = parse_request_files({"upload"}, request, kwargs)
    assert result is None
    assert isinstance(kwargs["upload"], UploadFile)


##### PARSE RESPONSE #####


async def test_parse_response_streaming() -> None:
    async def gen():
        yield "chunk"

    sr = StreamingResponse(content=gen(), status_code=200, headers=Headers({}))
    result = parse_response(sr)
    assert isinstance(result, StreamingResponse)


async def test_parse_response_response() -> None:
    resp = Response(status_code=200, headers={}, description="ok")
    result = parse_response(resp)
    assert isinstance(result, Response)
    assert result.description == "ok"


async def test_parse_response_pydantic_model() -> None:
    model = SampleModel(name="test", age=25)
    result = parse_response(model)
    assert isinstance(result, Response)
    assert result.status_code == status_codes.HTTP_200_OK
    body = orjson.loads(result.description)
    assert body["name"] == "test"


async def test_parse_response_dict() -> None:
    result = parse_response({"key": "value"})
    assert isinstance(result, Response)
    body = orjson.loads(result.description)
    assert body["key"] == "value"


async def test_parse_response_string() -> None:
    result = parse_response("plain text")
    assert isinstance(result, Response)
    assert result.description == "plain text"


async def test_parse_response_number() -> None:
    result = parse_response(42)
    assert isinstance(result, Response)
    assert result.description == "42"


##### FILE UPLOAD ENDPOINTS SET #####


async def test_file_upload_endpoints_is_set() -> None:
    assert isinstance(FILE_UPLOAD_ENDPOINTS, set)


##### ROUTER CLASS #####


async def test_router_class_instantiation() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/test")
    assert router._prefix == "/test"
    assert isinstance(router._handlers, dict)
    assert isinstance(router._originals, dict)


async def test_router_wraps_methods() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/api")
    assert hasattr(router, "get")
    assert hasattr(router, "post")
    assert hasattr(router, "put")
    assert hasattr(router, "delete")


async def test_router_post_handler_registration() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/t")

    @router.post("/data")
    async def handler(body: SampleModel) -> dict:
        return {"name": body.name}

    assert "/t/data" in router._handlers


async def test_router_get_handler_with_path_params() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/t")

    @router.get("/items/:item_id")
    async def handler(item_id: str) -> dict:
        return {"id": item_id}

    assert "/t/items/:item_id" in router._handlers


async def test_router_alias() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/t")

    @router.get("/original")
    async def handler() -> str:
        return "ok"

    router.alias("/original", "/alias1", "/alias2")


async def test_router_alias_missing_source() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/t")
    with pytest.raises(ValueError, match="No handler registered"):
        router.alias("/nonexistent", "/alias")


async def test_router_file_upload_registration() -> None:
    from et_mlapi.core.router import Router

    FILE_UPLOAD_ENDPOINTS.clear()
    router = Router(__file__, prefix="/up")

    @router.post("/file")
    async def handler(files: UploadFile) -> dict:
        return {"ok": True}

    assert "/up/file" in FILE_UPLOAD_ENDPOINTS
    FILE_UPLOAD_ENDPOINTS.clear()


async def test_router_handler_with_request_param() -> None:
    from et_mlapi.core.router import Router

    router = Router(__file__, prefix="/t")

    @router.get("/req")
    async def handler(request) -> str:
        return "ok"

    assert "/t/req" in router._handlers

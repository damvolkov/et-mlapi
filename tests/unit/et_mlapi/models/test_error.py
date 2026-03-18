"""Tests for models/error.py."""

import orjson

from et_mlapi.models.error import ErrorDetail, ErrorEnvelope, ErrorResponse, error_response

##### ERROR DETAIL #####


async def test_error_detail_defaults() -> None:
    detail = ErrorDetail(message="test error")
    assert detail.message == "test error"
    assert detail.type == "invalid_request_error"
    assert detail.param is None
    assert detail.code is None


async def test_error_detail_custom() -> None:
    detail = ErrorDetail(message="bad param", type="validation_error", param="name", code="required")
    assert detail.type == "validation_error"
    assert detail.param == "name"
    assert detail.code == "required"


##### ERROR ENVELOPE #####


async def test_error_envelope_serialization() -> None:
    envelope = ErrorEnvelope(error=ErrorDetail(message="fail"))
    data = orjson.loads(envelope.model_dump_json())
    assert "error" in data
    assert data["error"]["message"] == "fail"


##### ERROR RESPONSE #####


async def test_error_response_simple() -> None:
    resp = ErrorResponse(error="not_found", detail="Item does not exist")
    assert resp.error == "not_found"
    assert resp.detail == "Item does not exist"


async def test_error_response_no_detail() -> None:
    resp = ErrorResponse(error="server_error")
    assert resp.detail is None


##### ERROR RESPONSE FACTORY #####


async def test_error_response_factory_structured() -> None:
    resp = error_response(400, "bad request")
    assert resp.status_code == 400
    body = orjson.loads(resp.description)
    assert "error" in body
    assert body["error"]["message"] == "bad request"


async def test_error_response_factory_simple() -> None:
    resp = error_response(404, "not found", simple=True)
    assert resp.status_code == 404
    body = orjson.loads(resp.description)
    assert body["error"] == "not found"


async def test_error_response_factory_with_detail() -> None:
    resp = error_response(422, "validation failed", detail="field X is required", simple=True)
    body = orjson.loads(resp.description)
    assert body["detail"] == "field X is required"


async def test_error_response_factory_custom_type() -> None:
    resp = error_response(403, "forbidden", error_type="auth_error")
    body = orjson.loads(resp.description)
    assert body["error"]["type"] == "auth_error"

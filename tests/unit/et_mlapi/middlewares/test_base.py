"""Tests for middlewares/base.py."""

from unittest.mock import MagicMock

import pytest
from robyn import Request, Response

from et_mlapi.middlewares.base import BaseMiddleware, MiddlewareHandler

##### BASE MIDDLEWARE #####


async def test_base_middleware_must_implement_one() -> None:
    with pytest.raises(TypeError, match="must implement at least one of before/after"):

        class BadMiddleware(BaseMiddleware):
            pass


async def test_base_middleware_before_only() -> None:
    class BeforeOnly(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

    assert not getattr(BeforeOnly.before, "__isabstractmethod__", False)
    assert getattr(BeforeOnly.after, "__isabstractmethod__", False)


async def test_base_middleware_after_only() -> None:
    class AfterOnly(BaseMiddleware):
        def after(self, response: Response) -> Response:
            return response

    assert getattr(AfterOnly.before, "__isabstractmethod__", False)
    assert not getattr(AfterOnly.after, "__isabstractmethod__", False)


async def test_base_middleware_both() -> None:
    class BothMiddleware(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    assert not getattr(BothMiddleware.before, "__isabstractmethod__", False)
    assert not getattr(BothMiddleware.after, "__isabstractmethod__", False)


async def test_base_middleware_default_endpoints() -> None:
    class TestMW(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

    assert TestMW.endpoints == frozenset()


async def test_base_middleware_custom_endpoints() -> None:
    class TestMW(BaseMiddleware):
        endpoints = frozenset(["/health", "/docs"])

        def before(self, request: Request) -> Request:
            return request

    assert len(TestMW.endpoints) == 2
    assert "/health" in TestMW.endpoints


##### MIDDLEWARE HANDLER #####


async def test_middleware_handler_register() -> None:
    app = MagicMock()
    app.get_all_routes.return_value = [("GET", "/health")]
    app.before_request = MagicMock(side_effect=lambda ep: lambda fn: fn)
    app.after_request = MagicMock(side_effect=lambda ep: lambda fn: fn)

    class TestMW(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    handler = MiddlewareHandler(app)
    result = handler.register(TestMW)
    assert result is handler
    assert len(handler._middlewares) == 1


async def test_middleware_handler_chaining() -> None:
    app = MagicMock()
    app.get_all_routes.return_value = [("GET", "/a"), ("POST", "/b")]
    app.before_request = MagicMock(side_effect=lambda ep: lambda fn: fn)
    app.after_request = MagicMock(side_effect=lambda ep: lambda fn: fn)

    class MW1(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    class MW2(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    handler = MiddlewareHandler(app)
    handler.register(MW1).register(MW2)
    assert len(handler._middlewares) == 2


async def test_middleware_handler_specific_endpoints() -> None:
    app = MagicMock()
    app.before_request = MagicMock(side_effect=lambda ep: lambda fn: fn)
    app.after_request = MagicMock(side_effect=lambda ep: lambda fn: fn)

    class SpecificMW(BaseMiddleware):
        endpoints = frozenset(["/docs"])

        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    handler = MiddlewareHandler(app)
    handler.register(SpecificMW)
    app.before_request.assert_called_once_with("/docs")


async def test_middleware_handler_both_hooks_registered() -> None:
    app = MagicMock()
    app.get_all_routes.return_value = [("GET", "/test")]
    app.before_request = MagicMock(side_effect=lambda ep: lambda fn: fn)
    app.after_request = MagicMock(side_effect=lambda ep: lambda fn: fn)

    class BothMW(BaseMiddleware):
        def before(self, request: Request) -> Request:
            return request

        def after(self, response: Response) -> Response:
            return response

    handler = MiddlewareHandler(app)
    handler.register(BothMW)
    app.before_request.assert_called()
    app.after_request.assert_called()

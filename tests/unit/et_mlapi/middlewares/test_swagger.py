"""Tests for middlewares/swagger.py."""

from unittest.mock import MagicMock

from robyn import Response

from et_mlapi.middlewares.swagger import (
    _BRANDING_CSS,
    _FAVICON_SVG,
    _FAVICON_URI,
    _ROBYN_FAVICON,
    SwaggerBrandingMiddleware,
)

##### CONSTANTS #####


async def test_favicon_svg_is_valid() -> None:
    assert _FAVICON_SVG.startswith("<svg")
    assert _FAVICON_SVG.endswith("</g></svg>")


async def test_favicon_uri_is_data_uri() -> None:
    assert _FAVICON_URI.startswith("data:image/svg+xml;base64,")


async def test_branding_css_contains_styles() -> None:
    assert "et-mlapi" in _BRANDING_CSS
    assert ".swagger-ui" in _BRANDING_CSS


##### SWAGGER BRANDING MIDDLEWARE #####


async def test_swagger_endpoints() -> None:
    assert SwaggerBrandingMiddleware.endpoints == frozenset(["/docs"])


async def test_swagger_before_passthrough() -> None:
    app = MagicMock()
    mw = SwaggerBrandingMiddleware(app)
    request = MagicMock()
    result = mw.before(request)
    assert result is request


async def test_swagger_after_patches_html() -> None:
    app = MagicMock()
    mw = SwaggerBrandingMiddleware(app)

    html = f"""<html>
    <head><link rel="icon" href="{_ROBYN_FAVICON}" type="image/png"><title>Robyn OpenAPI Docs</title></head>
    <body>Swagger</body>
    </html>"""

    response = Response(status_code=200, headers={}, description=html)
    result = mw.after(response)
    desc = str(result.description)

    assert _ROBYN_FAVICON not in desc
    assert _FAVICON_URI in desc
    assert "et-mlapi" in desc
    assert _BRANDING_CSS in desc
    assert 'type="image/svg+xml"' in desc


async def test_swagger_after_no_match() -> None:
    app = MagicMock()
    mw = SwaggerBrandingMiddleware(app)
    response = Response(status_code=200, headers={}, description="<html><body>nothing</body></html>")
    result = mw.after(response)
    assert "nothing" in str(result.description)

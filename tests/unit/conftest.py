"""Unit test conftest — shared fixtures for all unit tests."""

from collections.abc import Generator
from dataclasses import dataclass, field

import orjson
import pytest

from et_mlapi.core.lifespan import State


@dataclass
class MockHeaders:
    """Mock Headers object for Robyn Request."""

    _data: dict = field(default_factory=dict)

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._data.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._data[key] = value


@dataclass
class MockRequest:
    """Mock Request object for Robyn."""

    _body: dict | str = field(default_factory=dict)
    headers: MockHeaders = field(default_factory=MockHeaders)
    method: str = "GET"
    path: str = "/"
    files: dict | None = None

    def json(self) -> dict:
        if isinstance(self._body, str):
            return orjson.loads(self._body)
        return self._body


@dataclass
class MockPathParams:
    """Mock PathParams object for Robyn."""

    _data: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)


##### FIXTURES #####


@pytest.fixture(scope="session")
def test_state() -> State:
    return State()


@pytest.fixture
def fresh_state() -> State:
    return State()


@pytest.fixture
def global_dependencies(test_state: State) -> Generator[dict, None, None]:
    yield {"state": test_state}
    test_state.clear()


@pytest.fixture
def make_mock_request():
    def _make(
        body: dict | str | None = None, method: str = "GET", path: str = "/", files: dict | None = None
    ) -> MockRequest:
        return MockRequest(_body=body or {}, method=method, path=path, files=files)

    return _make

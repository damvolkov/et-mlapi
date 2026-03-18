"""Integration test conftest — server lifecycle fixture."""

import multiprocessing
import socket
import time
from contextlib import suppress

import httpx
import pytest

_HOST = "127.0.0.1"
_STARTUP_TIMEOUT = 30


def _find_free_port() -> int:
    """Bind to port 0, let the OS assign a free port, return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    """Start et-mlapi on the given port. Runs in a subprocess."""
    from et_mlapi.core.settings import settings as st

    st.system.port = port
    st.system.host = _HOST

    from et_mlapi.main import main

    main()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


##### SERVER LIFECYCLE #####


@pytest.fixture(scope="session")
def mlapi_server():
    port = _find_free_port()
    process = multiprocessing.Process(target=_run_server, args=(port,), daemon=True)
    process.start()

    base_url = f"http://{_HOST}:{port}"

    for _ in range(_STARTUP_TIMEOUT):
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                break
        except (httpx.ConnectError, httpx.ReadTimeout):
            time.sleep(1)
    else:
        process.terminate()
        raise RuntimeError(f"et-mlapi failed to start on :{port} within {_STARTUP_TIMEOUT}s")

    yield {"base_url": base_url, "host": _HOST, "port": port}

    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()


##### DERIVED FIXTURES #####


@pytest.fixture(scope="session")
def base_url(mlapi_server: dict) -> str:
    return mlapi_server["base_url"]


@pytest.fixture(scope="session")
async def http_client(base_url: str):
    client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
    yield client
    with suppress(RuntimeError):
        await client.aclose()

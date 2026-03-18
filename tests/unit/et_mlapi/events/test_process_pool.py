"""Tests for events/process_pool.py."""

from concurrent.futures import ProcessPoolExecutor

from et_mlapi.core.lifespan import State
from et_mlapi.events.process_pool import ProcessPoolEvent, create_process_pool, process_pool_context

##### CREATE PROCESS POOL #####


async def test_create_process_pool_default() -> None:
    pool = create_process_pool()
    assert isinstance(pool, ProcessPoolExecutor)
    pool.shutdown(wait=False)


async def test_create_process_pool_custom_workers() -> None:
    pool = create_process_pool(max_workers=2)
    assert isinstance(pool, ProcessPoolExecutor)
    pool.shutdown(wait=False)


##### PROCESS POOL CONTEXT #####


async def test_process_pool_context_yields_executor() -> None:
    with process_pool_context(max_workers=1) as pool:
        assert isinstance(pool, ProcessPoolExecutor)


##### PROCESS POOL EVENT #####


async def test_process_pool_event_name() -> None:
    assert ProcessPoolEvent.name == "process_pool"


async def test_process_pool_event_startup() -> None:
    event = ProcessPoolEvent()
    event.state = State()
    pool = await event.startup()
    assert isinstance(pool, ProcessPoolExecutor)
    pool.shutdown(wait=False)


async def test_process_pool_event_shutdown() -> None:
    event = ProcessPoolEvent()
    event.state = State()
    pool = await event.startup()
    await event.shutdown(pool)


async def test_process_pool_event_has_shutdown() -> None:
    assert ProcessPoolEvent.has_shutdown() is True

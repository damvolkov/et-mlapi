"""Tests for core/lifespan.py."""

from unittest.mock import MagicMock

import pytest

from et_mlapi.core.lifespan import BaseEvent, Lifespan, State, create_lifespan

##### STATE #####


async def test_state_set_and_get() -> None:
    state = State()
    state.foo = "bar"
    assert state.foo == "bar"


async def test_state_contains() -> None:
    state = State()
    state.x = 1
    assert "x" in state
    assert "y" not in state


async def test_state_delete() -> None:
    state = State()
    state.x = 1
    del state.x
    assert "x" not in state


async def test_state_delete_missing_raises() -> None:
    state = State()
    with pytest.raises(AttributeError, match="State has no attribute 'missing'"):
        del state.missing


async def test_state_get_missing_raises() -> None:
    state = State()
    with pytest.raises(AttributeError, match="State has no attribute 'missing'"):
        _ = state.missing


async def test_state_get_with_default() -> None:
    state = State()
    assert state.get("missing", "default") == "default"
    assert state.get("missing") is None


async def test_state_clear() -> None:
    state = State()
    state.a = 1
    state.b = 2
    state.clear()
    assert "a" not in state
    assert "b" not in state


async def test_state_iter() -> None:
    state = State()
    state.a = 1
    state.b = 2
    keys = list(state)
    assert "a" in keys
    assert "b" in keys


async def test_state_repr() -> None:
    state = State()
    state.x = 42
    assert "State(" in repr(state)
    assert "42" in repr(state)


##### BASE EVENT #####


async def test_base_event_has_shutdown_default() -> None:
    class NoShutdownEvent(BaseEvent[str]):
        name = "test"

        async def startup(self) -> str:
            return "started"

    assert NoShutdownEvent.has_shutdown() is False


async def test_base_event_has_shutdown_override() -> None:
    class WithShutdownEvent(BaseEvent[str]):
        name = "test"

        async def startup(self) -> str:
            return "started"

        async def shutdown(self, instance: str) -> None:
            pass

    assert WithShutdownEvent.has_shutdown() is True


async def test_base_event_startup() -> None:
    class TestEvent(BaseEvent[int]):
        name = "counter"

        async def startup(self) -> int:
            return 42

    event = TestEvent()
    event.state = State()
    result = await event.startup()
    assert result == 42


##### LIFESPAN #####


async def test_create_lifespan() -> None:
    mock_app = MagicMock()
    lifespan = create_lifespan(mock_app)
    assert isinstance(lifespan, Lifespan)
    assert lifespan.state is None
    assert lifespan.events == []


async def test_lifespan_register_chaining() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)

    class EventA(BaseEvent[str]):
        name = "a"

        async def startup(self) -> str:
            return "a"

    class EventB(BaseEvent[str]):
        name = "b"

        async def startup(self) -> str:
            return "b"

    result = lifespan.register(EventA).register(EventB)
    assert result is lifespan


async def test_lifespan_startup_creates_state() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)

    class SimpleEvent(BaseEvent[str]):
        name = "simple"

        async def startup(self) -> str:
            return "value"

    lifespan.register(SimpleEvent)
    await lifespan.startup()

    assert lifespan.state is not None
    assert "simple" in lifespan.state
    assert lifespan.state.simple == "value"
    assert len(lifespan.events) == 1
    mock_app.inject_global.assert_called_once()


async def test_lifespan_shutdown_reverse_order() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)
    shutdown_order: list[str] = []

    class EventA(BaseEvent[str]):
        name = "a"

        async def startup(self) -> str:
            return "a"

        async def shutdown(self, instance: str) -> None:
            shutdown_order.append("a")

    class EventB(BaseEvent[str]):
        name = "b"

        async def startup(self) -> str:
            return "b"

        async def shutdown(self, instance: str) -> None:
            shutdown_order.append("b")

    lifespan.register(EventA).register(EventB)
    await lifespan.startup()
    await lifespan.shutdown()

    assert shutdown_order == ["b", "a"]


async def test_lifespan_shutdown_no_state() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)
    await lifespan.shutdown()


async def test_lifespan_shutdown_clears_state() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)

    class SimpleEvent(BaseEvent[str]):
        name = "simple"

        async def startup(self) -> str:
            return "value"

    lifespan.register(SimpleEvent)
    await lifespan.startup()
    await lifespan.shutdown()

    assert lifespan.state is not None
    assert "simple" not in lifespan.state


async def test_lifespan_skip_shutdown_if_not_overridden() -> None:
    mock_app = MagicMock()
    lifespan = Lifespan(mock_app)

    class NoShutdownEvent(BaseEvent[str]):
        name = "no_shutdown"

        async def startup(self) -> str:
            return "val"

    lifespan.register(NoShutdownEvent)
    await lifespan.startup()
    await lifespan.shutdown()

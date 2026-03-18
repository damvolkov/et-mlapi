---
name: python
description: Python >=3.13 mastery. Typing (strict, generics PEP 695, Annotated, Protocol), dispatch (ovld/plum/dict), descriptors, magic methods, slots, functools/itertools/operator mastery, async patterns, stdlib (collections, asyncio, contextlib). Use for language-level questions and advanced patterns.
---

# Python >=3.13 Mastery

## Typing — Strict, Always

Everything typed. No `Any` unless interfacing with untyped third-party.

### Modern Syntax (3.13+)

```python
# Union: str | None, never Optional
result: str | None = None

# Builtins: list[int], dict[str, Any], tuple[str, ...]
items: list[str] = []
mapping: dict[str, int] = {}

# Self for return types
class Node:
    def clone(self) -> Self: ...
```

### PEP 695 Generics

New syntax, always. Old `Generic[T]` never.

```python
# Type aliases
type FieldType = Literal["tag", "text"]
type RoundedScore = Annotated[float, AfterValidator(lambda v: round(v, 2))]

# Generic classes
class Store[D: Node]:
    def __init__(self, redis: AsyncRedis): ...

# Generic functions
def map_nodes[T: Node, U](nodes: list[T], fn: Callable[[T], U]) -> list[U]:
    return [fn(node) for node in nodes]

# Subclass propagation
class KnowledgeStore[D: Node](BaseStore[D]):
    pass
```

### TypeVars & ParamSpec

```python
from typing import TypeVar, ParamSpec

# Single letter or T-prefixed, always bound
D = TypeVar("D", bound=Node)
T = TypeVar("T")
S = TypeVar("S", str, int, float)

# For decorators that preserve signature
P = ParamSpec("P")

def timing[**P](fn: Callable[P, T]) -> Callable[P, T]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.monotonic()
        result = fn(*args, **kwargs)
        print(f"Took {time.monotonic() - start:.4f}s")
        return result
    return wrapper
```

### Annotated Types

Combine validation + serialization + semantic markers in one declaration.

```python
type TagField = Annotated[str, "tag"]  # semantic marker for schema gen
type TextField = Annotated[str, "text"]
type RedisList = Annotated[
    list[str],
    BeforeValidator(ensure_list),
    PlainSerializer(ensure_str),
]

type RedisUrlStr = Annotated[str, AfterValidator(lambda v: str(RedisDsn(v)))]
```

### ClassVar

Constants that must NOT be loaded from env (pydantic-settings):

```python
from typing import ClassVar
import re

class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    API_VERSION: ClassVar[str] = "1.0.0"
    REGEX: ClassVar[re.Pattern[str]] = re.compile(r"^\w+$")
```

### Protocol

Structural subtyping without inheritance. Preferred over ABC when possible.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Adapter(Protocol):
    async def health(self) -> bool: ...
    async def fetch(self, url: str) -> dict: ...

class NLPAdapter:
    async def health(self) -> bool: return True
    async def fetch(self, url: str) -> dict: return {}

# Duck typing validated at runtime
def use_adapter(adapter: Adapter) -> None:
    if isinstance(adapter, Adapter):
        await adapter.health()
```

### @overload

Different return types based on input types.

```python
from typing import overload

@overload
def build_query(query_type: Literal["vector"], text: str, vector: list[float]) -> VectorQuery: ...
@overload
def build_query(query_type: Literal["hybrid"], text: str, vector: list[float]) -> HybridQuery: ...

def build_query(query_type: str, text: str, vector: list[float]):
    match query_type:
        case "vector": return VectorQuery(text, vector)
        case "hybrid": return HybridQuery(text, vector)
```

### Type Reflection

Runtime introspection for codegen and schema generation.

```python
from typing import get_origin, get_args, Annotated, UnionType

def resolve_schema(annotation: type) -> dict:
    match get_origin(annotation):
        case x if x is Annotated:
            args = get_args(annotation)
            base_type = args[0]
            metadata = args[1:]
            return {"type": base_type.__name__, "markers": [str(m) for m in metadata]}
        case x if x is UnionType or x is Union:
            args = get_args(annotation)
            return {"union": [resolve_schema(arg) for arg in args]}
        case x if x is list:
            args = get_args(annotation)
            inner = resolve_schema(args[0]) if args else {"type": "Any"}
            return {"type": "array", "items": inner}
        case _:
            return {"type": annotation.__name__}
```

## Control Flow — Dispatch Patterns

Hard rule: No nested if-else. >=3 branches → dispatch.

### 1. match-case — Value/Shape Dispatch

Default. Each case body 1-3 lines.

```python
match query_type:
    case "vector": return VectorQuery(...)
    case "hybrid": return HybridQuery(...)
    case "keyword": return KeywordQuery(...)
    case _: raise ValueError("Unknown query type")
```

### 2. Dict Dispatcher — Complex Multi-Entity

When branches have significant logic. Declare at module/class top level.

```python
##### DISPATCHERS #####

_PIPELINE_HANDLERS: dict[str, Callable[[PipelineContext], Coroutine]] = {
    "ingest": handle_ingest,
    "search": handle_search,
    "delete": handle_delete,
}

async def dispatch_pipeline(action: str, ctx: PipelineContext) -> Result:
    handler = _PIPELINE_HANDLERS.get(action)
    if handler is None:
        raise ValueError(f"Unknown action: {action}")
    return await handler(ctx)
```

### 3. plum-dispatch — Typed Multiple Dispatch

When dispatch dimension is the **type** of input arguments.

```python
from plum import dispatch

@dispatch
async def process(data: TextChunk) -> ProcessedChunk:
    return await _process_text(data)

@dispatch
async def process(data: ImageChunk) -> ProcessedChunk:
    return await _process_image(data)

@dispatch
async def process(data: AudioChunk) -> ProcessedChunk:
    return await _process_audio(data)
```

### Guard Clauses & Walrus

```python
if (result := await redis.get(key)) is not None:
    return process(result)

if (error := validate(data)) is None:
    return save(data)

while (chunk := f.read(1024)):
    process(chunk)
```

## Conventions

- **Enums**: `StrEnum(auto())` for string options. Default choice.
- **JSON**: `import orjson as json` — never stdlib `json`.
- **Comprehensions**: map/filter over raw loops.
- **Config**: never `os.environ`, `os.getenv`, `python-dotenv`. Always `pydantic-settings`.
- **Docstrings**: one-liner. Big O when non-obvious. No inline comments.

## Performance & Memory

Analyze Big O. Prioritize O(1) / O(log n).

### __slots__

Everywhere. Each subclass declares only its OWN slots.

```python
@dataclass(slots=True, frozen=True)
class Node:
    id: str
    name: str

@dataclass(slots=True, frozen=True)
class IndexNode(Node):
    __slots__ = ("vector",)  # only this subclass's new attr
    vector: list[float]
```

### Iterables & Generators

Generators (`yield`) and async generators (`async yield`) by default. Never materialize to `list` unless strictly needed.

```python
def stream_nodes(store: Store) -> Generator[Node]:
    for batch in store.batches():
        for node in batch:
            yield node

async def stream_embeddings(nodes: Iterable[Node]) -> AsyncGenerator[list[float]]:
    for node in nodes:
        yield await embed(node.text)
```

### Deduplication & Membership

`set` / `frozenset` over `list`. Combine with generators for memory efficiency.

```python
# Generator → frozenset: memory-efficient dedupe
unique_ids = frozenset(node.id for node in store.search(query))

# Generator → set for mutable tracking
seen = set()
for node in stream_nodes(store):
    if node.id not in seen:
        seen.add(node.id)
        process(node)
```

### Pre-Compile Regex

```python
import re

_EMAIL_PATTERN: re.Pattern[str] = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
_SNAKE_CASE: re.Pattern[str] = re.compile(r"^[a-z_]+$")

def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_PATTERN.match(email))
```

## Caching

```python
from functools import cache, lru_cache, cached_property

# Pure function, hashable args, unbounded
@cache
def fibonacci(n: int) -> int:
    return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)

# Bounded LRU
@lru_cache(maxsize=128)
def get_user(user_id: str) -> User:
    return db.query(User).filter_by(id=user_id).first()

# Instance-level, computed once
class Session:
    @cached_property
    def user_id(self) -> str:
        return self._claims["sub"]
```

## Stdlib Mastery

Advanced usage expected. Never reinvent.

### functools

```python
from functools import cache, lru_cache, partial, reduce, singledispatch, wraps, cached_property

# Decorator that preserves signature
def timing(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__}: {time.monotonic() - start:.4f}s")
        return result
    return wrapper

# Partial application
add_five = partial(lambda x, y: x + y, 5)
assert add_five(10) == 15

# Reduce list to single value
product = reduce(lambda x, y: x * y, [1, 2, 3, 4], 1)
```

### itertools

```python
from itertools import chain, islice, groupby, starmap, compress, takewhile, pairwise, batched

# Chain multiple iterables
all_items = chain.from_iterable([list1, list2, list3])

# Group by key
for key, group in groupby(sorted_items, key=lambda x: x.category):
    items = list(group)

# Pairwise iteration
for a, b in pairwise(items):
    compare(a, b)

# Batch items
for batch in batched(items, 10):
    process_batch(batch)

# Conditional filtering
non_zero = compress(items, [x != 0 for x in items])

# Iterate while condition
prefix = takewhile(lambda x: x < 10, sorted_items)
```

### operator

```python
from operator import itemgetter, attrgetter, methodcaller

# Multi-key dict sorting
by_category_then_name = sorted(items, key=itemgetter("category", "name"))

# Nested attribute access
get_user_email = attrgetter("profile.contact.email")
emails = [get_user_email(user) for user in users]

# Method calling
upper_names = list(map(methodcaller("upper"), names))
```

### contextlib

```python
from contextlib import suppress, asynccontextmanager, AsyncExitStack

# Ignore exception
with suppress(FileNotFoundError):
    path.unlink()

# Async context manager
@asynccontextmanager
async def redis_connection():
    conn = await connect_redis()
    try:
        yield conn
    finally:
        await conn.close()

# Async stack cleanup
async with AsyncExitStack() as stack:
    redis = await stack.enter_async_context(redis_connection())
    http = await stack.enter_async_context(httpx.AsyncClient())
```

### collections

```python
from collections import deque, Counter, defaultdict, ChainMap

# Fixed-length ringbuffer
window = deque(maxlen=10)

# Frequency counter
word_counts = Counter(words)
most_common = word_counts.most_common(5)

# Default values
groups = defaultdict(list)
groups[key].append(item)

# Merged dicts (read-only)
merged = ChainMap(dict1, dict2, dict3)
```

### asyncio

```python
from asyncio import gather, Semaphore, TaskGroup, timeout, Queue

# Parallel I/O
results = await gather(task1(), task2(), task3())

# Bounded concurrency
sem = Semaphore(10)
async def bounded_task(item):
    async with sem:
        return await process(item)

# Structured concurrency (3.11+)
async with TaskGroup() as tg:
    task1 = tg.create_task(coro1())
    task2 = tg.create_task(coro2())

# Timeout
try:
    result = await timeout(5)(slow_operation())
except TimeoutError:
    pass

# Producer/consumer
queue = Queue()
async with queue:
    await queue.put(item)
    item = await queue.get()
```

## Magic Methods & Protocols

### repr, eq, hash, bool, lt

```python
@dataclass(slots=True, frozen=True)
class Node:
    id: str
    score: float

    def __repr__(self) -> str:
        return f"Node(id={self.id!r}, score={self.score})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id and self.score == other.score

    def __hash__(self) -> int:
        return hash((self.id, self.score))

    def __bool__(self) -> bool:
        return self.score > 0

    def __lt__(self, other: "Node") -> bool:
        return self.score < other.score
```

### __init_subclass__

Auto-registration on subclass definition.

```python
class Adapter(ABC):
    _registry: ClassVar[dict[str, type["Adapter"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.__name__] = cls

class NLPAdapter(Adapter):
    pass

class ImageAdapter(Adapter):
    pass

# Auto-registered
assert Adapter._registry["NLPAdapter"] is NLPAdapter
```

### __set_name__

Descriptors learn their attribute name.

```python
class ValidatedString:
    def __init__(self, min_length: int = 0):
        self.min_length = min_length
        self.name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: object, objtype: type | None = None) -> str:
        if obj is None:
            return self
        return object.__getattribute__(obj, f"_{self.name}")

    def __set__(self, obj: object, value: str) -> None:
        if len(value) < self.min_length:
            raise ValueError(f"{self.name} too short")
        object.__setattr__(obj, f"_{self.name}", value)

class User:
    name = ValidatedString(min_length=1)
```

### __class_getitem__

Parametrized types at runtime.

```python
class Indexed[T]:
    def __init__(self, items: list[T]):
        self.items = items

    def search(self, fn: Callable[[T], bool]) -> T | None:
        for item in self.items:
            if fn(item):
                return item

# Usage
numbers: Indexed[int] = Indexed([1, 2, 3])
result = numbers.search(lambda x: x > 2)
```

## Async Patterns

### TaskGroup — Structured Concurrency (3.11+)

```python
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(fetch_user(1))
    task2 = tg.create_task(fetch_user(2))
    # All tasks must complete before exit

# Automatic error propagation
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task_a())
        tg.create_task(task_b())  # if this fails, TaskGroup exits
except ExceptionGroup as eg:
    for exc in eg.exceptions:
        handle(exc)
```

### Semaphore — Bounded Concurrency

```python
sem = asyncio.Semaphore(10)

async def bounded_request(url: str):
    async with sem:
        return await http.get(url)

results = await asyncio.gather(
    *[bounded_request(url) for url in urls]
)
```

### timeout — Async Timeouts (3.11+)

```python
try:
    result = await asyncio.timeout(5)(slow_operation())
except TimeoutError:
    print("Operation timed out")
```

### Queue — Producer/Consumer

```python
queue = asyncio.Queue(maxsize=10)

async def producer():
    for item in items:
        await queue.put(item)

async def consumer():
    while True:
        item = await queue.get()
        process(item)
        queue.task_done()

async with asyncio.TaskGroup() as tg:
    tg.create_task(producer())
    tg.create_task(consumer())
```

### Async Generators

```python
async def stream_embeddings(texts: list[str]) -> AsyncGenerator[list[float]]:
    for text in texts:
        embedding = await embed(text)
        yield embedding

# Streaming consumption
async for embedding in stream_embeddings(texts):
    process(embedding)
```

## Prohibited Patterns (STRICTLY FORBIDDEN)

### No __init__.py (ever)

Python >=3.3 namespace packages. No exceptions.

### No imports inside functions

All top-level. Use `TYPE_CHECKING` for circular deps.

```python
# FORBIDDEN
def load_config(path: Path) -> Config:
    from app.models import Config
    return Config.from_yaml(path)

# CORRECT
from app.models import Config

def load_config(path: Path) -> Config:
    return Config.from_yaml(path)

# CORRECT — circular deps only
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Config
```

### No relative imports

Always absolute.

```python
# FORBIDDEN
from .module import X

# CORRECT
from app.module import X
```

### No `os.environ` / `os.getenv`

Always `pydantic-settings`.

```python
# FORBIDDEN
db_url = os.environ.get("DATABASE_URL")

# CORRECT
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

settings = Settings()
```

## Error Handling

### Exception Hierarchy

```python
class AppError(Exception):
    """Base for all project exceptions."""

class ValidationError(AppError):
    pass

class NotFoundError(AppError):
    pass

class ExternalServiceError(AppError):
    pass
```

### Result Pattern with match-case

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

# Usage
match await fetch_user(user_id):
    case Ok(user):
        return user
    case Err(NotFoundError()):
        return None
    case Err(e):
        logger.error("fetch_failed", error=str(e))
        raise
```

### contextlib.suppress

```python
from contextlib import suppress

# Never try/except pass
with suppress(FileNotFoundError):
    path.unlink()
```

## Logging

Emoji + UPPERCASE_EVENT, context in extra={}.

```python
import structlog

logger = structlog.get_logger()

logger.info("📦 INDEX_CREATED", extra={"index": name})
logger.info("✅ OPERATION_COMPLETE", extra={"items": count})
logger.warning("⚠️ TTL_EXPIRED", extra={"key": key})
logger.error("❌ STORE_ERROR", extra={"error": str(e), "operation": "search"})
```

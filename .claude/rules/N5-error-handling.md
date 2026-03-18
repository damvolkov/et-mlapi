---
description: Error handling patterns. Structured exceptions, result types, suppression, logging.
alwaysApply: false
---

# Error Handling

## Suppression

- `contextlib.suppress(SpecificError)` — NEVER `try...except...pass`.
- Only suppress when you genuinely don't care about the outcome.

## Exception Hierarchy

- Every project defines `AppError(Exception)` as base.
- All custom exceptions inherit from `AppError`.
- Never bare `except:`. Always catch specific types.
- Never `except Exception:` unless re-raising or logging + raising.

```python
class AppError(Exception):
    """Base for all project exceptions."""

class NotFoundError(AppError): ...
class ValidationError(AppError): ...
class ExternalServiceError(AppError): ...
```

## Result Pattern

For expected failure paths, use typed result with `match-case`:

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
        process(user)
    case Err(NotFoundError()):
        log.warning("user_not_found", user_id=user_id)
    case Err(e):
        log.error("fetch_failed", error=str(e))
        raise
```

## Logging

- `structlog` mandatory for all error logging.
- Always structured: `log.error("event_name", key=value, exc_info=True)`.
- Never `print()` or `logging.error(f"...")` with f-strings.
- Bind context early: `log = structlog.get_logger().bind(service="api")`.

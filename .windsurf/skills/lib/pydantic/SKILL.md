---
name: pydantic
description: Pydantic v2 advanced patterns. Validators, serializers, computed fields, private attrs, typing, model config, introspection-based schema generation. Use when creating or modifying Pydantic models, schemas, or validation.
---

# Pydantic v2 Patterns

## Model Validators

mode="wrap" — flat → nested field distribution:

```python
@model_validator(mode="wrap")
@classmethod
def distribute_fields(cls, values: dict, handler: Callable) -> Self:
    metadata = {}
    known_fields = cls.model_fields
    for key, val in list(values.items()):
        if key not in known_fields:
            metadata[key] = values.pop(key)
    values["metadata"] = metadata
    return handler(values)
```

mode="before" — data normalization:

```python
@model_validator(mode="before")
@classmethod
def normalize_input(cls, values: dict) -> dict:
    if "old_field" in values:
        values["new_field"] = values.pop("old_field")
    return values
```

mode="after" — derived field assignment:

```python
@model_validator(mode="after")
def build_composite_id(self) -> Self:
    object.__setattr__(self, "id", f"{self.tenant}:{self.name}")
    return self
```

@classmethod required for mode="before" and mode="wrap". Return Self from mode="after".

## Field Validators & Serializers

```python
@field_validator("category", mode="before")
@classmethod
def coerce_category(cls, v: str | Category) -> Category:
    return Category(v) if isinstance(v, str) else v
```

Context-aware serialization:

```python
@model_serializer(mode="wrap")
def serialize(self, handler: Callable) -> dict:
    data = handler(self)
    if self._context == "node":
        data.pop("score", None)
    return data
```

Bidirectional transform via Annotated:

```python
type RedisList = Annotated[
    list[str],
    BeforeValidator(ensure_list),
    PlainSerializer(ensure_str),
]

type RoundedScore = Annotated[float, AfterValidator(lambda v: round(v, 2))]
type RedisUrlStr = Annotated[str, AfterValidator(lambda v: str(RedisDsn(v)))]
```

## Computed Fields & Private Attrs

```python
@computed_field
@property
def embed_text(self) -> str:
    return f"{self.name} {self.description}"

class Entity(BaseModel):
    _scores: dict[str, float] = PrivateAttr(default_factory=dict)
    _context: str = PrivateAttr(default="api")
    vector: SkipJsonSchema[list[float]] = Field(default_factory=list)
```

## Typing in Models

```python
# backward-compatible aliases
name: str = Field(validation_alias=AliasChoices("field_name", "camelCase", "fieldName"))

# semantic markers for Redis index generation
name: Annotated[str, "tag"]           # → TagField
description: Annotated[str, "text"]   # → TextField
```

## Model Config

```python
model_config = ConfigDict(extra="ignore", populate_by_name=True)
model_config = ConfigDict(arbitrary_types_allowed=True)
```

## Introspection-Based Schema Generation

Resolve annotations to Redis index field types:

```python
from typing import get_origin, get_args, Annotated

def resolve_field_type(annotation: type) -> str:
    match get_origin(annotation):
        case x if x is Annotated:
            args = get_args(annotation)
            metadata = args[1] if len(args) > 1 else None
            match metadata:
                case "tag": return "TagField"
                case "text": return "TextField"
                case _: return resolve_field_type(args[0])
        case x if x is list:
            return "TagField"
        case _:
            match annotation:
                case t if t is str: return "TextField"
                case t if t is float: return "NumericField"
                case _: return "TextField"
```

Use object.__setattr__() for frozen/slots models. Compose Annotated types for semantic markers + validation + serialization in one declaration. Leverage validator pipeline: before → wrap → after.

## Settings (pydantic-settings)

Any system with config → `Settings(BaseSettings)`. Never `os.environ`, `os.getenv`, `python-dotenv`.
Loads `.env` automatically. `ClassVar` for constants. File paths → typed `Path`. Load content on the fly.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import ClassVar, Literal
from pathlib import Path

class Settings(BaseSettings):
    """Unified settings for service."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DEBUG: bool = True
    ENVIRONMENT: Literal["DEV", "PROD"] = "DEV"

    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    PROJECT: ClassVar[dict] = read_pyproject(BASE_DIR / "pyproject.toml")
    API_VERSION: ClassVar[str] = PROJECT.get("project", {}).get("version", "0.1.0")
    DATA_PATH: ClassVar[Path] = BASE_DIR / "data"

    PROMPT_PATH: Path = BASE_DIR / "data" / "prompts" / "system.md"
    CERTS_PATH: Path = BASE_DIR / "certs" / "ca.pem"

    @computed_field
    @property
    def system_prompt(self) -> str:
        return self.PROMPT_PATH.read_text()

    REDIS_ADDRESS: str = "localhost:6379"
```

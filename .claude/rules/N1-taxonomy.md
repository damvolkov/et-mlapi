---
description: Semantic domain taxonomy — entity/action/vocabulary inventory. Runs IN PARALLEL with code creation. Prerequisite to N3-naming-conventions.
alwaysApply: true
---

# Semantic Domain Taxonomy

**Pipeline node: N1** — This is NOT a one-time pre-step. It runs **in parallel** with entity creation, module design, and implementation. Every time you create an entity, method, or ecosystem element, the taxonomy must hold. If it doesn't, stop and reconcile.

## Why

Names that look intuitive in isolation become chaos in aggregate. `TaskSpec` next to `AgentConfig` next to `StateUpdate` — three classes, three different suffix conventions for the same conceptual field. `get_state()` next to `deliver_to_user()` next to `enrich_thread()` — three methods, three different verb families for similar operations. The taxonomy prevents this by establishing vocabulary BEFORE and DURING creation.

## Process

### Step 1: Entity Inventory

List ALL high-level entities in the bounded context. An entity is anything with identity, state, or behavior.

```
Example — Agent orchestration system:
  Entities: Agent, Task, State, Thread, User, Session
```

**Rule:** If you can't list entities, you don't understand the domain. Stop and analyze.

### Step 2: Action Inventory

List ALL operations that occur between entities. Don't name them yet — just describe them.

```
Example — raw action list:
  retrieve state, send message to user, add context to thread,
  transfer control to another agent, combine thread histories,
  render state change as text, modify state, delete thread item
```

### Step 3: Semantic Field Deduplication

Group synonyms into fields. Pick ONE canonical term per field. This is the CRITICAL step.

**Verb fields (for methods):**

```
FIELD: "retrieve"
  Synonyms: get, fetch, retrieve, obtain, pull, read, load, lookup
  ✅ Canonical: get
  → get_state, get_thread, get_user

FIELD: "modify"
  Synonyms: update, modify, change, mutate, set, patch, alter, edit
  ✅ Canonical: update
  → update_state, update_thread, update_user

FIELD: "transmit"
  Synonyms: send, deliver, emit, push, dispatch, notify, broadcast
  ✅ Canonical: send
  → send_message, send_update

FIELD: "insert"
  Synonyms: add, inject, enrich, append, insert, include, attach
  ✅ Canonical: add
  → add_context, add_thread_item

FIELD: "delete"
  Synonyms: remove, delete, drop, clear, purge, detach, strip
  ✅ Canonical: remove
  → remove_thread_item, remove_session

FIELD: "delegate"
  Synonyms: transfer, handoff, delegate, forward, route, dispatch
  ✅ Canonical: transfer
  → transfer_agent

FIELD: "unite"
  Synonyms: merge, combine, join, concatenate, unify, consolidate
  ✅ Canonical: merge
  → merge_thread

FIELD: "render"
  Synonyms: format, render, serialize, stringify, display, present
  ✅ Canonical: format
  → format_effect

FIELD: "produce"
  Synonyms: create, build, make, generate, construct, initialize
  ✅ Canonical: create
  → create_session, create_task
```

**Concept fields (for class suffixes):**

```
FIELD: "configuration"
  Synonyms: Config, Spec, Instructions, Definition, Blueprint, Schema, Template
  ✅ Canonical: Spec
  → TaskSpec, AgentSpec (NOT TaskConfig, AgentInstructions)

FIELD: "condition"
  Synonyms: State, Status, Condition, Mode, Phase
  ✅ Canonical: State
  → TaskState, AgentState (NOT TaskStatus, AgentCondition)

FIELD: "consequence"
  Synonyms: Effect, Result, Outcome, Impact, Update
  ✅ Canonical: Effect
  → StateEffect, TaskEffect (NOT UpdateEffect, StateResult)

FIELD: "rule"
  Synonyms: Policy, Strategy, Rule, Constraint, Guard
  ✅ Canonical: Policy
  → InterruptionPolicy, SchedulingPolicy (NOT InterruptionStrategy)

FIELD: "position"
  Synonyms: Slot, Position, Assignment, Allocation, Entry
  ✅ Canonical: Slot
  → AgentSlot

FIELD: "rank"
  Synonyms: Priority, Weight, Rank, Level, Importance
  ✅ Canonical: Priority
  → TaskPriority
```

### Step 4: Vocabulary Table

Produce the final vocabulary as a reference table. This is the **contract** for the bounded context.

```
┌──────────────┬──────────────────────────────────────────────┐
│ Category     │ Canonical Terms                              │
├──────────────┼──────────────────────────────────────────────┤
│ Entities     │ Agent, Task, State, Thread, User, Session    │
├──────────────┼──────────────────────────────────────────────┤
│ Verbs        │ get, update, send, add, remove, transfer,    │
│              │ merge, format, create                        │
├──────────────┼──────────────────────────────────────────────┤
│ Suffixes     │ Spec, State, Effect, Policy, Slot, Priority  │
└──────────────┴──────────────────────────────────────────────┘
```

### Step 5: Composition

Build names by composing vocabulary terms:

**Classes:** `{Entity}{Suffix}`
```python
class TaskState(StrEnum): ...
class TaskSpec: ...
class TaskPriority(StrEnum): ...
class TaskEffect: ...
class AgentSlot: ...
class AgentState: ...
class InterruptionPolicy: ...
class StateEffect: ...
```

**Methods:** `{verb}_{entity}[_{detail}]`
```python
async def get_state(self) -> ReactiveState: ...
async def send_message(self, text: str) -> None: ...
async def add_context(self, payload: dict) -> None: ...
async def transfer_agent(self, target: str) -> None: ...
async def merge_thread(self, source: Thread) -> None: ...
def format_effect(self, effect: StateEffect) -> str | None: ...
async def update_state(self, key: str, value: Any) -> None: ...
async def remove_thread_item(self, item_id: str) -> None: ...
```

## Rules

1. **One word per semantic field.** NEVER use two synonyms in the same bounded context. If you chose `get`, you CANNOT also use `fetch` or `load` for the same type of operation.
2. **Entity prefix on all related classes.** `Task` → `TaskState`, `TaskSpec`, `TaskPriority`, `TaskEffect`. NOT `TaskStatus`, `TaskConfig`, `TaskOutcome`.
3. **Verb consistency across entities.** If `get_state` exists, then `get_thread`, `get_user` — NOT `fetch_thread`, `load_user`.
4. **Vocabulary is immutable within a context.** Once established, no synonyms. New concept that doesn't fit → new semantic field with a new canonical term.
5. **Evaluate collectively, not individually.** A name that looks fine alone may break the pattern alongside its siblings. Always review the full set.
6. **Taxonomy is continuous.** Every new entity, method, or class must pass through the vocabulary table. If it doesn't fit, update the table FIRST, then name it.

## Anti-Patterns

```python
# ❌ WRONG — mixed synonyms, no entity prefixes, chaos
class Priority(StrEnum): ...        # priority of WHAT?
class TaskStatus(StrEnum): ...      # "Status" but elsewhere "State"
class InterruptionStrategy: ...     # "Strategy" but elsewhere "Policy"
class UpdateEffect: ...             # "Update" is a verb, not an entity prefix
class StateUpdate: ...              # is "Update" the entity or "State"?
class TaskSpec: ...                 # "Spec" but elsewhere "Config"
class AgentSlot: ...                # OK but lonely — no Agent* siblings

def get_state(): ...                # "get" ✓
def deliver_to_user(): ...          # "deliver" ≠ "send" — pick one
def enrich_thread(): ...            # "enrich" ≠ "add" — pick one
def perform_handoff(): ...          # "perform_handoff" ≠ "transfer" — pick one

# ✅ CORRECT — consistent vocabulary, entity-prefixed, predictable
class TaskState(StrEnum): ...       # Entity + Suffix
class TaskSpec: ...                 # Entity + Suffix (same family)
class TaskPriority(StrEnum): ...    # Entity + Suffix
class TaskEffect: ...               # Entity + Suffix
class AgentSlot: ...                # Entity + Suffix
class AgentState: ...               # Entity + Suffix (sibling of AgentSlot)
class InterruptionPolicy: ...       # Compound domain + Suffix
class StateEffect: ...              # Entity + Suffix

def get_state(): ...                # verb + entity
def send_message(): ...             # verb + entity
def add_context(): ...              # verb + entity
def transfer_agent(): ...           # verb + entity
def merge_thread(): ...             # verb + entity
def format_effect(): ...            # verb + entity
```

## When to Run This Exercise

- **New project**: always, before writing the first class.
- **New bounded context**: always (new module with 3+ entities).
- **During implementation**: continuously — every new name passes through the vocabulary.
- **Naming feels inconsistent**: stop, inventory, deduplicate, reconcile, then resume.
- **Code review reveals synonyms**: retroactively fix the vocabulary and rename.

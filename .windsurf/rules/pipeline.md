---
description: Code creation pipeline — maps each step to its rule/skill. Agent reads this to know the workflow and where to find each rule.
alwaysApply: true
---

# Code Creation Pipeline

Every code creation task follows this pipeline. Each node has associated rules and skills. Follow top-to-bottom. Skip nodes that don't apply to the current task.

```
┌─────────────────────────────────────────────────────────────────┐
│                         IDENTITY                                │
│  Who am I? What are my constraints?                             │
│  → principles.md                                                │
│  → AGENT.md (persona + hard constraints)                        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌──────────────────┐ ┌────────────────────────────────────────────┐
│  N1 — TAXONOMY   │ │  N2 — STRUCTURE                            │
│  Entity/action   │ │  Project layout, module boundaries,        │
│  inventory.      │ │  directory conventions.                    │
│  Vocabulary      │ │  → rules/N2-project-structure.md           │
│  contract.       │ │  → skills/architecture/                    │
│  CONTINUOUS —    │ └──────────────────┬─────────────────────────┘
│  runs in         │                    │
│  parallel with   │                    │
│  all creation.   │                    │
│  → rules/        │                    │
│  N1-taxonomy.md  │                    │
└────────┬─────────┘                    │
         │                              │
         └──────────┬───────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  N3 — NAMING                                                    │
│  Apply domain vocabulary to concrete names.                     │
│  Classes, functions, modules, constants, tests.                 │
│  Depends on: N1 (vocabulary), N2 (module boundaries).           │
│  → rules/N3-naming-conventions.md                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  N4 — IMPLEMENTATION                                            │
│  Language rules, typing, control flow, library choices.         │
│  → rules/N4-lang-python.md                                      │
│  → rules/N4-libraries.md                                        │
│  → skills/lib/* (python, pydantic, fastapi, robyn)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  N5 — QUALITY                                                   │
│  Error handling, validation, exception hierarchy.               │
│  → rules/N5-error-handling.md                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  N6 — TESTING                                                   │
│  Test strategy, coverage, fixtures, patterns.                   │
│  → rules/N6-testing.md                                          │
│  → skills/testing/* (fixtures, mocking)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  N7 — DEVOPS                                                    │
│  Build, deploy, CI/CD, containers, infrastructure.              │
│  → skills/devops/                                               │
│  → skills/starters/* (api-general, api-ml, cli, library)        │
└─────────────────────────────────────────────────────────────────┘
```

N1 is NOT sequential — it runs **in parallel** with entity creation and feeds N3 continuously.
Every new entity, method, or class passes through the N1 vocabulary table before being named.

## Node Dependencies

```
IDENTITY ──→ all nodes (always loaded, shapes every decision)
N1 ═══════→ N3, N4 (vocabulary feeds naming AND implementation — CONTINUOUS)
N2 ────────→ N3 (module boundaries inform module/class naming)
N1 + N3 ──→ N4 (named entities guide implementation patterns)
N4 ────────→ N5 (language patterns determine error handling)
N2 + N3 ──→ N6 (test structure mirrors source; test names mirror source names)
N4 + N5 ──→ N7 (implementation + quality feed build/deploy decisions)
```

## When to Invoke Each Node

| Node | Trigger |
|------|---------|
| N1 | New project, new bounded context, new feature with 3+ entities |
| N2 | New project, new package, major restructuring |
| N3 | Every file, every class, every function |
| N4 | Every line of code |
| N5 | Every error path, every external boundary |
| N6 | Every testable unit |
| N7 | Build, deploy, infrastructure changes |

## Quick Reference — Rule Files

| Node | File | Scope |
|------|------|-------|
| — | `principles.md` | Agent identity, philosophy, hard constraints |
| N1 | `N1-taxonomy.md` | Entity/action inventory, vocabulary tables |
| N2 | `N2-project-structure.md` | Layouts, directories, config composition |
| N3 | `N3-naming-conventions.md` | Modules, classes, functions, constants, tests |
| N4 | `N4-lang-python.md` | Typing, control flow, performance, async |
| N4 | `N4-libraries.md` | Dependency choices, Rust-backed mandates |
| N5 | `N5-error-handling.md` | Exceptions, Result pattern, structured logging |
| N6 | `N6-testing.md` | Pytest, coverage, fixtures, parametrize |

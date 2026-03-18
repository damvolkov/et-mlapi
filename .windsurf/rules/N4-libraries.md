---
description: Library constraints. Which libraries to use and when. Relevant when choosing or adding dependencies.
alwaysApply: false
---

# Libraries

Rust-backed alternative exists → MUST use it. No exceptions. Package manager: uv only, no pip.

## Web [MUST]

- fastapi[standard]: full APIs, prototypes, large apps
- robyn: ML/AI real-time APIs (Rust-backed, multi-process)
- pydantic + pydantic-settings: validation, config

## HTTP [MUST]

- httpx: async client
- httpx-retries: retry transport

## Storage [MUST]

- redis (async): AsyncRedis, pipelines, hexpire
- redisvl: vector indexing, HybridQuery

## Data & Serialization

- orjson [MUST]: Rust-backed JSON — import orjson as json. Never stdlib json.
- polars [MUST]: Rust-backed DataFrames — never pandas
- glom [MUST]: nested structure access
- furl [MUST]: URL construction
- aiofiles [MUST]: async file I/O

## Runtime & Dispatch [MUST]

- beartype: runtime typing via decorate_methods(beartype)
- ovld [MUST]: multiple dispatch + Literal. Type-friendly, async-compatible. First choice for dispatch.
- plum-dispatch [MUST]: alternative multiple dispatch. Type-friendly, async-compatible.
- cachetools: TTL-based caching

## ML & NLP

- openai: Azure OpenAI (LLM + embeddings)
- dspy [PREFER]: code-first LLM pipelines — modules (Predict, ChainOfThought, ReAct), optimizers (MIPROv2, BootstrapFewShot), typed signatures, multi-model portable (dspy.ai)
- scikit-learn, numpy: computation
- spacy: NLP processing
- joblib: parallel processing

## CLI [MUST]

- typer: CLI commands
- rich: tables, console, RichHandler (DEV)

## Scheduling & Security

- apscheduler [MUST]: AsyncIOScheduler
- pyjwt: JWT handling
- asgi-correlation-id: request tracing
- python-json-logger: structured logs (PROD)

## LLM Evaluation & Testing

- promptfoo [PREFER]: CLI/lib for LLM eval, red-teaming (OWASP LLM Top 10), CI/CD native, 50+ providers, runs locally (github.com/promptfoo/promptfoo)
- deepeval [PREFER]: Pytest-like LLM eval, 50+ metrics, RAG/agent/chatbot eval, red-team scanning, synthetic data gen (github.com/confident-ai/deepeval)
- evidently: ML/LLM monitoring, 100+ metrics, drift detection, dashboards, CI/CD test suites (github.com/evidentlyai/evidently)

## LLM Observability & Tracing

- logfire [PREFER]: Pydantic team, OTel-native, unified traces for LLM/agents/API/DB, FastAPI+Pydantic+Redis integrations, DSPy support, free tier (pydantic.dev/logfire)
- langfuse [PREFER]: open-source LLM observability, self-hosted, traces/sessions/spans, prompt management, evals, Python SDK v3 with decorators (github.com/langfuse/langfuse)
- arize-phoenix: open-source, OpenTelemetry-native, drift detection, clustering, embedded evals (github.com/Arize-ai/phoenix)
- agentops: agent-specific monitoring, cost tracking, execution graphs, replay analytics, integrates CrewAI/LangChain/OpenAI Agents (github.com/AgentOps-AI/agentops)
- braintrust: eval-first observability, CI/CD deployment blocking, cost analytics (braintrust.dev)

## LLM Instrumentation (OpenTelemetry)

- openinference: OTel semantic conventions for LLM/embedding/retrieval tracing (github.com/Arize-ai/openinference)
- openllmetry: auto-instrumentation for 20+ LLM providers via OTel (github.com/traceloop/openllmetry)

## Dev & Quality

- ruff [PREFER]: Rust-backed linter/formatter
- ty [PREFER]: Astral Rust type checker
- pre-commit
- pytest [MUST] + plugins [MUST]: pytest-asyncio, pytest-mock, pytest-xdist, pytest-rerunfailures, pytest-cov
- polyfactory [MUST]: model factories (DataclassFactory, ModelFactory). Replaces factory-boy.
- pytest-httpserver [MUST]: real mock HTTP server (werkzeug-based) for unit tests
- respx [MUST]: httpx transport-level mocking for integration tests
- fakeredis [MUST]: in-memory Redis mock

## Build

hatchling + uv-dynamic-versioning (Git-based PEP 440)

## Tunneling

- frp: self-hosted reverse proxy — TCP/UDP/HTTP (github.com/fatedier/frp)
- zrok: zero-trust sharing, peer-to-peer (github.com/openziti/zrok)

## Commands

```bash
uv add <package>             # production
uv add --group dev <package> # dev
uv sync --dev                # sync all
```

---
name: devops
description: DevOps tooling. uv, Makefile, Dockerfile, Docker Compose, GitHub Actions, pre-commit, Helm, ruff/ty config. Use when working with Docker, CI/CD, Makefile, deployment, or dev environment.
---

# DevOps

## uv (package manager — no pip)

```bash
uv sync --dev          # sync all deps
uv sync --locked       # production (locked)
uv add <package>       # add prod dep
uv add --group dev <p> # add dev dep
uv run <command>       # run in venv
uv run pytest          # tests
uv run fastapi dev     # dev server
uv run ruff check      # lint
uv run ty check        # type check
```

## Makefile

Development: `make dev` (port 8012 + Redis + NLP), `make prod`, `make infra` (compose up), `make down`, `make log <name>`.

Quality: `make lint` (ruff check --fix + format), `make type` (ty check), `make sync`, `make install`.

Docker: `make docker-build`, `make docker-up`, `make docker-test`, `make docker-down`.

Testing: `make ingest` (flush + ingest), `make regression`, `make regression ID=<id>`.

Env vars: PROJECT=ai-haven, SERVICE_PORT=8012, ENVIRONMENT=DEV, PACKAGE=app.

## Dockerfile

Builder stage:

```dockerfile
FROM ghcr.io/astral-sh/uv:0.8.0-python3.13-bookworm AS builder
ARG ENABLE_DEBUG=false
```

UV_COMPILE_BYTECODE=1, UV_LINK_MODE=copy. Git for uv-dynamic-versioning. ENABLE_DEBUG=true adds debugpy.

Runtime stage: non-root user (1000), only curl + git, EXPOSE 8012. CMD: debugpy (debug) or fastapi run (prod).

Build: `SHELL ["/bin/bash", "-o", "pipefail", "-c"]`, --no-install-recommends, `--mount=type=cache,target=/root/.cache/uv`.

## Docker Compose

Single file: compose.yml at root. Multiple: docker/compose-{infra,dev,ml}.yml.

Service skeleton:

```yaml
services:
  <name>:
    image: <registry>/<image>:<tag>       # pin versions, never :latest in prod
    container_name: <project>-<service>
    hostname: <service>
    env_file: .env
    ports: ["<host>:<container>"]
    healthcheck:
      test: ["CMD", "<check>"]
      interval: <i>
      timeout: <t>
      retries: <r>
      start_period: <s>
    restart: unless-stopped
    networks: [<net>]
    depends_on:
      <dep>:
        condition: service_healthy
```

Healthchecks:

```yaml
# redis
test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
interval: 5s, timeout: 3s, retries: 5

# http
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
interval: 30s, timeout: 10s, retries: 5, start_period: 10s

# wget (no curl)
test: ["CMD", "wget", "-q", "--spider", "http://localhost:7880"]

# tcp
test: ["CMD", "nc", "-z", "localhost", "10200"]
```

GPU:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Env patterns: env_file for shared, environment for docker-internal overrides (service DNS), inline YAML blocks for complex config, `${VAR:-default}` for fallbacks.

App service (dev):

```yaml
api:
  build: { context: ., dockerfile: Dockerfile }
  container_name: api
  env_file: .env
  ports: ["${API_PORT:-8000}:8000"]
  volumes: ["./src:/app/src"]
  command: uvicorn app.__main__:create_api_app --factory --host 0.0.0.0 --port 8000 --reload
  restart: unless-stopped
  depends_on:
    redis: { condition: service_healthy }
```

Infra reference:

```yaml
services:
  redis:
    image: redis/redis-stack:latest
    container_name: project-redis
    hostname: redis
    env_file: .env
    command: redis-stack-server --requirepass ${REDIS_PASSWORD}
    ports: ["6380:6379", "8002:8001"]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: always
    networks: [project-net]

  livekit:
    image: livekit/livekit-server:v1.9
    container_name: livekit
    hostname: livekit
    env_file: .env
    command: --config /etc/livekit.yaml
    ports: ["7880:7880", "7881:7881/udp", "60000-60050:60000-60050/udp"]
    volumes: ["./docker/livekit/livekit.yaml:/etc/livekit.yaml"]
    environment: ["REDIS_ADDRESS=redis:6379"]
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:7880"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks: [project-net]
    depends_on:
      redis: { condition: service_healthy }

networks:
  project-net:
    driver: bridge
```

## Pre-Commit

On commit: end-of-file-fixer, trailing-whitespace, check-merge-conflict, ruff (lint + format, excludes test/), ty-check (local, excludes test/).

On push: semgrep (OWASP, CWE, Gitleaks), gitleaks.

## GitHub Actions

- dev_ci.yml: push to dev → Docker build, push ECR, optional K8s deploy
- main_ci.yml: push to main → semver release, Docker build/push
- release_ci.yml: push to release/X.Y.Z
- health.yaml: PR/push → Docker build, lint, Helm validate
- helm_ci.yml: dispatch → Helm deploy
- promote_ci.yml: dispatch → promote Docker image between ECRs

## Helm

```
helm/chart/ → Chart.yaml, values.yaml, templates/ (deployment, hpa, ingress, pdb, secrets, svc)
helm/dev/ → dev1.yaml, dev2.yaml (env overrides)
```

## Tool Config

```toml
[tool.ruff]
line-length = 200

[tool.ty.src]
exclude = ["test/"]

[tool.ty.rules]
useless-overload-body = "ignore"    # ovld compat
invalid-overload = "ignore"         # ovld compat
unused-ignore-comment = "ignore"
```

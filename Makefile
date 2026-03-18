PROJECT ?= et-mlapi
PACKAGE ?= src/et_mlapi
SERVICE_PORT ?= 8012

OS := $(shell uname -s)

BOLD   := \033[1m
RESET  := \033[0m
GREEN  := \033[1;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
CYAN   := \033[0;36m
RED    := \033[0;31m

export PYTHONPATH := $(CURDIR)/src

COMPOSE_FILE := compose.yml

.PHONY: help install sync lock lint type test test-integration check \
        dev prod docker-build docker-up docker-down log clean


# Help

help:
	@echo "$(BOLD)$(BLUE)et-mlapi$(RESET) — ML API Template (Robyn + Pydantic + WebSockets + SSE)"
	@echo ""
	@echo "$(BOLD)Setup:$(RESET)"
	@echo "  $(GREEN)make install$(RESET)          Install everything (uv, deps, pre-commit)"
	@echo "  $(GREEN)make sync$(RESET)             Sync dependencies from lockfile"
	@echo ""
	@echo "$(BOLD)Development:$(RESET)"
	@echo "  $(GREEN)make dev$(RESET)              API on :$(SERVICE_PORT) with reload"
	@echo "  $(GREEN)make prod$(RESET)             Production mode"
	@echo ""
	@echo "$(BOLD)Quality:$(RESET)"
	@echo "  $(GREEN)make lint$(RESET)             Ruff check + format"
	@echo "  $(GREEN)make type$(RESET)             ty type checker"
	@echo "  $(GREEN)make test$(RESET)             Unit tests (parallel, coverage >90%)"
	@echo "  $(GREEN)make test-integration$(RESET) Integration tests"
	@echo "  $(GREEN)make check$(RESET)            lint + type + test"
	@echo ""
	@echo "$(BOLD)Docker:$(RESET)"
	@echo "  $(GREEN)make docker-up$(RESET)        Build + start (port :$(SERVICE_PORT))"
	@echo "  $(GREEN)make docker-down$(RESET)      Stop"
	@echo "  $(GREEN)make docker-build$(RESET)     Build image only"
	@echo "  $(GREEN)make log$(RESET)              Tail container logs"
	@echo ""
	@echo "$(BOLD)Cleanup:$(RESET)"
	@echo "  $(GREEN)make clean$(RESET)            Remove caches and build artifacts"


# Setup & Dependencies

install:
	@echo "$(GREEN)[1/4] Installing uv$(RESET)"
ifeq ($(OS),Linux)
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
else ifeq ($(OS),Darwin)
	@command -v uv >/dev/null 2>&1 || brew install uv
endif
	@echo "$(GREEN)[2/4] Syncing Python dependencies$(RESET)"
	@uv sync --dev --quiet
	@echo "$(GREEN)[3/4] Installing pre-commit hooks$(RESET)"
	@uv run pre-commit install > /dev/null
	@echo "$(GREEN)[4/4] Done$(RESET)"

sync:
	@uv sync --dev

lock:
	@uv lock


# Quality & Testing

lint:
	@uv run ruff check --fix $(PACKAGE) tests/
	@uv run ruff format $(PACKAGE) tests/

type:
	@uv run ty check

test:
	@uv run pytest tests/unit -n auto -v -m 'not slow' --cov --cov-report=term-missing

test-integration:
	@uv run pytest tests/integration -v -m slow

check: lint type test


# Development

dev:
	@echo "$(CYAN)=== API: http://localhost:$(SERVICE_PORT) [reload] ===$(RESET)"
	@uv run python -m robyn src/et_mlapi/main.py --dev

prod:
	@echo "$(CYAN)=== Production mode ===$(RESET)"
	@ENVIRONMENT=PROD DEBUG=False uv run python -m et_mlapi.main


# Docker

docker-build:
	@echo "$(CYAN)=== Building Docker image ===$(RESET)"
	@docker compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)=== Build complete ===$(RESET)"

docker-up: docker-build
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)=== Running at http://localhost:$(SERVICE_PORT) ===$(RESET)"

docker-down:
	@docker compose -f $(COMPOSE_FILE) down

log:
	@docker compose -f $(COMPOSE_FILE) logs -f


# Cleanup

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf dist/ build/ *.egg-info/
	@echo "$(GREEN)=== Clean ===$(RESET)"

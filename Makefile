# Orion — common dev commands.
# Run `make help` to see all targets.

SHELL    := /bin/bash
VENV     := .venv
PY       := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
UVICORN  := $(VENV)/bin/uvicorn
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff

HOST     ?= 0.0.0.0
PORT     ?= 8000
Q        ?= what is happening in tech today?

.DEFAULT_GOAL := help

# ---------- help ----------

.PHONY: help
help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	      /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- setup ----------

.PHONY: venv
venv:  ## Create the Python virtualenv (idempotent).
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip --quiet

.PHONY: install
install: venv  ## Install runtime + dev dependencies.
	$(PIP) install -e ".[dev]"

.PHONY: env
env:  ## Create a .env from .env.example if it does not exist.
	@test -f .env && echo ".env already exists" || (cp .env.example .env && echo "Created .env — fill in your API keys.")

.PHONY: setup
setup: install env  ## One-shot: venv + deps + .env.

# ---------- run ----------

.PHONY: dev
dev:  ## Run the API with auto-reload (http://localhost:$(PORT)).
	$(UVICORN) app.main:app --reload --host $(HOST) --port $(PORT)

.PHONY: run
run:  ## Run the API without reload (closer to production).
	$(UVICORN) app.main:app --host $(HOST) --port $(PORT)

.PHONY: ask
ask:  ## Ask Orion from the CLI:  make ask Q="what's up in markets?"
	$(PY) -m app.cli --trace "$(Q)"

.PHONY: ask-json
ask-json:  ## Same as `ask` but full JSON response.
	$(PY) -m app.cli --json "$(Q)"

# ---------- smoke tests against a running server ----------

.PHONY: health
health:  ## Hit /health on the running server.
	@curl -fsS http://$(HOST):$(PORT)/health | python3 -m json.tool

.PHONY: tools
tools:  ## List registered tools via REST.
	@curl -fsS http://$(HOST):$(PORT)/tools | python3 -m json.tool

.PHONY: curl-ask
curl-ask:  ## Hit POST /ask:  make curl-ask Q="..."
	@curl -fsS -X POST http://$(HOST):$(PORT)/ask \
	  -H 'content-type: application/json' \
	  -d "$$(python3 -c 'import json,sys; print(json.dumps({"query": "$(Q)"}))')" \
	  | python3 -m json.tool

# ---------- quality ----------

.PHONY: test
test:  ## Run the full pytest suite.
	$(PYTEST) -q

.PHONY: test-watch
test-watch:  ## Re-run tests on file change (requires `pip install pytest-watch`).
	@which $(VENV)/bin/ptw >/dev/null 2>&1 || $(PIP) install pytest-watch --quiet
	$(VENV)/bin/ptw -- -q

.PHONY: lint
lint:  ## Lint with ruff.
	$(RUFF) check app tests

.PHONY: format
format:  ## Auto-format with ruff.
	$(RUFF) format app tests
	$(RUFF) check --fix app tests

# ---------- housekeeping ----------

.PHONY: clean
clean:  ## Remove caches.
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: distclean
distclean: clean  ## Also remove the virtualenv.
	rm -rf $(VENV)

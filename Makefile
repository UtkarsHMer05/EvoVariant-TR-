# EvoVariant-TR — single project control surface (Milestone 20).
#
# One canonical set of commands for setup, validation, data, scoring, UI.
# `make help` lists every target with its purpose.
#
# Cost policy (Milestone 19):
#   - `make validate` and all default targets are CPU/local only and free.
#   - GPU targets are clearly named `gpu-*`, are NEVER the default goal,
#     print a cost warning, and refuse to run without an explicit cost
#     acknowledgement. `gpu-full` additionally requires the on-disk
#     approval artifact (artifacts/approvals/full_run_approval.json).
#   - No target hides a destructive operation; there is deliberately no
#     generic `clean` that can delete data.

SHELL := /bin/bash
.DEFAULT_GOAL := help

VENV ?= .venv
PYTHON := $(VENV)/bin/python

# Overridable paths (make data-verify MANIFEST=... BASE_DIR=... REGISTRY=...).
PROTOCOL ?= research/protocol/protocol.yaml
MANIFEST ?=
BASE_DIR ?= data/raw
REGISTRY ?= experiments/registry

# Cost acknowledgement (must be exported in the calling environment).
COST_ACK_ENV := EVOVARIANT_TR_PAID_COMPUTE_ACK
COST_ACK_VALUE := I_ACCEPT_COSTS
APPROVAL ?= artifacts/approvals/full_run_approval.json

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help (default target)
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "GPU targets (gpu-pilot, gpu-full) may cost money. They print a cost"
	@echo "warning and require $(COST_ACK_ENV)=$(COST_ACK_VALUE) in the environment."

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

.PHONY: check-venv
check-venv:
	@test -x $(PYTHON) || { echo "ERROR: $(PYTHON) not found. Run: make bootstrap" >&2; exit 2; }

.PHONY: bootstrap
bootstrap: ## Create .venv and install the core package + dev extras (CPU only, free)
	python3.12 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip -q
	$(PYTHON) -m pip install -e ".[dev]"
	@echo "OK: $(VENV) ready (CPU only; no CUDA/GPU packages installed)"

# ---------------------------------------------------------------------------
# Validation (all free, CPU/local only)
# ---------------------------------------------------------------------------

.PHONY: validate
validate: ## Run the full local gate: secret scan, ruff, mypy, pytest, coverage floor
	./scripts/validate_local.sh

.PHONY: secrets
secrets: ## Scan tracked files for credential patterns
	./scripts/check_secrets.sh

.PHONY: lint
lint: ## Ruff lint on src, tests, scripts
	$(MAKE) check-venv
	$(PYTHON) -m ruff check src tests scripts

.PHONY: typecheck
typecheck: ## mypy strict on the core package
	$(MAKE) check-venv
	$(PYTHON) -m mypy

.PHONY: test
test: ## Run the default test tiers (unit + contract + integration; free)
	$(MAKE) check-venv
	$(PYTHON) -m pytest

.PHONY: coverage
coverage: ## Run tests with the 95% coverage floor
	$(MAKE) check-venv
	$(PYTHON) -m pytest --cov --cov-report=term -q

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

.PHONY: frontend-install
frontend-install: ## Install frontend dependencies (npm ci, apps/web)
	cd apps/web && npm ci

.PHONY: frontend-build
frontend-build: ## Typecheck + production build of apps/web
	cd apps/web && npx tsc --noEmit && NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL="$${NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL:-http://localhost:8000}" npm run build

# ---------------------------------------------------------------------------
# Data / protocol / registry verification (all free, CPU/local only)
# ---------------------------------------------------------------------------

.PHONY: protocol-verify
protocol-verify: ## Validate the frozen research protocol YAML
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli validate-protocol --protocol $(PROTOCOL)

.PHONY: ml-protocol-verify
ml-protocol-verify: ## Validate the additive ML-extension control plane and hashes
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli validate-ml-control-plane --repo-root .

.PHONY: schema-verify
schema-verify: ## Validate all checked-in JSON Schemas
	$(MAKE) check-venv
	$(PYTHON) -c "import json; from pathlib import Path; import jsonschema; [jsonschema.Draft202012Validator.check_schema(json.loads(p.read_text())) for p in Path('research/schemas').glob('*.schema.json')]; print('OK: all research schemas valid')"

.PHONY: data-verify
data-verify: ## Verify a file manifest against on-disk data (MANIFEST=... BASE_DIR=...)
	$(MAKE) check-venv
	@test -n "$(MANIFEST)" || { echo "ERROR: set MANIFEST=path/to/manifest.json" >&2; exit 2; }
	$(PYTHON) scripts/verify_manifest.py --manifest $(MANIFEST) --base-dir $(BASE_DIR)

.PHONY: data-qc
data-qc: ## Recompute the temporal audit and deterministic ML-extension split manifests
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli build-ml-splits \
		--t0 data/raw/clinvar/variant_summary_2025-01.txt.gz \
		--t1 data/raw/clinvar/variant_summary_2026-08.txt.gz \
		--t0-manifest research/data_manifests/clinvar_t0.json \
		--t1-manifest research/data_manifests/clinvar_t1.json \
		--output-dir data/derived/ml_extension/phase3

.PHONY: modal-smoke
modal-smoke: ## Run a no-spend Modal preflight and append a deferred/planned cost record
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli modal-smoke

.PHONY: registry-verify
registry-verify: ## Verify the immutable experiment registry (REGISTRY=...)
	$(MAKE) check-venv
	$(PYTHON) scripts/verify_registry.py --registry-dir $(REGISTRY)

.PHONY: model-registry-verify
model-registry-verify: ## Verify ML-extension model candidate manifests (free/local)
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli verify-model-registry

# ---------------------------------------------------------------------------
# GPU targets — COST MONEY, never default, explicit acknowledgement required
# ---------------------------------------------------------------------------

.PHONY: gpu-pilot
gpu-pilot: ## [PAID] Run the multi-gene pilot scoring on Modal (M55+; not yet implemented)
	@echo "=============================================================="
	@echo " WARNING: gpu-pilot may incur PAID GPU costs on Modal."
	@echo " Requires: export $(COST_ACK_ENV)=$(COST_ACK_VALUE)"
	@echo "=============================================================="
	@test "$$(printenv $(COST_ACK_ENV))" = "$(COST_ACK_VALUE)" || { \
		echo "REFUSED: $(COST_ACK_ENV) is not set to $(COST_ACK_VALUE)." >&2; \
		echo "No GPU work will run. See docs/security/SECRETS_AND_COST_POLICY.md." >&2; \
		exit 1; }
	$(MAKE) check-venv
	@echo "Cost gate passed, but the pilot scoring pipeline is not implemented yet."
	@echo "It lands at Milestone 55 (end-to-end scoring orchestration)."
	@exit 1

.PHONY: gpu-full
gpu-full: ## [PAID] Run the full primary scoring (M69+; requires ack + approval artifact)
	@echo "=============================================================="
	@echo " WARNING: gpu-full runs the FULL primary scoring run on Modal."
	@echo " Requires: export $(COST_ACK_ENV)=$(COST_ACK_VALUE)"
	@echo "            AND an approval artifact at $(APPROVAL)"
	@echo "=============================================================="
	@test "$$(printenv $(COST_ACK_ENV))" = "$(COST_ACK_VALUE)" || { \
		echo "REFUSED: $(COST_ACK_ENV) is not set to $(COST_ACK_VALUE)." >&2; \
		exit 1; }
	$(MAKE) check-venv
	$(PYTHON) -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from evovariant_tr.cost_policy import require_full_run_approval; a = require_full_run_approval(Path('$(APPROVAL)')); print(f'OK: approval artifact verified (max USD {a.max_budget_usd}, {a.gpu_type})')"
	@echo "Cost and approval gates passed, but full scoring is not implemented yet."
	@echo "It lands at Milestone 69 (frozen primary analysis)."
	@exit 1

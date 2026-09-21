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
PHASE_EXEC_ARGS ?= --help
FEATURES ?=
TRAIN_OUTPUT ?= research/runs/phase8_training
HPO_CONFIGS ?=
HPO_OUTPUT ?= research/runs/phase9_hpo
PREDICTIONS ?=
ENSEMBLE_OUTPUT ?= research/runs/phase11_ensemble.json
ENSEMBLE_LEFT_MODEL ?=
ENSEMBLE_RIGHT_MODEL ?=

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
bootstrap: ## Create .venv and install core, API, and dev extras (CPU only, free)
	python3.12 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip -q
	$(PYTHON) -m pip install -e ".[dev,api]"
	@echo "OK: $(VENV) ready (CPU only; no CUDA/GPU packages installed; API extra included)"

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

.PHONY: test-scientific
test-scientific: ## Run the explicit scientific validation tier (free/local)
	$(MAKE) check-venv
	$(PYTHON) -m pytest --run-scientific -m scientific tests/scientific

.PHONY: test-e2e
test-e2e: ## Run the explicit browser/API E2E tier (no paid compute)
	$(MAKE) check-venv
	$(PYTHON) -m pytest --run-e2e -m e2e tests/e2e

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
frontend-build: ## Lint + typecheck + production build of apps/web
	cd apps/web && node node_modules/eslint/bin/eslint.js src && npx tsc --noEmit && NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL="$${NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL:-http://localhost:8000}" npm run build

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

.PHONY: phase3-audit
phase3-audit: ## Run the detailed Phase 3 source, temporal, reference, and leakage audit
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase3-integrity-audit \
		--repo-root . \
		--output artifacts/phase3_integrity_audit_20260921.json

.PHONY: phase3-reference-manifest
phase3-reference-manifest: ## Verify the frozen Broad GRCh38 assets and write their metadata manifest
	$(MAKE) check-venv
	$(PYTHON) research/scripts/acquire_grch38_reference.py

.PHONY: phase3-reference-audit
phase3-reference-audit: ## Independently validate every authoritative cohort REF base against GRCh38
	$(MAKE) check-venv
	$(PYTHON) scripts/phase3_reference_validation.py

.PHONY: phase3-freeze
phase3-freeze: ## Run Phase 3 audit/reference gates and freeze the ML-extension manifests
	$(MAKE) data-qc
	$(MAKE) phase3-audit
	$(MAKE) phase3-reference-manifest
	$(MAKE) phase3-reference-audit
	$(PYTHON) scripts/freeze_phase3_cohort.py

.PHONY: phase5-smoke
phase5-smoke: ## Run the bounded real Nucleotide Transformer and Caduceus H100 smokes
	$(MAKE) check-venv
	@test "$${$(COST_ACK_ENV)}" = "$(COST_ACK_VALUE)" || { \
		echo "REFUSED: set $(COST_ACK_ENV)=$(COST_ACK_VALUE) for approved Phase 5 smokes" >&2; \
		exit 1; \
	}
	$(VENV)/bin/modal run scripts/phase5_model_smoke.py

.PHONY: modal-smoke
modal-smoke: ## Run a no-spend Modal preflight and append a deferred/planned cost record
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli modal-smoke

# ---------------------------------------------------------------------------
# ML-extension phase surfaces (free/local; gated phases record status only)
# ---------------------------------------------------------------------------

.PHONY: benchmark-zero-shot
benchmark-zero-shot: ## Record/run the Phase 6 multi-model benchmark gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 6 --family ZS \
		--command-name benchmark-zero-shot --output research/runs/phase6_zs_status.json \
		--blocker "current approval does not cover the exact full Phase 6 workload" \
		--blocker "full-cohort batch parity and endpoint execution evidence are absent" \
		--blocker "no completed Phase 6 scientific result is registered"

.PHONY: phase-execute
phase-execute: ## Run an explicitly approved, resumable Phase 6/7 execution (PHASE_EXEC_ARGS=...)
	$(MAKE) check-venv
	@echo "Approval-gated Phase 6/7 runner; default invocation prints help and makes no network request."
	$(PYTHON) scripts/phase_execute.py $(PHASE_EXEC_ARGS)

.PHONY: extract-features
extract-features: ## Record/run the Phase 7 representation extraction gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 7 --family REP \
		--command-name extract-features --output research/runs/phase7_rep_status.json \
		--blocker "no approved full Phase 7 extraction or completed feature cache exists" \
		--blocker "Phase 6 zero-shot outputs are not registered"

.PHONY: train
train: ## Record/run the Phase 8 downstream training gate
	$(MAKE) check-venv
	@if [ -n "$(FEATURES)" ]; then \
		$(PYTHON) scripts/train_from_features.py --features "$(FEATURES)" \
			--output-dir "$(TRAIN_OUTPUT)"; \
	else \
		$(PYTHON) -m evovariant_tr.cli phase-status --phase 8 --family CLF \
		--command-name train --output research/runs/phase8_clf_status.json \
		--blocker "verified frozen feature cache is unavailable" \
		--blocker "Phase 7 representation extraction is blocked"; \
	fi

.PHONY: hpo
hpo: ## Record/run the Phase 9 validation-only HPO gate
	$(MAKE) check-venv
	@if [ -n "$(FEATURES)" ] && [ -n "$(HPO_CONFIGS)" ]; then \
		$(PYTHON) scripts/hpo_from_features.py --features "$(FEATURES)" \
			--configs "$(HPO_CONFIGS)" --output-dir "$(HPO_OUTPUT)"; \
	else \
		$(PYTHON) -m evovariant_tr.cli phase-status --phase 9 --family HPO \
		--command-name hpo --output research/runs/phase9_hpo_status.json \
		--blocker "no registered development feature artifact exists" \
		--blocker "Phase 8 training is blocked"; \
	fi

.PHONY: finetune-smoke
finetune-smoke: ## Record/run the Phase 10 PEFT/fine-tuning gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 10 --family FT \
		--command-name finetune-smoke --output research/runs/phase10_ft_status.json \
		--status DEFERRED \
		--blocker "official training path and tiny GPU smoke are unverified" \
		--blocker "adaptation is formally deferred by compute and current approval scope"

.PHONY: ensemble
ensemble: ## Record/run the Phase 11 ensemble gate
	$(MAKE) check-venv
	@if [ -n "$(PREDICTIONS)" ] && [ -n "$(ENSEMBLE_LEFT_MODEL)" ] && [ -n "$(ENSEMBLE_RIGHT_MODEL)" ]; then \
		$(PYTHON) scripts/analyze_ensemble.py --predictions "$(PREDICTIONS)" \
			--left-model "$(ENSEMBLE_LEFT_MODEL)" --right-model "$(ENSEMBLE_RIGHT_MODEL)" \
			--output "$(ENSEMBLE_OUTPUT)"; \
	else \
		$(PYTHON) -m evovariant_tr.cli phase-status --phase 11 --family ENS \
		--command-name ensemble --output research/runs/phase11_ens_status.json \
		--blocker "registered base-model predictions are unavailable" \
		--blocker "OOF stack inputs do not exist"; \
	fi

.PHONY: evaluate
evaluate: ## Record/run the Phase 14 locked statistical evaluation gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 14 --family STAT \
		--command-name evaluate --output research/runs/phase14_stat_status.json \
		--blocker "frozen model/configuration does not exist" \
		--blocker "locked test evaluation is not authorized"

.PHONY: calibration-abstention
calibration-abstention: ## Record/run the Phase 12 calibration and abstention gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 12 --family CAL_ABS \
		--command-name calibration-abstention --output research/runs/phase12_cal_abs_status.json \
		--blocker "no registered development predictions exist" \
		--blocker "locked-test labels are unavailable for selection"

.PHONY: robustness-ablation
robustness-ablation: ## Record/run the Phase 13 ablation and robustness gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 13 --family ABL_ROB \
		--command-name robustness-ablation --output research/runs/phase13_abl_rob_status.json \
		--blocker "frozen base-model outputs do not exist" \
		--blocker "predeclared matrix cannot be evaluated yet"

.PHONY: batch-run
batch-run: ## Record/run the Phase 15 batch pipeline gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 15 --family BATCH \
		--command-name batch-run --output research/runs/phase15_batch_status.json \
		--blocker "Evo2 is verified for single-variant scoring but full-cohort batch parity is unverified" \
		--blocker "full-cohort batch authorization and remote batch smoke are absent"

.PHONY: web-check
web-check: ## Run the frontend lint/typecheck/build gate
	$(MAKE) frontend-build

.PHONY: web-e2e
web-e2e: ## Run committed Playwright workbench journeys (local browser only)
	cd apps/web && node node_modules/playwright/cli.js install chromium && NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL="$${NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL:-http://127.0.0.1:8000}" npm run test:e2e

.PHONY: ui-check
ui-check: ## Record/run the Phase 16 research workbench gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 16 --family UI \
		--command-name ui-check --output research/runs/phase16_ui_status.json \
		--blocker "registered experiment outputs are unavailable" \
		--blocker "scientific result panels remain evidence-gated until immutable outputs exist"

.PHONY: figures
figures: ## Record/run the Phase 17 registry-driven figures gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli generate-figure-manifest \
		--registry $(REGISTRY) --repo-root . --output research/runs/phase17_fig_status.json
	$(PYTHON) -m evovariant_tr.cli render-figure-bundle \
		--manifest research/runs/phase17_fig_status.json --repo-root . --output-dir research/figures

.PHONY: release-check
release-check: ## Record/run the Phase 19 final release gate
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 19 --family RELEASE \
		--command-name release-check --output research/runs/phase19_release_status.json \
		--blocker "Phase 6/7 and downstream scientific result artifacts are unresolved" \
		--blocker "locked evaluation, figure-regeneration, registry, and current approval gates are unresolved"

.PHONY: clean-room
clean-room: ## Run the free reproducibility status surface
	$(MAKE) check-venv
	$(PYTHON) -m evovariant_tr.cli phase-status --phase 18 --family REPRO \
		--command-name clean-room --output research/runs/phase18_clean_room_status.json \
		--blocker "clean-room full scientific Modal reproduction remains unrun" \
		--blocker "registry-driven figure manifest is BLOCKED because no eligible completed scientific outputs exist"

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

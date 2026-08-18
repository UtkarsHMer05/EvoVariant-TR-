#!/bin/bash
# Single local validation command for EvoVariant-TR (Milestone 17).
#
# Runs the full free/local gate: lint, strict type check, default test tiers
# (unit + contract + integration; modal/scientific/e2e stay gated), and the
# coverage floor. Never launches paid compute.
#
# Usage: ./scripts/validate_local.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "==> secret scan"
"$REPO_ROOT/scripts/check_secrets.sh"

echo "==> ruff"
python -m ruff check src tests scripts

echo "==> mypy (strict)"
python -m mypy

echo "==> pytest (default tiers: unit, contract, integration)"
python -m pytest

echo "==> coverage floor (core deterministic modules)"
python -m pytest --cov --cov-report=term -q

echo "==> validate_local: ALL GATES PASSED"

#!/bin/bash
# Deploy EvoVariant-TR scoring service to Modal (M52, M065).
#
# Requirements:
#   1. modal CLI installed: pip install modal
#   2. modal authenticated: modal login
#   3. Cost acknowledgement: EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS
#
# Usage:
#   ./scripts/deploy_modal.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COST_ACK="${EVOVARIANT_TR_PAID_COMPUTE_ACK:-}"
if [ "$COST_ACK" != "I_ACCEPT_COSTS" ]; then
    echo "WARNING: Paid compute costs will be incurred."
    echo "To acknowledge, set:"
    echo "  export EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS"
    echo "REFUSED: Cost acknowledgement not set."
    exit 1
fi

echo "==> Cost acknowledgement verified."

# Verify the canonical current project identity and reject legacy identities (M19).
if grep -Eq 'variant-analysis-evo2|evovariant-tr-v2' evo2_scorer_app.py src/evovariant_tr/modal_config.py; then
    echo "ERROR: a legacy Modal identity was found in the active deployment files."
    echo "REFUSED: legacy deployment identity forbidden (M19)."
    exit 1
fi
if ! grep -q 'CANONICAL_MODAL_APP = "evovariant-tr"' src/evovariant_tr/modal_config.py; then
    echo "ERROR: canonical Modal app identity is not declared."
    exit 1
fi

echo "==> Canonical Modal identity check passed (evovariant-tr)."
echo "==> Deploying to Modal..."

modal deploy evo2_scorer_app.py

echo "==> Deployment initiated. Check status with: modal app list"

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

# Verify old project identity is not used as the Modal App name (M19)
if grep -q 'modal\.App("variant-analysis-evo2"' evo2_scorer_app.py 2>/dev/null; then
    echo "ERROR: old project identity 'variant-analysis-evo2' found in app."
    echo "REFUSED: old deployment identity forbidden (M19)."
    exit 1
fi

echo "==> Old project identity check passed."
echo "==> Deploying to Modal..."

modal deploy evo2_scorer_app.py

echo "==> Deployment initiated. Check status with: modal app list"

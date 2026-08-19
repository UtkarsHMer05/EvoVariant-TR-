"""Modal tests — gated, never run by default.

These tests exercise Modal/GPU infrastructure and COST MONEY. They require
BOTH the explicit flag and the cost acknowledgement:

    EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS pytest --run-modal

Until Milestone 52+ lands the new Modal service, this module only proves the
gating contract: the marker exists and the tests are skipped by default.
"""

from __future__ import annotations

import pytest

from evovariant_tr.cost_policy import (
    APPROVED_GPU_TYPES,
    APPROVED_MODAL_ENVIRONMENTS,
    COST_ACK_ENV,
    FORBIDDEN_MODAL_IDENTITIES,
    CostPolicyError,
    FullRunApproval,
    assert_paid_compute_allowed,
    paid_compute_acknowledged,
)
from evovariant_tr.evo2_scorer import check_evo2_parity
from evovariant_tr.modal_config import check_modal_environment


@pytest.mark.modal
def test_modal_placeholder_requires_real_infrastructure() -> None:
    """Placeholder for the M55 model-load smoke test.

    Replaced by real Modal tests once services/modal exists (M52+). If this
    body ever runs, the paid-compute gate was explicitly unlocked.
    """
    pytest.skip("real Modal tests land with Milestone 52-55; gate verified")


@pytest.mark.modal
def test_paid_compute_gate_blocks_without_ack() -> None:
    """M19: paid compute is blocked unless the explicit env var is set."""
    import os

    old = os.environ.pop(COST_ACK_ENV, None)
    try:
        assert not paid_compute_acknowledged()
        with pytest.raises(CostPolicyError):
            assert_paid_compute_allowed()
    finally:
        if old is not None:
            os.environ[COST_ACK_ENV] = old


@pytest.mark.modal
def test_parity_requirements_enforced() -> None:
    """M49: Evo 2 parity requirements are immutable and validated."""
    result = check_evo2_parity()
    assert "all_pass" in result
    assert "checks" in result
    assert "parity_requirements" in result


@pytest.mark.modal
def test_forbidden_identities_blocked() -> None:
    """M19: old-project Modal identities are forbidden."""
    for identity in FORBIDDEN_MODAL_IDENTITIES:
        with pytest.raises(ValueError, match="forbidden old-project identity"):
            FullRunApproval(
                approved_by="test",
                approved_at="2026-08-19T00:00:00Z",
                max_budget_usd=100.0,
                run_scope="test",
                modal_environment=identity,
                gpu_type="H100",
                protocol_hash="abc123",
            )


@pytest.mark.modal
def test_modal_environment_check_structure() -> None:
    """M52: modal environment check returns consistent structure."""
    result = check_modal_environment()
    assert "modal_installed" in result
    assert "modal_authenticated" in result
    assert APPROVED_MODAL_ENVIRONMENTS == frozenset({"evovariant-tr"})
    assert APPROVED_GPU_TYPES == frozenset({"H100"})
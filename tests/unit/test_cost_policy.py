"""Tests for evovariant_tr.cost_policy — Milestone 19.

Covers the three acceptance validations:
- Validation 1: No real secret is tracked (tested via redaction + the scanner at M19).
- Validation 2: Full-run command refuses to execute without an approval artifact.
- Validation 3: Paid runs are impossible from ordinary unit tests.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from evovariant_tr import cost_policy
from evovariant_tr.cost_policy import (
    APPROVED_GPU_TYPES,
    APPROVED_MODAL_ENVIRONMENTS,
    COST_ACK_ENV,
    COST_ACK_VALUE,
    CostPolicyError,
    FullRunApproval,
    assert_paid_compute_allowed,
    paid_compute_acknowledged,
    require_full_run_approval,
)


# --------------------------------------------------------------------------- #
#  Happy path: paid_compute_acknowledged / assert_paid_compute_allowed
# --------------------------------------------------------------------------- #
def test_paid_compute_not_acknowledged_by_default(monkeypatch):
    """Ordinary unit tests never set the env var (Validation 3)."""
    monkeypatch.delenv(COST_ACK_ENV, raising=False)
    assert paid_compute_acknowledged() is False


def test_paid_compute_acknowledged_when_set(monkeypatch):
    monkeypatch.setenv(COST_ACK_ENV, COST_ACK_VALUE)
    assert paid_compute_acknowledged() is True


def test_paid_compute_wrong_value_is_not_acknowledged(monkeypatch):
    monkeypatch.setenv(COST_ACK_ENV, "maybe")
    assert paid_compute_acknowledged() is False


def test_assert_paid_compute_raises_without_ack(monkeypatch):
    monkeypatch.delenv(COST_ACK_ENV, raising=False)
    with pytest.raises(CostPolicyError, match="paid compute is blocked"):
        assert_paid_compute_allowed()


def test_assert_paid_compute_passes_with_ack(monkeypatch):
    monkeypatch.setenv(COST_ACK_ENV, COST_ACK_VALUE)
    assert_paid_compute_allowed()  # must not raise


# --------------------------------------------------------------------------- #
#  Happy path: FullRunApproval with valid data
# --------------------------------------------------------------------------- #
def _valid_approval_kwargs():
    return {
        "approved_by": "guide",
        "approved_at": "2026-08-19T12:00:00Z",
        "max_budget_usd": 500.0,
        "run_scope": "full_primary_analysis",
        "modal_environment": "evovariant-tr",
        "gpu_type": "H100",
        "protocol_hash": "374bc2c59941d6001e41c478658ad65fa4e2ae0789829d2625e8801b00ad7c5c",
    }


def test_full_run_approval_valid():
    approval = FullRunApproval(**_valid_approval_kwargs())
    assert approval.modal_environment == "evovariant-tr"
    assert approval.gpu_type == "H100"
    assert approval.max_budget_usd == 500.0


def test_full_run_approval_is_frozen():
    approval = FullRunApproval(**_valid_approval_kwargs())
    with pytest.raises(ValidationError):
        approval.modal_environment = "other"  # type: ignore[misc]


def test_full_run_approval_rejects_extra_fields():
    kw = _valid_approval_kwargs()
    kw["unexpected_field"] = "nope"
    with pytest.raises(ValidationError):
        FullRunApproval(**kw)


# --------------------------------------------------------------------------- #
#  Invalid input: validation failures
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "field, bad_value, match",
    [
        ("max_budget_usd", -1.0, "max_budget_usd must be positive"),
        ("max_budget_usd", 0.0, "max_budget_usd must be positive"),
        ("modal_environment", "variant-analysis-evo2", "forbidden old-project identity"),
        ("modal_environment", "my-cool-env", "must be one of"),
        ("gpu_type", "T4", "must be one of"),
        ("gpu_type", "variant-analysis-evo2", "must be one of"),
        ("approved_by", "", "field must be non-empty"),
        ("run_scope", "   ", "field must be non-empty"),
        ("modal_environment", "", "field must be non-empty"),
        ("gpu_type", "", "field must be non-empty"),
        ("protocol_hash", "   ", "field must be non-empty"),
    ],
)
def test_full_run_approval_rejects_invalid(field, bad_value, match):
    kw = _valid_approval_kwargs()
    kw[field] = bad_value
    with pytest.raises(Exception, match=match):
        FullRunApproval(**kw)


def test_approved_environments_are_disjoint_from_forbidden():
    assert APPROVED_MODAL_ENVIRONMENTS.isdisjoint(
        cost_policy.FORBIDDEN_MODAL_IDENTITIES
    )
    assert APPROVED_GPU_TYPES == {"H100"}


# --------------------------------------------------------------------------- #
#  Validation 2: require_full_run_approval refuses without artifact
# --------------------------------------------------------------------------- #
def test_require_full_run_approval_missing(tmp_path):
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(CostPolicyError, match="requires an explicit approval artifact"):
        require_full_run_approval(missing)


def test_require_full_run_approval_invalid_json(tmp_path):
    bad = tmp_path / "approval.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(CostPolicyError, match="invalid approval artifact"):
        require_full_run_approval(bad)


def test_require_full_run_approval_invalid_content(tmp_path):
    bad = tmp_path / "approval.json"
    bad.write_text(
        json.dumps({"approved_by": "x", "bad": "data"}), encoding="utf-8"
    )
    with pytest.raises(CostPolicyError, match="invalid approval artifact"):
        require_full_run_approval(bad)


def test_require_full_run_approval_valid(tmp_path):
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(_valid_approval_kwargs()), encoding="utf-8"
    )
    result = require_full_run_approval(approval)
    assert isinstance(result, FullRunApproval)
    assert result.modal_environment == "evovariant-tr"


def test_require_full_run_approval_forbidden_identity(tmp_path):
    bad = tmp_path / "approval.json"
    kw = _valid_approval_kwargs()
    kw["modal_environment"] = "variant-analysis-evo2"
    bad.write_text(json.dumps(kw), encoding="utf-8")
    with pytest.raises(CostPolicyError, match="invalid approval artifact"):
        require_full_run_approval(bad)


def test_require_full_run_approval_rejects_stale_protocol_hash(tmp_path):
    approval = tmp_path / "approval.json"
    kw = _valid_approval_kwargs()
    kw["protocol_hash"] = "a" * 64
    approval.write_text(json.dumps(kw), encoding="utf-8")
    with pytest.raises(CostPolicyError, match="does not match the current frozen"):
        require_full_run_approval(approval)

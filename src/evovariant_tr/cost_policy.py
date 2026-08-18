"""Secrets, environment, and cost-control policy for EvoVariant-TR.

Prevents accidental credential exposure and unapproved GPU spending:
- paid compute requires an explicit environment acknowledgement;
- full scoring (M69) requires an explicit approval artifact on disk;
- only approved Modal environment names and GPU types may be used;
- the old project's deployment identities are forbidden.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

COST_ACK_ENV = "EVOVARIANT_TR_PAID_COMPUTE_ACK"
COST_ACK_VALUE = "I_ACCEPT_COSTS"

DEFAULT_APPROVAL_PATH = Path("artifacts/approvals/full_run_approval.json")

# Approved Modal environment names and GPU types for the NEW project.
APPROVED_MODAL_ENVIRONMENTS = frozenset({"evovariant-tr"})
APPROVED_GPU_TYPES = frozenset({"H100"})

# Old-project deployment identities must never be reused as final infra.
FORBIDDEN_MODAL_IDENTITIES = frozenset(
    {"variant-analysis-evo2", "utkarshmer05--variant-analysis-evo2"}
)


class CostPolicyError(RuntimeError):
    """Raised for any cost-control policy violation."""


class FullRunApproval(BaseModel):
    """Explicit, auditable approval artifact required before full scoring."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approved_by: str
    approved_at: str
    max_budget_usd: float
    run_scope: str
    modal_environment: str
    gpu_type: str
    protocol_hash: str

    @field_validator(
        "approved_by", "run_scope", "modal_environment", "gpu_type", "protocol_hash"
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must be non-empty")
        return value

    @field_validator("max_budget_usd")
    @classmethod
    def _positive_budget(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("max_budget_usd must be positive")
        return value

    @field_validator("modal_environment")
    @classmethod
    def _approved_environment(cls, value: str) -> str:
        if value in FORBIDDEN_MODAL_IDENTITIES:
            raise ValueError(
                f"modal_environment {value!r} is a forbidden old-project identity"
            )
        if value not in APPROVED_MODAL_ENVIRONMENTS:
            raise ValueError(
                f"modal_environment must be one of {sorted(APPROVED_MODAL_ENVIRONMENTS)}"
            )
        return value

    @field_validator("gpu_type")
    @classmethod
    def _approved_gpu(cls, value: str) -> str:
        if value not in APPROVED_GPU_TYPES:
            raise ValueError(f"gpu_type must be one of {sorted(APPROVED_GPU_TYPES)}")
        return value


def paid_compute_acknowledged() -> bool:
    return os.environ.get(COST_ACK_ENV) == COST_ACK_VALUE


def assert_paid_compute_allowed() -> None:
    """Runtime gate for anything that spends money.

    Ordinary unit tests never set the acknowledgement, so paid runs are
    impossible from them (Validation 3, Milestone 19).
    """
    if not paid_compute_acknowledged():
        raise CostPolicyError(
            f"paid compute is blocked: set {COST_ACK_ENV}={COST_ACK_VALUE} "
            f"to explicitly acknowledge costs"
        )


def load_full_run_approval(path: str | Path = DEFAULT_APPROVAL_PATH) -> FullRunApproval:
    """Load and validate the approval artifact; refuse loudly if absent/invalid."""
    target = Path(path)
    if not target.is_file():
        raise CostPolicyError(
            f"full scoring requires an explicit approval artifact at {target}; "
            f"none exists. See docs/security/SECRETS_AND_COST_POLICY.md"
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
        return FullRunApproval.model_validate(raw)
    except (CostPolicyError, json.JSONDecodeError, ValueError, TypeError) as exc:
        raise CostPolicyError(f"invalid approval artifact {target}: {exc}") from exc


def require_full_run_approval(
    path: str | Path = DEFAULT_APPROVAL_PATH,
) -> FullRunApproval:
    """Hard gate for the full primary scoring run (enforced again at M69)."""
    return load_full_run_approval(path)

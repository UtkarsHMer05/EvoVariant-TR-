"""Zero-shot benchmark planning and score-direction safeguards."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from evovariant_tr.experiment_control import (
    ExperimentArtifact,
    deferred_artifact,
)
from evovariant_tr.model_registry import RegisteredModel, included_models


@dataclass(frozen=True)
class BenchmarkPlan:
    """A frozen-input plan; it contains no predictions by itself."""

    model_ids: tuple[str, ...]
    split_manifest_hash: str
    locked_test_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_ids": list(self.model_ids),
            "split_manifest_hash": self.split_manifest_hash,
            "locked_test_allowed": self.locked_test_allowed,
            "reason": self.reason,
        }


def harmonize_score(raw_score: float, score_direction: str) -> float:
    """Map a declared direction to a common higher-is-pathogenic convention."""
    if score_direction == "higher_is_more_pathogenic":
        return float(raw_score)
    if score_direction == "higher_is_more_benign":
        return -float(raw_score)
    raise ValueError("score direction must be declared before benchmark comparison")


def validate_benchmark_rows(
    rows: Iterable[dict[str, Any]],
    *,
    purpose: str,
) -> None:
    """Reject locked labels when rows are used for development choices."""
    for row in rows:
        if purpose in {"selection", "hpo", "calibration", "ensemble"}:
            if str(row.get("split")) == "LOCKED_TEST":
                raise ValueError(
                    f"locked-test row {row.get('normalized_variant_id', '<unknown>')} "
                    f"cannot be used for {purpose}"
                )


def build_zero_shot_plan(
    models: tuple[RegisteredModel, ...],
    *,
    split_manifest_hash: str,
    execution_authorized: bool = False,
) -> BenchmarkPlan:
    """Build a benchmark plan and refuse unverified model execution."""
    included = included_models(models)
    if not included:
        return BenchmarkPlan(
            model_ids=(),
            split_manifest_hash=split_manifest_hash,
            locked_test_allowed=False,
            reason="no model manifest has passed the inclusion gate",
        )
    if not execution_authorized:
        return BenchmarkPlan(
            model_ids=tuple(model.model_id for model in included),
            split_manifest_hash=split_manifest_hash,
            locked_test_allowed=False,
            reason="full-cohort execution authorization and batch parity evidence are absent",
        )
    return BenchmarkPlan(
        model_ids=tuple(model.model_id for model in included),
        split_manifest_hash=split_manifest_hash,
        locked_test_allowed=True,
        reason="inputs frozen and execution gate supplied",
    )


def benchmark_status(
    models: tuple[RegisteredModel, ...],
    *,
    split_manifest_hash: str,
) -> ExperimentArtifact:
    """Return a no-result status artifact until an included model is executable."""
    plan = build_zero_shot_plan(models, split_manifest_hash=split_manifest_hash)
    return deferred_artifact(
        phase=6,
        family="ZS",
        blockers=[
            plan.reason,
            "current exact-scope approval and batch parity evidence are absent",
            "no completed Phase 6 scientific result is registered",
        ],
        inputs={"plan": plan.to_dict()},
    )

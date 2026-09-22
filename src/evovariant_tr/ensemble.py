"""Validation-safe ensemble and out-of-fold stacking utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PredictionRow:
    normalized_variant_id: str
    split: str
    model_id: str
    score: float
    label: int | None = None
    oof: bool = False


@dataclass(frozen=True)
class ModelPairSummary:
    left_model: str
    right_model: str
    n_common: int
    disagreement_rate: float
    error_overlap_rate: float | None
    pearson_correlation: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_model": self.left_model,
            "right_model": self.right_model,
            "n_common": self.n_common,
            "disagreement_rate": self.disagreement_rate,
            "error_overlap_rate": self.error_overlap_rate,
            "pearson_correlation": self.pearson_correlation,
        }


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(
        sum((a - mean_left) ** 2 for a in left) * sum((b - mean_right) ** 2 for b in right)
    )
    return numerator / denominator if denominator else None


def compare_model_predictions(
    rows: list[PredictionRow],
    *,
    left_model: str,
    right_model: str,
    split: str = "VALIDATION",
    positive_threshold: float | None = None,
) -> ModelPairSummary:
    """Compare complementary errors without reading locked labels.

    ``None`` preserves the signed-score convention used by foundation-model
    deltas.  Probability rows must pass their operating threshold explicitly;
    the downstream classifier analysis uses ``0.5``.
    """
    selected = [row for row in rows if row.split == split]
    left = {row.normalized_variant_id: row for row in selected if row.model_id == left_model}
    right = {row.normalized_variant_id: row for row in selected if row.model_id == right_model}
    common_ids = sorted(set(left) & set(right))
    if any(
        left[identity].label is None or right[identity].label is None for identity in common_ids
    ):
        raise ValueError("prediction comparison requires labels on the selected development split")
    left_scores = [left[identity].score for identity in common_ids]
    right_scores = [right[identity].score for identity in common_ids]
    def is_positive(score: float) -> bool:
        threshold = 0.0 if positive_threshold is None else positive_threshold
        return score >= threshold

    disagreements = sum(
        is_positive(score_a) != is_positive(score_b)
        for score_a, score_b in zip(left_scores, right_scores, strict=True)
    )
    left_errors = [
        (is_positive(score) != bool(left[identity].label))
        for identity, score in zip(common_ids, left_scores, strict=True)
    ]
    right_errors = [
        (is_positive(score) != bool(right[identity].label))
        for identity, score in zip(common_ids, right_scores, strict=True)
    ]
    both_errors = sum(a and b for a, b in zip(left_errors, right_errors, strict=True))
    either_errors = sum(a or b for a, b in zip(left_errors, right_errors, strict=True))
    return ModelPairSummary(
        left_model=left_model,
        right_model=right_model,
        n_common=len(common_ids),
        disagreement_rate=disagreements / len(common_ids) if common_ids else 0.0,
        error_overlap_rate=both_errors / either_errors if either_errors else None,
        pearson_correlation=_pearson(left_scores, right_scores),
    )


def weighted_mean(scores: list[float], weights: list[float]) -> float:
    """Compute a normalized weighted ensemble score."""
    if len(scores) != len(weights) or not scores:
        raise ValueError("scores and weights must have the same non-empty length")
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("ensemble weights must be non-negative and non-zero")
    return sum(score * weight for score, weight in zip(scores, weights, strict=True)) / sum(weights)


def validate_oof_stack(rows: list[PredictionRow]) -> None:
    """Require out-of-fold train predictions and forbid locked-test stack fitting."""
    if not rows:
        raise ValueError("stacking requires prediction rows")
    for row in rows:
        if row.split == "LOCKED_TEST":
            raise ValueError("stacker fitting cannot use locked-test predictions")
        if row.split == "TRAIN" and not row.oof:
            raise ValueError("every training prediction for stacking must be out-of-fold")
        if row.label is None:
            raise ValueError("stacking fit rows require development labels")


def stack_feature_matrix(
    rows: list[PredictionRow],
) -> tuple[list[str], list[list[float]], list[int]]:
    """Build deterministic OOF matrix for a downstream meta-classifier."""
    validate_oof_stack(rows)
    models = sorted({row.model_id for row in rows})
    by_id: dict[str, dict[str, PredictionRow]] = {}
    for row in rows:
        by_id.setdefault(row.normalized_variant_id, {})[row.model_id] = row
    complete = sorted(identity for identity, values in by_id.items() if set(values) == set(models))
    matrix = [[by_id[identity][model].score for model in models] for identity in complete]
    labels: list[int] = []
    for identity in complete:
        label = by_id[identity][models[0]].label
        if label is None:
            raise ValueError("complete stack rows must have labels")
        labels.append(label)
    return complete, matrix, labels

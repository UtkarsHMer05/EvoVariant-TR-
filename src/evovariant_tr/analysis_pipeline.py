"""Validation-only ensemble, calibration, and abstention analysis.

This module consumes registered-style prediction JSONL artifacts and deliberately
does not provide a path that selects configuration from locked-test labels.  It is
local CPU analysis; foundation-model inference and final locked evaluation remain
separate, approval-gated operations.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

from evovariant_tr.abstention import compute_abstention_analysis, compute_risk_coverage_curve
from evovariant_tr.ensemble import PredictionRow, compare_model_predictions, weighted_mean
from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc, compute_ece


class AnalysisPipelineError(ValueError):
    """Raised when prediction artifacts cannot support safe development analysis."""


def load_prediction_rows(
    path: str | Path,
    *,
    allow_locked_test: bool = False,
) -> list[PredictionRow]:
    """Load validated prediction rows, rejecting accidental locked-test selection."""
    target = Path(path)
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AnalysisPipelineError(f"could not read prediction artifact {target}: {exc}") from exc
    rows: list[PredictionRow] = []
    seen: set[tuple[str, str, str]] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AnalysisPipelineError(f"prediction line {line_number} is not valid JSON") from exc
        if not isinstance(raw, dict):
            raise AnalysisPipelineError(f"prediction line {line_number} is not an object")
        try:
            identity = str(raw["normalized_variant_id"])
            split = str(raw["split"])
            model_id = str(raw["model_id"])
            score = float(raw["score"])
            label_raw = raw["label"]
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisPipelineError(
                f"prediction line {line_number} is missing required fields"
            ) from exc
        if split not in {"TRAIN", "VALIDATION", "LOCKED_TEST"}:
            raise AnalysisPipelineError(f"unsupported prediction split {split!r}")
        if split == "LOCKED_TEST" and not allow_locked_test:
            raise AnalysisPipelineError("locked-test predictions are not allowed for selection")
        if not identity or not model_id or not math.isfinite(score):
            raise AnalysisPipelineError(
                f"prediction line {line_number} has invalid identity or score"
            )
        if not isinstance(label_raw, int) or label_raw not in {0, 1}:
            raise AnalysisPipelineError(f"prediction line {line_number} has an invalid label")
        key = (identity, split, model_id)
        if key in seen:
            raise AnalysisPipelineError(f"duplicate prediction row {key!r}")
        seen.add(key)
        rows.append(
            PredictionRow(
                normalized_variant_id=identity,
                split=split,
                model_id=model_id,
                score=score,
                label=label_raw,
                oof=bool(raw.get("oof", False)),
            )
        )
    if not rows:
        raise AnalysisPipelineError("prediction artifact is empty")
    return rows


def _probability_metrics(scores: list[float], labels: list[int]) -> dict[str, float | int]:
    if len(scores) != len(labels) or not scores or set(labels) != {0, 1}:
        raise AnalysisPipelineError("analysis requires aligned scores and both classes")
    if any(score < 0.0 or score > 1.0 or not math.isfinite(score) for score in scores):
        raise AnalysisPipelineError("probability scores must be finite and in [0, 1]")
    predictions = [int(score >= 0.5) for score in scores]
    positive = sum(labels)
    negative = len(labels) - positive
    tp = sum(pred == 1 and label == 1 for pred, label in zip(predictions, labels, strict=True))
    tn = sum(pred == 0 and label == 0 for pred, label in zip(predictions, labels, strict=True))
    fp = negative - tn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / positive if positive else 0.0
    specificity = tn / negative if negative else 0.0
    ece, max_gap = compute_ece(scores, labels)
    brier = sum(
        (score - label) ** 2
        for score, label in zip(scores, labels, strict=True)
    ) / len(scores)
    epsilon = 1e-15
    nll = -sum(
        label * math.log(max(score, epsilon))
        + (1 - label) * math.log(max(1.0 - score, epsilon))
        for score, label in zip(scores, labels, strict=True)
    ) / len(scores)
    return {
        "auroc": compute_auc_roc(scores, labels),
        "auprc": compute_auc_pr(scores, labels),
        "accuracy": (tp + tn) / len(scores),
        "balanced_accuracy": (recall + specificity) / 2.0,
        "precision": precision,
        "sensitivity": recall,
        "specificity": specificity,
        "f1": 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "brier": brier,
        "nll": nll,
        "ece": ece,
        "max_calibration_gap": max_gap,
        "n": len(scores),
    }


def analyze_validation_ensemble(
    rows: list[PredictionRow],
    *,
    left_model: str,
    right_model: str,
    weights: tuple[float, float] = (0.5, 0.5),
) -> dict[str, Any]:
    """Analyze a fixed two-model weighted ensemble on VALIDATION only."""
    if any(row.split == "LOCKED_TEST" for row in rows):
        raise AnalysisPipelineError("locked-test rows cannot drive ensemble analysis")
    if len(weights) != 2:
        raise AnalysisPipelineError("exactly two ensemble weights are required")
    try:
        diversity = compare_model_predictions(
            rows,
            left_model=left_model,
            right_model=right_model,
            split="VALIDATION",
        )
    except ValueError as exc:
        raise AnalysisPipelineError(str(exc)) from exc
    selected = [row for row in rows if row.split == "VALIDATION"]
    left = {row.normalized_variant_id: row for row in selected if row.model_id == left_model}
    right = {row.normalized_variant_id: row for row in selected if row.model_id == right_model}
    common_ids = sorted(set(left) & set(right))
    if not common_ids:
        raise AnalysisPipelineError("ensemble has no common validation IDs")
    scores = [
        weighted_mean(
            [left[identity].score, right[identity].score],
            list(weights),
        )
        for identity in common_ids
    ]
    raw_labels = [left[identity].label for identity in common_ids]
    if any(label is None for label in raw_labels):
        raise AnalysisPipelineError("ensemble validation rows require labels")
    labels = [label for label in raw_labels if label is not None]
    logits = [
        math.log(max(score, 1e-15) / max(1.0 - score, 1e-15))
        for score in scores
    ]
    return {
        "status": "COMPLETED",
        "phase": 11,
        "family": "ENS_CAL_ABS",
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "models": [left_model, right_model],
        "weights": list(weights),
        "diversity": diversity.to_dict(),
        "metrics": _probability_metrics(scores, labels),
        "calibration": {
            "ece": compute_ece(scores, labels)[0],
            "risk_coverage": compute_risk_coverage_curve(logits, labels).to_dict(),
            "abstention": compute_abstention_analysis(logits, labels).to_dict(),
        },
    }


def write_analysis_artifact(path: str | Path, artifact: dict[str, Any]) -> Path:
    """Write a local analysis artifact without silently replacing an existing run."""
    target = Path(path)
    if target.exists():
        raise AnalysisPipelineError(f"analysis artifact already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(artifact, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target

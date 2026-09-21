"""Fail-closed, one-shot locked-test evaluation contract."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from evovariant_tr.analysis_pipeline import (
    AnalysisPipelineError,
    load_prediction_rows,
    write_analysis_artifact,
)
from evovariant_tr.analysis_plans import freeze_analysis_config, require_frozen_config
from evovariant_tr.benchmark import harmonize_score
from evovariant_tr.metrics import bootstrap_auc_ci, compute_auc_pr, compute_auc_roc


class FinalEvaluationError(ValueError):
    """Raised when a locked evaluation is not provably frozen and reporting-only."""


def evaluate_locked_once(
    predictions_path: str | Path,
    output_path: str | Path,
    *,
    model_id: str,
    frozen_config: dict[str, Any],
    expected_config_sha256: str,
) -> dict[str, Any]:
    """Evaluate exactly one frozen model/configuration on LOCKED_TEST rows.

    This function deliberately has no selection mode.  The caller must provide a
    configuration whose ``selection_closed`` field is true and whose content hash is
    already frozen.  It refuses to overwrite a prior output.
    """
    try:
        frozen = freeze_analysis_config(frozen_config)
        require_frozen_config(frozen, expected_sha256=expected_config_sha256)
    except ValueError as exc:
        raise FinalEvaluationError(str(exc)) from exc
    if frozen_config.get("selection_closed") is not True:
        raise FinalEvaluationError("final evaluation requires selection_closed=true")
    try:
        threshold = float(frozen_config["score_threshold"])
        direction = str(frozen_config["score_direction"])
        bootstrap_replicates = int(frozen_config.get("bootstrap_replicates", 1000))
    except (KeyError, TypeError, ValueError) as exc:
        raise FinalEvaluationError(
            "frozen config requires score_direction and numeric score_threshold"
        ) from exc
    if not math.isfinite(threshold) or bootstrap_replicates < 1:
        raise FinalEvaluationError("final evaluation threshold and bootstrap count must be valid")
    try:
        rows = load_prediction_rows(predictions_path, allow_locked_test=True)
    except AnalysisPipelineError as exc:
        raise FinalEvaluationError(str(exc)) from exc
    selected = [row for row in rows if row.model_id == model_id]
    if not selected or any(row.split != "LOCKED_TEST" for row in selected):
        raise FinalEvaluationError("final evaluation requires only LOCKED_TEST rows for one model")
    if any(row.label is None for row in selected):
        raise FinalEvaluationError("locked-test rows require labels for reporting")
    labels = [row.label for row in selected if row.label is not None]
    raw_scores = [row.score for row in selected]
    scores = [harmonize_score(score, direction) for score in raw_scores]
    if len(set(labels)) != 2:
        raise FinalEvaluationError("locked-test evaluation requires both classes")
    predictions = [int(score >= threshold) for score in scores]
    positive = sum(labels)
    negative = len(labels) - positive
    tp = sum(pred == 1 and label == 1 for pred, label in zip(predictions, labels, strict=True))
    tn = sum(pred == 0 and label == 0 for pred, label in zip(predictions, labels, strict=True))
    fp = negative - tn
    fn = positive - tp
    auc_mean, auc_std, auc_ci = bootstrap_auc_ci(
        scores,
        labels,
        n_bootstrap=bootstrap_replicates,
    )
    artifact = {
        "status": "COMPLETED",
        "phase": 14,
        "family": "STAT",
        "model_id": model_id,
        "selection_split": "LOCKED_TEST",
        "locked_test_evaluated": True,
        "selection_closed": True,
        "config_sha256": frozen.sha256,
        "record_count": len(selected),
        "metrics": {
            "auroc": compute_auc_roc(scores, labels),
            "auprc": compute_auc_pr(scores, labels),
            "accuracy": (tp + tn) / len(labels),
            "sensitivity": tp / positive if positive else 0.0,
            "specificity": tn / negative if negative else 0.0,
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "f1": 2.0 * tp / (2.0 * tp + fp + fn) if 2.0 * tp + fp + fn else 0.0,
            "threshold": threshold,
            "n_positive": positive,
            "n_negative": negative,
            "bootstrap_auc_mean": auc_mean,
            "bootstrap_auc_std": auc_std,
            "bootstrap_auc_ci": list(auc_ci),
            "bootstrap_replicates": bootstrap_replicates,
        },
        "provenance": {
            "predictions_path": str(predictions_path),
            "score_direction": direction,
            "post_test_tuning_allowed": False,
        },
    }
    try:
        write_analysis_artifact(output_path, artifact)
    except AnalysisPipelineError as exc:
        raise FinalEvaluationError(str(exc)) from exc
    return artifact


def load_frozen_config(path: str | Path) -> dict[str, Any]:
    """Read a JSON frozen evaluation configuration."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalEvaluationError(f"could not read frozen config: {exc}") from exc
    if not isinstance(raw, dict):
        raise FinalEvaluationError("frozen evaluation config must be a JSON object")
    return raw

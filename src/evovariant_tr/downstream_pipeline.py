"""Artifact-driven local training and validation for frozen Phase 7 features.

The module deliberately accepts only content-validated JSONL feature artifacts.  It never
opens a locked-test label file, never calls a model endpoint, and never selects a
configuration from test performance.  Real Phase 8/9 work can therefore reuse the same
code after an approved Phase 7 extraction has produced development features.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from evovariant_tr.feature_store import make_feature_record
from evovariant_tr.hpo import ValidationOnlyStudy, run_validation_only_study, write_study
from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc, compute_ece
from evovariant_tr.supervised import (
    LogisticModel,
    MLPModel,
    StumpModel,
    TrainingRow,
    fit_decision_stump,
    fit_logistic_regression,
    fit_mlp,
    validate_training_rows,
)


class DownstreamPipelineError(ValueError):
    """Raised when a feature artifact cannot support a leakage-safe run."""


class ProbabilityModel(Protocol):
    """Minimal prediction contract shared by the local classifier primitives."""

    def predict_proba(self, features: tuple[float, ...] | list[float]) -> float:
        ...


Model = LogisticModel | StumpModel | MLPModel


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_training_feature_rows(
    path: str | Path,
    *,
    model_id: str | None = None,
    layer: str | None = None,
) -> tuple[list[TrainingRow], list[TrainingRow], dict[str, Any]]:
    """Load TRAIN/VALIDATION rows and verify every stored feature hash.

    A feature JSONL file may contain only development rows for a training run.  A
    `LOCKED_TEST` row is rejected rather than silently filtered, because its presence is
    evidence that the upstream extraction boundary was not respected.
    """
    target = Path(path)
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DownstreamPipelineError(f"could not read feature artifact {target}: {exc}") from exc
    train: list[TrainingRow] = []
    validation: list[TrainingRow] = []
    identities: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} is not valid JSON"
            ) from exc
        if not isinstance(raw, dict):
            raise DownstreamPipelineError(f"feature artifact line {line_number} is not an object")
        split = raw.get("split")
        if split == "LOCKED_TEST":
            raise DownstreamPipelineError("locked-test features cannot enter downstream training")
        if split not in {"TRAIN", "VALIDATION"}:
            raise DownstreamPipelineError(f"unsupported training feature split: {split!r}")
        try:
            normalized_id = str(raw["normalized_variant_id"])
            row_model_id = str(raw["model_id"])
            row_layer = str(raw["layer"])
            values_raw = raw["values"]
            label_raw = raw["label"]
            gene_symbol = str(raw["gene_symbol"])
            recorded_hash = str(raw["content_sha256"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} is missing training metadata"
            ) from exc
        if not normalized_id or not row_model_id or not row_layer or not gene_symbol.strip():
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} has empty identity or gene metadata"
            )
        if model_id is not None and row_model_id != model_id:
            raise DownstreamPipelineError(
                f"feature artifact model mismatch: expected {model_id!r}, got {row_model_id!r}"
            )
        if layer is not None and row_layer != layer:
            raise DownstreamPipelineError(
                f"feature artifact layer mismatch: expected {layer!r}, got {row_layer!r}"
            )
        if normalized_id in seen_ids:
            raise DownstreamPipelineError(
                f"feature artifact contains duplicate normalized ID {normalized_id!r}"
            )
        seen_ids.add(normalized_id)
        if not isinstance(values_raw, list) or not values_raw:
            raise DownstreamPipelineError(f"feature artifact line {line_number} has no values")
        try:
            values = [float(value) for value in values_raw]
            label = int(label_raw)
        except (TypeError, ValueError) as exc:
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} has non-numeric values or label"
            ) from exc
        if label not in {0, 1} or not all(math.isfinite(value) for value in values):
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} has invalid label or non-finite values"
            )
        record = make_feature_record(
            normalized_variant_id=normalized_id,
            model_id=row_model_id,
            layer=row_layer,
            split=str(split),
            values=values,
            dtype=str(raw.get("dtype", "float32")),
            gene_symbol=gene_symbol,
        )
        if record.content_sha256 != recorded_hash:
            raise DownstreamPipelineError(
                f"feature artifact line {line_number} content hash does not match values"
            )
        identities.add((row_model_id, row_layer))
        training_row = TrainingRow(
            normalized_variant_id=normalized_id,
            split=str(split),
            label=label,
            features=record.values,
            gene_symbol=gene_symbol,
        )
        (train if split == "TRAIN" else validation).append(training_row)
    if not train or not validation:
        raise DownstreamPipelineError("both TRAIN and VALIDATION feature rows are required")
    if len(identities) != 1:
        raise DownstreamPipelineError("feature artifact mixes model or layer identities")
    validate_training_rows(train, validation, require_gene_grouping=True)
    metadata = {
        "feature_artifact": str(target),
        "feature_artifact_sha256": _sha256_file(target),
        "model_id": next(iter(identities))[0],
        "layer": next(iter(identities))[1],
        "train_count": len(train),
        "validation_count": len(validation),
        "locked_test_evaluated": False,
    }
    return train, validation, metadata


def _metric_panel(scores: Sequence[float], labels: Sequence[int]) -> dict[str, float | int]:
    if len(scores) != len(labels) or not scores:
        raise DownstreamPipelineError("scores and labels must be non-empty and aligned")
    if set(labels) != {0, 1}:
        raise DownstreamPipelineError("validation metrics require both classes")
    probabilities = [float(score) for score in scores]
    if any(not math.isfinite(score) or score < 0.0 or score > 1.0 for score in probabilities):
        raise DownstreamPipelineError("classifier probabilities must be finite and in [0, 1]")
    predictions = [int(score >= 0.5) for score in probabilities]
    positives = sum(labels)
    negatives = len(labels) - positives
    true_positive = sum(
        pred == 1 and label == 1
        for pred, label in zip(predictions, labels, strict=True)
    )
    true_negative = sum(
        pred == 0 and label == 0
        for pred, label in zip(predictions, labels, strict=True)
    )
    false_positive = negatives - true_negative
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = true_positive / positives if positives else 0.0
    specificity = true_negative / negatives if negatives else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    brier = sum(
        (score - label) ** 2
        for score, label in zip(probabilities, labels, strict=True)
    ) / len(labels)
    epsilon = 1e-15
    nll = -sum(
        label * math.log(max(score, epsilon))
        + (1 - label) * math.log(max(1.0 - score, epsilon))
        for score, label in zip(probabilities, labels, strict=True)
    ) / len(labels)
    ece, max_gap = compute_ece(probabilities, list(labels), n_bins=10)
    return {
        "auroc": compute_auc_roc(probabilities, list(labels)),
        "auprc": compute_auc_pr(probabilities, list(labels)),
        "accuracy": (true_positive + true_negative) / len(labels),
        "balanced_accuracy": (recall + specificity) / 2.0,
        "precision": precision,
        "sensitivity": recall,
        "specificity": specificity,
        "f1": f1,
        "brier": brier,
        "nll": nll,
        "ece": ece,
        "max_calibration_gap": max_gap,
        "n": len(labels),
        "n_positive": positives,
        "n_negative": negatives,
    }


def evaluate_classifier(model: ProbabilityModel, rows: Sequence[TrainingRow]) -> dict[str, Any]:
    """Evaluate a classifier on a development split only."""
    scores = [float(model.predict_proba(row.features)) for row in rows]
    labels = [row.label for row in rows]
    return _metric_panel(scores, labels)


def _model_parameters(model: Model) -> dict[str, Any]:
    if isinstance(model, LogisticModel):
        return {
            "kind": "logistic_regression",
            "weights": list(model.weights),
            "bias": model.bias,
            "seed": model.seed,
            "steps": model.steps,
        }
    if isinstance(model, StumpModel):
        return {
            "kind": "decision_stump",
            "feature_index": model.feature_index,
            "threshold": model.threshold,
            "positive_if_greater": model.positive_if_greater,
        }
    return {
        "kind": "mlp",
        "hidden_weights": [list(row) for row in model.hidden_weights],
        "hidden_bias": list(model.hidden_bias),
        "output_weights": list(model.output_weights),
        "output_bias": model.output_bias,
    }


def _prediction_rows(
    models: Mapping[str, ProbabilityModel],
    rows: Sequence[TrainingRow],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for model_name, model in sorted(models.items()):
        for row in rows:
            output.append(
                {
                    "normalized_variant_id": row.normalized_variant_id,
                    "split": row.split,
                    "model_id": model_name,
                    "score": float(model.predict_proba(row.features)),
                    "label": row.label,
                    "gene_symbol": row.gene_symbol,
                }
            )
    return output


def run_baseline_training(
    feature_path: str | Path,
    output_dir: str | Path,
    *,
    model_id: str | None = None,
    layer: str | None = None,
    seed: int = 42,
    mlp_epochs: int = 100,
) -> dict[str, Any]:
    """Fit logistic, stump, and MLP baselines on TRAIN and report VALIDATION only."""
    if mlp_epochs < 1:
        raise DownstreamPipelineError("mlp_epochs must be positive")
    train, validation, metadata = load_training_feature_rows(
        feature_path,
        model_id=model_id,
        layer=layer,
    )
    models: dict[str, Model] = {
        "logistic_regression": fit_logistic_regression(train, seed=seed),
        "decision_stump": fit_decision_stump(train),
        "mlp": fit_mlp(train, seed=seed, epochs=mlp_epochs),
    }
    metrics = {
        name: evaluate_classifier(model, validation)
        for name, model in sorted(models.items())
    }
    root = Path(output_dir)
    summary_path = root / "training_summary.json"
    predictions_path = root / "development_predictions.jsonl"
    if summary_path.exists() or predictions_path.exists():
        raise DownstreamPipelineError("training output directory already contains artifacts")
    predictions = _prediction_rows(models, [*train, *validation])
    _atomic_text(
        predictions_path,
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in predictions),
    )
    summary = {
        "status": "COMPLETED",
        "phase": 8,
        "family": "CLF",
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "seed": seed,
        "models": {
            name: {"parameters": _model_parameters(model), "validation_metrics": metrics[name]}
            for name, model in sorted(models.items())
        },
        "inputs": metadata,
        "artifacts": {
            "development_predictions": str(predictions_path),
        },
    }
    _atomic_json(summary_path, summary)
    return summary


def run_logistic_hpo_from_features(
    feature_path: str | Path,
    output_dir: str | Path,
    configs: list[dict[str, Any]],
    *,
    model_id: str | None = None,
    layer: str | None = None,
    seed: int = 42,
) -> ValidationOnlyStudy:
    """Run a bounded logistic study whose objective reads VALIDATION only."""
    train, validation, metadata = load_training_feature_rows(
        feature_path,
        model_id=model_id,
        layer=layer,
    )

    def objective(config: dict[str, Any]) -> float:
        allowed = {"learning_rate", "steps", "l2"}
        if set(config) - allowed:
            raise DownstreamPipelineError("HPO config contains an unsupported logistic parameter")
        model = fit_logistic_regression(train, seed=seed, **config)
        return float(evaluate_classifier(model, validation)["auroc"])

    study = run_validation_only_study(
        study_name="evovariant_tr_logistic_validation_only",
        configs=configs,
        objective=objective,
        seed=seed,
    )
    root = Path(output_dir)
    if (root / "hpo.json").exists():
        raise DownstreamPipelineError("HPO output already exists")
    root.mkdir(parents=True, exist_ok=True)
    write_study(root / "hpo.json", study)
    _atomic_json(
        root / "hpo_metadata.json",
        {
            "status": "COMPLETED",
            "phase": 9,
            "family": "HPO",
            "selection_split": "VALIDATION",
            "locked_test_evaluated": False,
            "inputs": metadata,
            "search_space": configs,
            "best_trial": study.best_trial.to_dict(),
        },
    )
    return study


def load_hpo_configs(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON list of bounded HPO configurations."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DownstreamPipelineError(f"could not read HPO configs: {exc}") from exc
    if not isinstance(raw, list) or not raw or not all(isinstance(item, dict) for item in raw):
        raise DownstreamPipelineError("HPO configs must be a non-empty JSON object list")
    return [dict(item) for item in raw]

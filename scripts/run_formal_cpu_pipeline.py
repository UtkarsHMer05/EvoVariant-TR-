#!/usr/bin/env python3
"""Run the formal development-only Phase 8--13 CPU continuation.

The runner consumes only hash-checked TRAIN/VALIDATION artifacts.  It keeps the
scientific surface small: one feature loader, the existing deterministic
classifiers/metrics, and one append-only result tree.  No locked-test file is
opened and no network or Modal call is made.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evovariant_tr.abstention import compute_abstention_analysis, compute_risk_coverage_curve
from evovariant_tr.analysis_plans import freeze_analysis_config
from evovariant_tr.downstream_pipeline import load_hpo_configs, load_training_feature_rows
from evovariant_tr.ensemble import PredictionRow, compare_model_predictions, stack_feature_matrix
from evovariant_tr.hpo import run_validation_only_study, write_study
from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc, compute_ece
from evovariant_tr.prediction_calibration import (
    apply_isotonic,
    apply_platt,
    fit_isotonic,
    fit_platt,
    probability_metrics,
)
from evovariant_tr.supervised import (
    LogisticModel,
    MLPModel,
    StumpModel,
    TrainingRow,
    fit_logistic_regression,
    fit_mlp,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
SEED = 42
BOOTSTRAP_REPLICATES = 200

FEATURE_ROOT = REPO_ROOT / "research/runs/phase8_formal_features_20260922"
EVO2 = REPO_ROOT / "research/runs/phase13_formal_evo2_20260922/combined_evo2_features_v2.jsonl"
NT_DIR = FEATURE_ROOT / "nucleotide_transformer"
CAD_DIR = FEATURE_ROOT / "caduceus"
FOUNDATION = FEATURE_ROOT / "foundation_fusion.jsonl"
ALL_FUSION = FEATURE_ROOT / "all_fusion.jsonl"
CADD = REPO_ROOT / (
    "artifacts/phase6a/comparators/formal_budgeted_20260921/cadd_grch38_v1.7_20260921.json"
)
PHYLOP = REPO_ROOT / (
    "artifacts/phase6a/comparators/formal_budgeted_20260921/phylop100way_hg38_20260921.json"
)


@dataclass
class FeatureSet:
    name: str
    rows: list[TrainingRow]
    feature_names: list[str]
    source: dict[str, Any]

    @property
    def train(self) -> list[TrainingRow]:
        return [row for row in self.rows if row.split == "TRAIN"]

    @property
    def validation(self) -> list[TrainingRow]:
        return [row for row in self.rows if row.split == "VALIDATION"]


@dataclass
class FitResult:
    key: str
    feature_set: FeatureSet
    classifier: str
    params: dict[str, Any]
    model: LogisticModel | StumpModel | MLPModel
    train_scores: list[float]
    validation_scores: list[float]
    train_metrics: dict[str, Any]
    validation_metrics: dict[str, Any]
    runtime_seconds: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
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


def atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_manifest() -> dict[str, dict[str, Any]]:
    if sha256_file(MANIFEST) != MANIFEST_SHA256:
        raise ValueError("formal development manifest hash changed")
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if document.get("record_set_sha256") != RECORD_SET_SHA256:
        raise ValueError("formal record-set hash changed")
    records = document.get("records")
    if not isinstance(records, list) or len(records) != 4000:
        raise ValueError("formal development manifest must contain 4,000 rows")
    result: dict[str, dict[str, Any]] = {}
    for record in sorted(records, key=lambda row: str(row["normalized_variant_id"])):
        identity = str(record["normalized_variant_id"])
        if record.get("split") not in {"TRAIN", "VALIDATION"}:
            raise ValueError("development manifest contains a non-development split")
        if identity in result:
            raise ValueError(f"duplicate manifest ID: {identity}")
        result[identity] = record
    if len(result) != 4000:
        raise ValueError("formal manifest contains duplicate IDs")
    return result


def load_feature(path: Path, name: str) -> FeatureSet:
    train, validation, metadata = load_training_feature_rows(path)
    rows = sorted([*train, *validation], key=lambda row: row.normalized_variant_id)
    if len(rows) != len({row.normalized_variant_id for row in rows}):
        raise ValueError(f"duplicate IDs in feature set {name}")
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    width = len(rows[0].features)
    feature_names = [str(value) for value in first.get("feature_names", [])]
    if len(feature_names) != width:
        feature_names = [f"{name}[{index}]" for index in range(width)]
    return FeatureSet(
        name=name,
        rows=rows,
        feature_names=feature_names,
        source={
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(path),
            "metadata": metadata,
        },
    )


def load_comparator(
    path: Path,
    name: str,
    value_key: str,
    manifest: dict[str, dict[str, Any]],
) -> FeatureSet:
    document = json.loads(path.read_text(encoding="utf-8"))
    values: dict[str, float] = {}
    for raw in document.get("rows", []):
        identity = str(raw["normalized_variant_id"])
        value = raw.get(value_key)
        if raw.get("status") != "AVAILABLE" or value is None:
            continue
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"non-finite {name} value for {identity}")
        if identity in values:
            raise ValueError(f"duplicate {name} ID {identity}")
        values[identity] = numeric
    rows = [
        TrainingRow(
            normalized_variant_id=identity,
            split=str(manifest[identity]["split"]),
            label=int(manifest[identity]["label"]),
            features=(values[identity],),
            gene_symbol=str(manifest[identity]["gene_symbol"]),
        )
        for identity in sorted(values)
        if identity in manifest
    ]
    if not rows:
        raise ValueError(f"{name} has no development coverage")
    return FeatureSet(
        name=name,
        rows=rows,
        feature_names=[name],
        source={
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(path),
            "value_key": value_key,
            "available_development_rows": len(rows),
        },
    )


def derive(source: FeatureSet, name: str, indices: list[int], labels: list[str]) -> FeatureSet:
    if len(indices) != len(labels) or not indices:
        raise ValueError("derived feature indices and names must be non-empty and aligned")
    return FeatureSet(
        name=name,
        rows=[
            TrainingRow(
                row.normalized_variant_id,
                row.split,
                row.label,
                tuple(row.features[index] for index in indices),
                row.gene_symbol,
            )
            for row in source.rows
        ],
        feature_names=labels,
        source={
            "derived_from": source.name,
            "source": source.source,
            "indices": indices,
        },
    )


def join_sets(left: FeatureSet, right: FeatureSet, name: str) -> FeatureSet:
    right_by_id = {row.normalized_variant_id: row for row in right.rows}
    rows: list[TrainingRow] = []
    for row in left.rows:
        other = right_by_id.get(row.normalized_variant_id)
        if other is None:
            continue
        if (row.split, row.label, row.gene_symbol) != (
            other.split,
            other.label,
            other.gene_symbol,
        ):
            raise ValueError(f"metadata mismatch while joining {left.name} and {right.name}")
        rows.append(
            TrainingRow(
                row.normalized_variant_id,
                row.split,
                row.label,
                row.features + other.features,
                row.gene_symbol,
            )
        )
    if not rows:
        raise ValueError(f"no common rows while joining {left.name} and {right.name}")
    return FeatureSet(
        name=name,
        rows=rows,
        feature_names=left.feature_names + right.feature_names,
        source={"left": left.source, "right": right.source},
    )


def fit_fast_stump(rows: list[TrainingRow]) -> StumpModel:
    """Exact stump search in O(features * rows log rows), not O(rows squared)."""
    if not rows or {row.label for row in rows} != {0, 1}:
        raise ValueError("stump training requires non-empty binary rows")
    width = len(rows[0].features)
    best: tuple[int, int, float, int] | None = None
    for feature_index in range(width):
        grouped: dict[float, list[int]] = {}
        for row in rows:
            grouped.setdefault(row.features[feature_index], []).append(row.label)
        total_positive = sum(row.label for row in rows)
        total_negative = len(rows) - total_positive
        before_positive = before_negative = 0
        for threshold in sorted(grouped):
            # >= threshold predicts positive; < threshold predicts positive.
            candidates = (
                (before_positive + total_negative - before_negative, 1),
                (before_negative + total_positive - before_positive, 0),
            )
            for errors, positive_flag in candidates:
                candidate = (errors, feature_index, threshold, positive_flag)
                if best is None or candidate < best:
                    best = candidate
            labels = grouped[threshold]
            before_positive += sum(labels)
            before_negative += len(labels) - sum(labels)
    assert best is not None
    _, feature_index, threshold, positive_flag = best
    return StumpModel(feature_index, threshold, bool(positive_flag))


def fit_model(
    classifier: str,
    rows: list[TrainingRow],
    *,
    params: dict[str, Any] | None = None,
    seed: int = SEED,
) -> LogisticModel | StumpModel | MLPModel:
    options = dict(params or {})
    if classifier == "logistic_regression":
        return fit_logistic_regression(rows, seed=seed, **options)
    if classifier == "decision_stump":
        return fit_fast_stump(rows)
    if classifier == "mlp":
        return fit_mlp(rows, seed=seed, **options)
    raise ValueError(f"unknown classifier {classifier}")


def metric_panel(scores: list[float], labels: list[int]) -> dict[str, Any]:
    if len(scores) != len(labels) or not scores or set(labels) != {0, 1}:
        raise ValueError("metrics require aligned non-empty scores and both classes")
    if any(not math.isfinite(score) or not 0.0 <= score <= 1.0 for score in scores):
        raise ValueError("classifier scores must be finite probabilities")
    predicted = [int(score >= 0.5) for score in scores]
    positive = sum(labels)
    negative = len(labels) - positive
    tp = sum(pred == 1 and label == 1 for pred, label in zip(predicted, labels, strict=True))
    tn = sum(pred == 0 and label == 0 for pred, label in zip(predicted, labels, strict=True))
    fp = negative - tn
    fn = positive - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / positive if positive else 0.0
    specificity = tn / negative if negative else 0.0
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denominator if denominator else 0.0
    brier = sum((score - label) ** 2 for score, label in zip(scores, labels, strict=True)) / len(
        scores
    )
    epsilon = 1e-15
    nll = -sum(
        label * math.log(max(score, epsilon)) + (1 - label) * math.log(max(1.0 - score, epsilon))
        for score, label in zip(scores, labels, strict=True)
    ) / len(scores)
    ece, max_gap = compute_ece(scores, labels, n_bins=10)
    return {
        "auroc": compute_auc_roc(scores, labels),
        "auprc": compute_auc_pr(scores, labels),
        "mcc": mcc,
        "balanced_accuracy": (recall + specificity) / 2.0,
        "accuracy": (tp + tn) / len(labels),
        "precision": precision,
        "sensitivity": recall,
        "recall": recall,
        "specificity": specificity,
        "f1": 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "brier": brier,
        "nll": nll,
        "ece": ece,
        "max_calibration_gap": max_gap,
        "n": len(labels),
        "n_positive": positive,
        "n_negative": negative,
        "coverage": 1.0,
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def grouped_auc_ci(
    rows: list[TrainingRow], scores: list[float], seed: int = SEED
) -> dict[str, Any]:
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(str(row.gene_symbol), []).append(index)
    names = sorted(groups)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = [names[rng.randrange(len(names))] for _ in names]
        indices = [index for name in sampled for index in groups[name]]
        sampled_labels = [rows[index].label for index in indices]
        if set(sampled_labels) != {0, 1}:
            continue
        values.append(compute_auc_roc([scores[index] for index in indices], sampled_labels))
    if not values:
        return {"replicates": 0, "ci95_low": None, "ci95_high": None}
    values.sort()
    return {
        "replicates": len(values),
        "ci95_low": values[max(0, int(0.025 * (len(values) - 1)))],
        "ci95_high": values[min(len(values) - 1, int(0.975 * (len(values) - 1)))],
    }


def fit_result(
    feature_set: FeatureSet,
    classifier: str,
    *,
    params: dict[str, Any] | None = None,
    seed: int = SEED,
    include_ci: bool = True,
) -> FitResult:
    started = time.perf_counter()
    model = fit_model(classifier, feature_set.train, params=params, seed=seed)
    train_scores = [float(model.predict_proba(row.features)) for row in feature_set.train]
    validation_scores = [float(model.predict_proba(row.features)) for row in feature_set.validation]
    train_metrics = metric_panel(train_scores, [row.label for row in feature_set.train])
    validation_metrics = metric_panel(
        validation_scores, [row.label for row in feature_set.validation]
    )
    if include_ci:
        validation_metrics["auroc_gene_clustered_ci95"] = grouped_auc_ci(
            feature_set.validation, validation_scores
        )
    return FitResult(
        key=f"{feature_set.name}__{classifier}",
        feature_set=feature_set,
        classifier=classifier,
        params=dict(params or {}),
        model=model,
        train_scores=train_scores,
        validation_scores=validation_scores,
        train_metrics=train_metrics,
        validation_metrics=validation_metrics,
        runtime_seconds=time.perf_counter() - started,
    )


def result_record(result: FitResult) -> dict[str, Any]:
    return {
        "model_id": result.key,
        "feature_set": result.feature_set.name,
        "classifier": result.classifier,
        "parameters": result.params,
        "train_count": len(result.feature_set.train),
        "validation_count": len(result.feature_set.validation),
        "feature_dimension": len(result.feature_set.feature_names),
        "feature_names": result.feature_set.feature_names,
        "train_metrics": result.train_metrics,
        "validation_metrics": result.validation_metrics,
        "runtime_seconds": result.runtime_seconds,
        "source": result.feature_set.source,
    }


def prediction_rows(results: list[FitResult]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for result in sorted(results, key=lambda item: item.key):
        for row, score in zip(
            [*result.feature_set.train, *result.feature_set.validation],
            [*result.train_scores, *result.validation_scores],
            strict=True,
        ):
            output.append(
                {
                    "normalized_variant_id": row.normalized_variant_id,
                    "split": row.split,
                    "model_id": result.key,
                    "score": score,
                    "label": row.label,
                    "gene_symbol": row.gene_symbol,
                    "locked_test_evaluated": False,
                }
            )
    return output


def by_id(rows: list[TrainingRow]) -> dict[str, TrainingRow]:
    return {row.normalized_variant_id: row for row in rows}


def ensemble_scores(
    results: list[FitResult], split: str, weights: list[float]
) -> tuple[list[str], list[float], list[int]]:
    if not results or len(results) != len(weights):
        raise ValueError("ensemble results and weights are not aligned")
    maps = []
    for result in results:
        source = result.feature_set.train if split == "TRAIN" else result.feature_set.validation
        scores = result.train_scores if split == "TRAIN" else result.validation_scores
        maps.append(
            {
                row.normalized_variant_id: (score, row.label)
                for row, score in zip(source, scores, strict=True)
            }
        )
    common = sorted(set.intersection(*(set(values) for values in maps)))
    if not common:
        raise ValueError("ensemble has no common IDs")
    total = sum(weights)
    if total <= 0:
        raise ValueError("ensemble weights must be positive")
    scores = [
        sum(maps[index][identity][0] * weights[index] for index in range(len(maps))) / total
        for identity in common
    ]
    labels = [maps[0][identity][1] for identity in common]
    return common, scores, labels


def kappa(left: list[int], right: list[int]) -> float | None:
    if not left or len(left) != len(right):
        return None
    observed = sum(a == b for a, b in zip(left, right, strict=True)) / len(left)
    p_left = sum(left) / len(left)
    p_right = sum(right) / len(right)
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    return (observed - expected) / (1 - expected) if expected < 1 else None


def reliability(scores: list[float], labels: list[int]) -> list[dict[str, float | int]]:
    points: list[dict[str, float | int]] = []
    for bin_index in range(10):
        lower = bin_index / 10
        upper = (bin_index + 1) / 10
        indices = [
            index
            for index, score in enumerate(scores)
            if lower <= score < upper or (bin_index == 9 and score == upper)
        ]
        if indices:
            points.append(
                {
                    "bin": bin_index,
                    "count": len(indices),
                    "confidence": sum(scores[index] for index in indices) / len(indices),
                    "observed_frequency": sum(labels[index] for index in indices) / len(indices),
                }
            )
    return points


def build_features(
    manifest: dict[str, dict[str, Any]],
) -> tuple[dict[str, FeatureSet], dict[str, FeatureSet]]:
    base: dict[str, FeatureSet] = {"evo2": load_feature(EVO2, "evo2")}
    for layer in (8, 16, 24):
        path = NT_DIR / f"nucleotide_transformer_layer_{layer}_scalar_summary.jsonl"
        base[f"nt{layer}"] = load_feature(path, f"nt{layer}")
    for layer in (4, 8, 16):
        path = CAD_DIR / f"caduceus_layer_{layer}_scalar_summary.jsonl"
        base[f"cad{layer}"] = load_feature(path, f"cad{layer}")
    base["cadd"] = load_comparator(CADD, "cadd", "raw_score", manifest)
    base["phylop"] = load_comparator(PHYLOP, "phylop", "sitewise_score", manifest)
    base["foundation_fusion"] = load_feature(FOUNDATION, "foundation_fusion")
    base["all_fusion"] = load_feature(ALL_FUSION, "all_fusion")
    base["cadd_phylop"] = join_sets(base["cadd"], base["phylop"], "cadd_phylop")

    ablations: dict[str, FeatureSet] = {
        "evo2_forward": derive(base["evo2"], "evo2_forward", [1], ["evo2_forward"]),
        "evo2_reverse": derive(base["evo2"], "evo2_reverse", [2], ["evo2_reverse"]),
        "evo2_aggregate": derive(base["evo2"], "evo2_aggregate", [0], ["evo2_aggregate"]),
        "evo2_without_orientation": derive(
            base["evo2"], "evo2_without_orientation", [0, 1, 2], ["evo2[0]", "evo2[1]", "evo2[2]"]
        ),
    }
    for family in ("nt8", "nt16", "nt24", "cad4", "cad8", "cad16"):
        for index, label in enumerate(("forward", "reverse", "aggregate")):
            ablations[f"{family}_{label}"] = derive(
                base[family], f"{family}_{label}", [index], [label]
            )

    foundation = base["foundation_fusion"]
    for removed, predicate in {
        "evo2": lambda name: name.startswith("evo2["),
        "nt": lambda name: name.startswith("nt"),
        "caduceus": lambda name: name.startswith("cad"),
        "orientation": lambda name: name.endswith("[3]"),
    }.items():
        keep = [index for index, name in enumerate(foundation.feature_names) if not predicate(name)]
        ablations[f"foundation_without_{removed}"] = derive(
            foundation,
            f"foundation_without_{removed}",
            keep,
            [foundation.feature_names[index] for index in keep],
        )
    all_fusion = base["all_fusion"]
    for removed, predicate in {
        "comparators": lambda name: name in {"cadd", "phylop"},
        "evo2": lambda name: name.startswith("evo2["),
        "nt": lambda name: name.startswith("nt"),
        "caduceus": lambda name: name.startswith("cad"),
    }.items():
        keep = [index for index, name in enumerate(all_fusion.feature_names) if not predicate(name)]
        ablations[f"all_without_{removed}"] = derive(
            all_fusion,
            f"all_without_{removed}",
            keep,
            [all_fusion.feature_names[index] for index in keep],
        )
    return base, ablations


def run_hpo(
    feature_sets: list[FeatureSet], root: Path, configs: list[dict[str, Any]]
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for feature_set in feature_sets:

        def objective(config: dict[str, Any], current: FeatureSet = feature_set) -> float:
            result = fit_result(current, "logistic_regression", params=config, include_ci=False)
            return float(result.validation_metrics["auroc"])

        study = run_validation_only_study(
            study_name=f"formal_{feature_set.name}_logistic_validation_only",
            configs=configs,
            objective=objective,
            seed=SEED,
        )
        directory = root / feature_set.name
        write_study(directory / "hpo.json", study)
        metadata = {
            "status": "PASS_FORMAL_VALIDATION_ONLY_HPO",
            "phase": 9,
            "feature_set": feature_set.name,
            "selection_split": "VALIDATION",
            "locked_test_evaluated": False,
            "source": feature_set.source,
            "search_space": configs,
            "best_trial": study.best_trial.to_dict(),
            "study_sha256": sha256_file(directory / "hpo.json"),
        }
        atomic_json(directory / "hpo_metadata.json", metadata)
        output[feature_set.name] = metadata
    best = max(output.values(), key=lambda item: float(item["best_trial"]["validation_metric"]))
    return {
        "status": "PASS_FORMAL_PHASE9",
        "phase": 9,
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "studies": output,
        "best_feature_set": best["feature_set"],
        "best_trial": best["best_trial"],
    }


def run_oof(selected: list[FitResult]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if len(selected) < 2:
        raise ValueError("OOF stacking needs at least two selected base models")
    common_ids = set.intersection(
        *(set(row.normalized_variant_id for row in result.feature_set.rows) for result in selected)
    )
    if not common_ids:
        raise ValueError("selected models have no common IDs for OOF stacking")
    train_rows = [
        row for row in selected[0].feature_set.train if row.normalized_variant_id in common_ids
    ]
    validation_rows = [
        row for row in selected[0].feature_set.validation if row.normalized_variant_id in common_ids
    ]
    gene_folds: dict[str, int] = {
        gene: index % 5
        for index, gene in enumerate(sorted({str(row.gene_symbol) for row in train_rows}))
    }
    oof_by_model: dict[str, dict[str, float]] = {result.key: {} for result in selected}
    for result in selected:
        for fold in range(5):
            fit_rows = [
                row
                for row in result.feature_set.train
                if gene_folds[str(row.gene_symbol)] != fold
                and row.normalized_variant_id in common_ids
            ]
            holdout = [
                row
                for row in result.feature_set.train
                if gene_folds[str(row.gene_symbol)] == fold
                and row.normalized_variant_id in common_ids
            ]
            model = fit_model(result.classifier, fit_rows, params=result.params, seed=SEED)
            for row in holdout:
                oof_by_model[result.key][row.normalized_variant_id] = float(
                    model.predict_proba(row.features)
                )
    order = [result.key for result in selected]
    model_order = sorted(oof_by_model)
    stack_rows = [
        PredictionRow(
            identity,
            "TRAIN",
            key,
            oof_by_model[key][identity],
            next(row.label for row in train_rows if row.normalized_variant_id == identity),
            True,
        )
        for identity in sorted(oof_by_model[model_order[0]])
        for key in model_order
    ]
    ids, matrix, labels = stack_feature_matrix(stack_rows)
    meta_train = [
        TrainingRow(
            identity,
            "TRAIN",
            label,
            tuple(matrix[index]),
            next(row.gene_symbol for row in train_rows if row.normalized_variant_id == identity),
        )
        for index, (identity, label) in enumerate(zip(ids, labels, strict=True))
    ]
    meta = fit_logistic_regression(meta_train, learning_rate=0.1, steps=200, l2=0.01, seed=SEED)
    validation_maps = [
        {
            row.normalized_variant_id: score
            for row, score in zip(
                result.feature_set.validation, result.validation_scores, strict=True
            )
        }
        for result in selected
    ]
    validation_ids = sorted(set.intersection(*(set(values) for values in validation_maps)))
    meta_validation = [
        TrainingRow(
            identity,
            "VALIDATION",
            next(row.label for row in validation_rows if row.normalized_variant_id == identity),
            tuple(values[identity] for values in validation_maps),
            next(
                row.gene_symbol for row in validation_rows if row.normalized_variant_id == identity
            ),
        )
        for identity in validation_ids
    ]
    validation_scores = [float(meta.predict_proba(row.features)) for row in meta_validation]
    metrics = metric_panel(validation_scores, [row.label for row in meta_validation])
    rows = [
        {
            "normalized_variant_id": row.normalized_variant_id,
            "split": row.split,
            "model_id": "oof_stack",
            "score": float(meta.predict_proba(row.features)),
            "label": row.label,
            "gene_symbol": row.gene_symbol,
            "oof": row.split == "TRAIN",
            "locked_test_evaluated": False,
        }
        for row in [*meta_train, *meta_validation]
    ]
    return {
        "model_id": "oof_stack",
        "base_models": order,
        "fold_count": 5,
        "oof_train_count": len(meta_train),
        "validation_count": len(meta_validation),
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "meta_parameters": {"learning_rate": 0.1, "steps": 200, "l2": 0.01, "seed": SEED},
        "validation_metrics": metrics,
    }, rows


def run_phase13(
    ablations: dict[str, FeatureSet],
    final_feature: FeatureSet,
    final_classifier: str,
    final_params: dict[str, Any],
    final_scores: list[float],
    final_rows: list[TrainingRow],
    root: Path,
) -> dict[str, Any]:
    ablation_results: list[dict[str, Any]] = []
    for name, feature_set in sorted(ablations.items()):
        result = fit_result(feature_set, "logistic_regression", include_ci=False)
        ablation_results.append(
            {"ablation": name, "metrics": result.validation_metrics, "source": feature_set.source}
        )

    curve: list[dict[str, Any]] = []
    genes = sorted({str(row.gene_symbol) for row in final_feature.train})
    for fraction in (0.10, 0.25, 0.50, 0.75, 1.00):
        count = max(1, math.ceil(len(genes) * fraction))
        allowed = set(genes[:count])
        subset = [row for row in final_feature.train if str(row.gene_symbol) in allowed]
        if {row.label for row in subset} != {0, 1}:
            curve.append(
                {"fraction": fraction, "status": "SKIPPED_SINGLE_CLASS", "train_count": len(subset)}
            )
            continue
        fitted = fit_model(final_classifier, subset, params=final_params, seed=SEED)
        scores = [float(fitted.predict_proba(row.features)) for row in final_feature.validation]
        curve.append(
            {
                "fraction": fraction,
                "status": "COMPLETED",
                "train_count": len(subset),
                "validation_metrics": metric_panel(
                    scores, [row.label for row in final_feature.validation]
                ),
            }
        )

    seed_robustness: list[dict[str, Any]] = []
    for classifier in ("logistic_regression", "mlp"):
        for seed in (7, 42, 99):
            params = (
                final_params
                if classifier == final_classifier
                else ({"epochs": 100} if classifier == "mlp" else {})
            )
            result = fit_result(
                final_feature, classifier, params=params, seed=seed, include_ci=False
            )
            seed_robustness.append(
                {
                    "model_id": result.key,
                    "seed": seed,
                    "classifier": classifier,
                    "validation_metrics": result.validation_metrics,
                }
            )

    by_gene: dict[str, list[int]] = {}
    for index, row in enumerate(final_rows):
        by_gene.setdefault(str(row.gene_symbol), []).append(index)
    subgroups = []
    labels = [row.label for row in final_rows]
    for gene, indices in sorted(by_gene.items()):
        gene_labels = [labels[index] for index in indices]
        gene_scores = [final_scores[index] for index in indices]
        subgroups.append(
            {
                "subgroup": gene,
                "sample_count": len(indices),
                "positive_count": sum(gene_labels),
                "negative_count": len(indices) - sum(gene_labels),
                "accuracy": sum(
                    (score >= 0.5) == bool(label)
                    for score, label in zip(gene_scores, gene_labels, strict=True)
                )
                / len(indices),
                "auroc": compute_auc_roc(gene_scores, gene_labels)
                if set(gene_labels) == {0, 1}
                else None,
            }
        )

    errors = []
    for row, score in sorted(
        zip(final_rows, final_scores, strict=True),
        key=lambda item: abs(item[1] - item[0].label),
        reverse=True,
    ):
        predicted = int(score >= 0.5)
        if predicted != row.label:
            errors.append(
                {
                    "normalized_variant_id": row.normalized_variant_id,
                    "label": row.label,
                    "score": score,
                    "predicted": predicted,
                    "gene_symbol": row.gene_symbol,
                }
            )
    robustness = {
        "context_length": {
            "status": "NOT_RUN_DEFERRED_BY_COMPUTE",
            "contexts_bp": [512, 1024, 2048, 4096, 8192],
        },
        "center_shift": {
            "status": "NOT_APPLICABLE",
            "reason": "cached features do not retain alternate context windows",
        },
        "minor_preprocessing": {
            "status": "NOT_RUN",
            "reason": "no scientifically approved perturbation was authorized",
        },
    }
    artifact = {
        "status": "PASS_FORMAL_PHASE13",
        "phase": 13,
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "ablation_results": ablation_results,
        "learning_curves": curve,
        "learning_curve_fractions": [0.10, 0.25, 0.50, 0.75, 1.00],
        "seed_robustness": seed_robustness,
        "subgroups": subgroups,
        "error_analysis": {
            "validation_error_count": len(errors),
            "highest_confidence_errors": errors[:25],
        },
        "robustness": robustness,
        "skipped_cells": [
            {
                "cell": "context_length",
                "reason": (
                    "additional foundation-model extraction is outside the current paid "
                    "authorization"
                ),
            },
            {"cell": "center_shift", "reason": "no cached alternate center windows"},
        ],
    }
    atomic_json(root / "ablations_learning_curves_robustness.json", artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=REPO_ROOT / "research/runs/formal_cpu_20260922"
    )
    args = parser.parse_args()
    root = args.output_root.resolve()
    phase8_root = root / "phase8"
    phase9_root = root / "phase9"
    phase11_root = root / "phase11"
    phase12_root = root / "phase12"
    phase13_root = root / "phase13"
    manifest = load_manifest()
    base, ablations = build_features(manifest)

    base_for_benchmark = [
        base[name]
        for name in (
            "evo2",
            "nt8",
            "nt16",
            "nt24",
            "cad4",
            "cad8",
            "cad16",
            "cadd",
            "phylop",
            "cadd_phylop",
            "foundation_fusion",
            "all_fusion",
        )
    ]
    results: list[FitResult] = []
    for feature_set in base_for_benchmark:
        for classifier, params in (
            ("logistic_regression", {}),
            ("decision_stump", {}),
            ("mlp", {"epochs": 100}),
        ):
            results.append(fit_result(feature_set, classifier, params=params))
    best = max(results, key=lambda result: float(result.validation_metrics["auroc"]))
    if float(best.validation_metrics["auroc"]) <= 0.5:
        raise ValueError("formal Phase 8 produced no better-than-random validation model")
    phase8 = {
        "status": "PASS_FORMAL_PHASE8",
        "phase": 8,
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "formal_manifest_sha256": MANIFEST_SHA256,
        "formal_record_set_sha256": RECORD_SET_SHA256,
        "feature_sets": {
            name: {
                "coverage": len(feature_set.rows),
                "train": len(feature_set.train),
                "validation": len(feature_set.validation),
                "feature_names": feature_set.feature_names,
                "source": feature_set.source,
            }
            for name, feature_set in base.items()
        },
        "models": [result_record(result) for result in sorted(results, key=lambda item: item.key)],
        "best_validation_model": best.key,
    }
    atomic_json(phase8_root / "summary.json", phase8)
    atomic_jsonl(phase8_root / "development_predictions.jsonl", prediction_rows(results))

    configs = load_hpo_configs(REPO_ROOT / "experiments/configs/logistic_hpo_search.json")
    phase9 = run_hpo(base_for_benchmark, phase9_root, configs)
    atomic_json(phase9_root / "summary.json", phase9)
    hpo_refits: dict[str, FitResult] = {}
    for feature_set in base_for_benchmark:
        config = phase9["studies"][feature_set.name]["best_trial"]["config"]
        refit = fit_result(
            feature_set,
            "logistic_regression",
            params=config,
            include_ci=False,
        )
        refit.key = f"{feature_set.name}__logistic_regression_hpo"
        hpo_refits[feature_set.name] = refit

    top_by_feature: list[FitResult] = []
    for feature_set in base_for_benchmark:
        candidates = [
            result
            for result in results
            if result.feature_set.name == feature_set.name
            and result.classifier in {"logistic_regression", "mlp"}
        ]
        candidates.append(hpo_refits[feature_set.name])
        top_by_feature.append(
            max(candidates, key=lambda result: float(result.validation_metrics["auroc"]))
        )
    full_coverage_candidates = [
        result for result in top_by_feature if len(result.feature_set.rows) == 4000
    ]
    selected = sorted(
        full_coverage_candidates,
        key=lambda result: (-float(result.validation_metrics["auroc"]), result.key),
    )[:3]
    if len(selected) < 2:
        raise ValueError("formal Phase 11 cannot find two base models")
    diversity: list[dict[str, Any]] = []
    prediction_rows_for_compare: list[PredictionRow] = []
    for result in selected:
        prediction_rows_for_compare.extend(
            PredictionRow(row.normalized_variant_id, row.split, result.key, score, row.label)
            for row, score in zip(
                result.feature_set.validation, result.validation_scores, strict=True
            )
        )
    for left_index, left in enumerate(selected):
        for right in selected[left_index + 1 :]:
            summary = compare_model_predictions(
                prediction_rows_for_compare,
                left_model=left.key,
                right_model=right.key,
                split="VALIDATION",
                positive_threshold=0.5,
            )
            left_map = {
                row.normalized_variant_id: int(score >= 0.5)
                for row, score in zip(
                    left.feature_set.validation, left.validation_scores, strict=True
                )
            }
            right_map = {
                row.normalized_variant_id: int(score >= 0.5)
                for row, score in zip(
                    right.feature_set.validation, right.validation_scores, strict=True
                )
            }
            ids = sorted(set(left_map) & set(right_map))
            diversity.append(
                {
                    **summary.to_dict(),
                    "cohen_kappa": kappa([left_map[i] for i in ids], [right_map[i] for i in ids]),
                }
            )

    _, equal_scores, equal_labels = ensemble_scores(selected, "VALIDATION", [1.0] * len(selected))
    train_auc_weights = [
        max(0.001, float(result.train_metrics["auroc"]) - 0.5) for result in selected
    ]
    _, weighted_scores, weighted_labels = ensemble_scores(selected, "VALIDATION", train_auc_weights)
    common_ids, _, _ = ensemble_scores(selected, "VALIDATION", [1.0] * len(selected))
    validation_maps = [
        {
            row.normalized_variant_id: score
            for row, score in zip(
                result.feature_set.validation, result.validation_scores, strict=True
            )
        }
        for result in selected
    ]
    vote_scores = [
        sum(int(values[identity] >= 0.5) for values in validation_maps) / len(selected)
        for identity in common_ids
    ]
    ensemble = {
        "equal_mean": metric_panel(equal_scores, equal_labels),
        "train_performance_weighted_mean": {
            "weights": train_auc_weights,
            "metrics": metric_panel(weighted_scores, weighted_labels),
        },
        "hard_vote": metric_panel(vote_scores, equal_labels),
    }
    stack, stack_prediction_rows = run_oof(selected)
    phase11 = {
        "status": "PASS_FORMAL_PHASE11",
        "phase": 11,
        "selection_split": "VALIDATION",
        "locked_test_evaluated": False,
        "selected_base_models": [result.key for result in selected],
        "diversity": diversity,
        "ensemble_methods": ensemble,
        "oof_stack": stack,
    }
    atomic_json(phase11_root / "ensemble_analysis.json", phase11)
    atomic_jsonl(phase11_root / "oof_stack_predictions.jsonl", stack_prediction_rows)

    stack_is_final = float(stack["validation_metrics"]["auroc"]) >= max(
        float(result.validation_metrics["auroc"]) for result in selected
    )
    if stack_is_final:
        final_model_id = "oof_stack"
        final_feature = selected[0].feature_set
        final_classifier = "logistic_regression"
        final_params = {"learning_rate": 0.1, "steps": 200, "l2": 0.01}
        final_train_scores = [
            row["score"] for row in stack_prediction_rows if row["split"] == "TRAIN"
        ]
        final_validation_scores = [
            row["score"] for row in stack_prediction_rows if row["split"] == "VALIDATION"
        ]
        final_train_rows = [
            row
            for row in selected[0].feature_set.train
            if row.normalized_variant_id
            in {
                item["normalized_variant_id"]
                for item in stack_prediction_rows
                if item["split"] == "TRAIN"
            }
        ]
        final_validation_rows = [
            row
            for row in selected[0].feature_set.validation
            if row.normalized_variant_id
            in {
                item["normalized_variant_id"]
                for item in stack_prediction_rows
                if item["split"] == "VALIDATION"
            }
        ]
    else:
        final_result = max(selected, key=lambda result: float(result.validation_metrics["auroc"]))
        final_model_id = final_result.key
        final_feature = final_result.feature_set
        final_classifier = final_result.classifier
        final_params = final_result.params
        final_train_scores = final_result.train_scores
        final_validation_scores = final_result.validation_scores
        final_train_rows = final_result.feature_set.train
        final_validation_rows = final_result.feature_set.validation

    train_labels = [row.label for row in final_train_rows]
    validation_labels = [row.label for row in final_validation_rows]
    platt = fit_platt(final_train_scores, train_labels)
    isotonic = fit_isotonic(final_train_scores, train_labels)
    calibrated = {
        "uncalibrated": probability_metrics(final_validation_scores, validation_labels),
        "platt": probability_metrics(
            apply_platt(final_validation_scores, platt), validation_labels
        ),
        "isotonic": probability_metrics(
            apply_isotonic(final_validation_scores, isotonic), validation_labels
        ),
    }
    logits = [
        math.log(max(score, 1e-15) / max(1.0 - score, 1e-15)) for score in final_validation_scores
    ]
    phase12 = {
        "status": "PASS_FORMAL_PHASE12",
        "phase": 12,
        "selection_split": "VALIDATION",
        "calibration_fit_split": "TRAIN_OR_OOF_TRAIN",
        "evaluation_split": "VALIDATION",
        "locked_test_evaluated": False,
        "model_id": final_model_id,
        "methods": {"platt": platt, "isotonic": isotonic},
        "validation_metrics": calibrated,
        "reliability": {
            name: reliability(scores, validation_labels)
            for name, scores in {
                "uncalibrated": final_validation_scores,
                "platt": apply_platt(final_validation_scores, platt),
                "isotonic": apply_isotonic(final_validation_scores, isotonic),
            }.items()
        },
        "risk_coverage": compute_risk_coverage_curve(logits, validation_labels).to_dict(),
        "abstention": compute_abstention_analysis(logits, validation_labels).to_dict(),
    }
    atomic_json(phase12_root / "calibration_abstention.json", phase12)

    phase13 = run_phase13(
        ablations,
        final_feature,
        final_classifier,
        final_params,
        final_validation_scores,
        final_validation_rows,
        phase13_root,
    )
    calibration_choice = min(calibrated, key=lambda name: float(calibrated[name]["brier"]))
    frozen = {
        "selection_closed": True,
        "phase": "PRE_PHASE14_FREEZE",
        "model_id": final_model_id,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.5,
        "calibrator": calibration_choice,
        "base_models": [result.key for result in selected] if stack_is_final else [final_model_id],
        "feature_set": final_feature.name,
        "feature_names": final_feature.feature_names,
        "hpo": phase9["studies"][final_feature.name]["best_trial"],
        "formal_manifest_sha256": MANIFEST_SHA256,
        "formal_record_set_sha256": RECORD_SET_SHA256,
        "locked_test_evaluated": False,
        "post_test_tuning_allowed": False,
        "bootstrap_replicates": 1000,
    }
    frozen_hash = freeze_analysis_config(frozen).sha256
    atomic_json(phase13_root / "frozen_config.json", frozen)
    atomic_json(
        phase13_root / "pre_phase14_freeze.json",
        {
            "status": "PASS_PRE_PHASE14_FREEZE",
            "selection_closed": True,
            "config_sha256": frozen_hash,
            "config": frozen,
            "phase13_artifact": str(
                (phase13_root / "ablations_learning_curves_robustness.json").relative_to(REPO_ROOT)
            ),
            "locked_test_evaluated": False,
        },
    )

    report = {
        "status": "PASS_FORMAL_PHASE8_13_AND_PRE_PHASE14_FREEZE",
        "manifest_sha256": MANIFEST_SHA256,
        "record_set_sha256": RECORD_SET_SHA256,
        "phase8": phase8["status"],
        "phase9": phase9["status"],
        "phase10": "DEFERRED_BY_COMPUTE",
        "phase11": phase11["status"],
        "phase12": phase12["status"],
        "phase13": phase13["status"],
        "pre_phase14_freeze": "PASS_PRE_PHASE14_FREEZE",
        "final_model_id": final_model_id,
        "frozen_config_sha256": frozen_hash,
        "locked_test_evaluated": False,
    }
    atomic_json(root / "summary.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

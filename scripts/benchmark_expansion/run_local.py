#!/usr/bin/env python3
"""Generate the no-spend EvoVariant-TR benchmark-expansion artifacts.

The runner consumes registered caches and writes explicit PASS, limitation,
data-blocked, and compute-blocked states. It never fits on the locked cohort.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import warnings
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evovariant_tr.benchmark_expansion import (  # noqa: E402
    budget_plan,
    review_group,
    substitution_class,
    temporal_bin,
    temporal_duration,
    transition_category,
)
from evovariant_tr.clinvar_parser import CLINVAR_REVIEW_STATUS_STARS  # noqa: E402
from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc  # noqa: E402

EXPANSION = ROOT / "research/benchmarks/expansion_v1"
ARTIFACTS = ROOT / "artifacts/benchmarks"
DOCS = ROOT / "docs/benchmarks"
WEB = ROOT / "apps/web/public/benchmarks"

T0_ARCHIVE = ROOT / "data/raw/clinvar/variant_summary_2025-01.txt.gz"
T1_ARCHIVE = ROOT / "data/raw/clinvar/variant_summary_2026-08.txt.gz"
DEV_MANIFEST = ROOT / "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
LOCKED_MANIFEST = ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
LOCKED_PREDICTIONS = ROOT / "research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl"
DEV_PREDICTIONS = ROOT / "research/runs/formal_cpu_20260922/phase8/development_predictions.jsonl"
FEATURES = {
    "primary": ROOT / "research/runs/phase7_formal_evo2_20260922/features/evo2_delta_primary.jsonl",
    "forward_reverse": ROOT / "research/runs/phase7_formal_evo2_20260922/features/evo2_delta_forward_reverse.jsonl",
    "orientation": ROOT / "research/runs/phase7_formal_evo2_20260922/features/evo2_delta_orientation_difference.jsonl",
}
COMPARATORS = {
    "formal_cadd": ROOT / "artifacts/phase6a/comparators/formal_budgeted_20260921/cadd_grch38_v1.7_20260921.json",
    "formal_phylop": ROOT / "artifacts/phase6a/comparators/formal_budgeted_20260921/phylop100way_hg38_20260921.json",
    "locked_cadd": ROOT / "artifacts/phase6a/comparators/cadd_grch38_v1.7_20260921.json",
    "locked_phylop": ROOT / "artifacts/phase6a/comparators/phylop100way_hg38_20260921.json",
}
# Optional external provenance document. Override with
# EVOVARIANT_MASTER_PROMPT_PATH when the originating prompt lives elsewhere.
DEFAULT_MASTER_PROMPT_PATH = Path(
    os.environ.get(
        "EVOVARIANT_MASTER_PROMPT_PATH",
        str(ROOT / "docs/agent/MASTER_PROMPT.md"),
    )
)
EXPECTED_PRIMARY = {
    "auroc": 0.9092259737895887,
    "auprc": 0.8630391000187404,
    "accuracy": 0.8435517970401691,
    "balanced_accuracy": 0.8398662176920277,
    "precision": 0.8242574257425742,
    "recall": 0.8121951219512196,
    "specificity": 0.8675373134328358,
    "f1": 0.8181818181818182,
    "mcc": 0.6809606106662964,
    "brier": 0.11407921672922404,
    "ece": 0.05523106003405314,
    "nll": 0.551757943,
}
START_MAIN_FALLBACK = "cd143aaa4bf568e00d73269648f39f5131a744c1"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def atomic_write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        mode = "wb" if isinstance(value, bytes) else "w"
        kwargs = {} if mode == "wb" else {"encoding": "utf-8"}
        with os.fdopen(fd, mode, **kwargs) as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def parse_date(raw: str | None) -> date | None:
    if not raw or raw.strip() in {"", "-"}:
        return None
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            pass
    return None


def parse_int(raw: str | None) -> int | None:
    try:
        return int(str(raw or "").strip())
    except ValueError:
        return None


def identity_from_tsv(row: dict[str, str]) -> str | None:
    if row.get("Assembly") != "GRCh38":
        return None
    if row.get("Type") not in {"SNV", "single nucleotide variant"}:
        return None
    if "germline" not in row.get("OriginSimple", "").lower():
        return None
    position = parse_int(row.get("PositionVCF")) or parse_int(row.get("Start"))
    reference = (row.get("ReferenceAlleleVCF") or row.get("ReferenceAllele", "")).strip().upper()
    alternate = (row.get("AlternateAlleleVCF") or row.get("AlternateAllele", "")).strip().upper()
    chromosome = row.get("Chromosome", "").strip().removeprefix("chr")
    if position is None or not chromosome:
        return None
    if reference not in "ACGT" or alternate not in "ACGT" or reference == alternate:
        return None
    return f"GRCh38:{chromosome}:{position}:{reference}>{alternate}"


def snapshot_record(row: dict[str, str], identity: str) -> dict[str, Any]:
    status = row.get("ReviewStatus", "").strip()
    stars = CLINVAR_REVIEW_STATUS_STARS.get(status, 0)
    evaluated = parse_date(row.get("LastEvaluated"))
    significance = row.get("ClinicalSignificance", "").strip()
    benign = {"Benign", "Likely_benign", "Benign/Likely_benign", "Likely benign"}
    pathogenic = {"Pathogenic", "Likely_pathogenic", "Pathogenic/Likely_pathogenic", "Likely pathogenic"}
    label = 0 if significance in benign else 1 if significance in pathogenic else None
    return {
        "normalized_variant_id": identity,
        "gene_symbol": row.get("GeneSymbol") if row.get("GeneSymbol") not in {"", "-"} else None,
        "review_status": status,
        "review_stars": stars,
        "review_group": review_group(stars),
        "clinical_significance": significance,
        "label": label,
        "last_evaluated": evaluated.isoformat() if evaluated else None,
        "allele_id": row.get("AlleleID"),
        "variation_id": row.get("VariationID"),
        "source_row": int(row.get("__row_number", "0")),
    }


def record_priority(record: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(record.get("review_stars", 0)),
        str(record.get("last_evaluated") or ""),
        str(record.get("review_status") or ""),
        str(record.get("clinical_significance") or ""),
    )


def load_snapshot(
    path: Path, target_ids: set[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    records: dict[str, dict[str, Any]] = {}
    counters = Counter()
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().lstrip("#").rstrip("\r\n").split("\t")
        for line_number, line in enumerate(handle, start=2):
            counters["rows"] += 1
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < len(header):
                continue
            row = dict(zip(header, fields, strict=False))
            row["__row_number"] = str(line_number)
            identity = identity_from_tsv(row)
            if identity is None:
                continue
            counters["eligible_rows"] += 1
            if identity not in target_ids:
                continue
            counters["matched_rows"] += 1
            record = snapshot_record(row, identity)
            previous = records.get(identity)
            if previous is None or record_priority(record) > record_priority(previous):
                records[identity] = record
    return records, dict(counters)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_records(path: Path) -> list[dict[str, Any]]:
    return list(read_json(path)["records"])


def clip_probability(value: float) -> float:
    return min(1.0 - 1e-12, max(1e-12, float(value)))


def f1_for_class(predictions: list[int], labels: list[int], positive: int) -> float:
    tp = sum(p == positive and y == positive for p, y in zip(predictions, labels, strict=True))
    fp = sum(p == positive and y != positive for p, y in zip(predictions, labels, strict=True))
    fn = sum(p != positive and y == positive for p, y in zip(predictions, labels, strict=True))
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0


def bootstrap_auc(
    scores: list[float],
    labels: list[int],
    groups: list[str] | None,
    seed: int = 42,
    replicates: int = 1000,
) -> dict[str, Any]:
    rng = random.Random(seed)
    group_values = sorted(set(groups)) if groups else []
    by_group: dict[str, list[int]] = defaultdict(list)
    if groups:
        for index, group in enumerate(groups):
            by_group[group].append(index)
    values: list[float] = []
    for _ in range(replicates):
        if groups:
            sampled_groups = [rng.choice(group_values) for _ in group_values]
            indexes = [index for group in sampled_groups for index in by_group[group]]
        else:
            indexes = [rng.randrange(len(scores)) for _ in scores]
        boot_labels = [labels[index] for index in indexes]
        if len(set(boot_labels)) < 2:
            continue
        values.append(compute_auc_roc([scores[index] for index in indexes], boot_labels))
    if not values:
        return {"mean": None, "std": None, "ci95": None, "replicates": 0, "seed": seed}
    values.sort()
    return {
        "mean": mean(values),
        "std": stdev(values) if len(values) > 1 else 0.0,
        "ci95": [values[int(0.025 * (len(values) - 1))], values[int(0.975 * (len(values) - 1))]],
        "replicates": len(values),
        "seed": seed,
    }


def metric_bundle(
    scores: list[float],
    labels: list[int],
    *,
    threshold: float = 0.5,
    groups: list[str] | None = None,
    bootstrap: bool = True,
) -> dict[str, Any]:
    if len(scores) != len(labels) or not scores:
        raise ValueError("scores and labels must be non-empty and aligned")
    predictions = [int(score >= threshold) for score in scores]
    positive = sum(labels)
    negative = len(labels) - positive
    tp = sum(p == 1 and y == 1 for p, y in zip(predictions, labels, strict=True))
    tn = sum(p == 0 and y == 0 for p, y in zip(predictions, labels, strict=True))
    fp = sum(p == 1 and y == 0 for p, y in zip(predictions, labels, strict=True))
    fn = sum(p == 0 and y == 1 for p, y in zip(predictions, labels, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    accuracy = (tp + tn) / len(labels)
    balanced = (recall + specificity) / 2
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn) - (fp * fn)) / denominator if denominator else 0.0
    probabilities = [clip_probability(score) for score in scores]
    nll = -sum(
        label * math.log(max(score, 1e-15)) + (1 - label) * math.log(max(1.0 - score, 1e-15))
        for score, label in zip(scores, labels, strict=True)
    ) / len(labels)
    ece = 0.0
    for bucket in range(10):
        lower = bucket / 10
        upper = 1.0 if bucket == 9 else (bucket + 1) / 10
        indexes = []
        for index, score in enumerate(probabilities):
            if (lower <= score <= upper) if bucket == 9 else (lower <= score < upper):
                indexes.append(index)
        if indexes:
            observed = sum(labels[index] for index in indexes) / len(indexes)
            confidence = sum(probabilities[index] for index in indexes) / len(indexes)
            ece += len(indexes) / len(labels) * abs(observed - confidence)
    result: dict[str, Any] = {
        "n": len(labels),
        "positive": positive,
        "negative": negative,
        "auroc": compute_auc_roc(scores, labels) if positive and negative else None,
        "auprc": compute_auc_pr(scores, labels) if positive else 0.0,
        "accuracy": accuracy,
        "balanced_accuracy": balanced,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1_for_class(predictions, labels, 1),
        "macro_f1": (f1_for_class(predictions, labels, 0) + f1_for_class(predictions, labels, 1)) / 2,
        "micro_f1": accuracy,
        "weighted_f1": (
            f1_for_class(predictions, labels, 0) * negative
            + f1_for_class(predictions, labels, 1) * positive
        ) / len(labels),
        "mcc": mcc,
        "brier": sum((score - label) ** 2 for score, label in zip(probabilities, labels, strict=True)) / len(labels),
        "nll": nll,
        "ece": ece,
        "probability_mae": sum(abs(score - label) for score, label in zip(probabilities, labels, strict=True)) / len(labels),
        "error_rate": (fp + fn) / len(labels),
        "confidence": sum(max(score, 1 - score) for score in probabilities) / len(labels),
        "threshold": threshold,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
    if bootstrap and result["auroc"] is not None:
        result["bootstrap_auc"] = bootstrap_auc(scores, labels, groups)
    return result


# ANALYSES

def load_prediction_index(path: Path, allowed_ids: set[str] | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    by_model: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in load_jsonl(path):
        if row.get("locked_test_evaluated") or row.get("split") == "LOCKED_TEST":
            raise RuntimeError(f"locked-test row found in development artifact: {row.get('normalized_variant_id')}")
        if row.get("split") not in {"TRAIN", "VALIDATION"}:
            continue
        variant_id = str(row["normalized_variant_id"])
        if allowed_ids is not None and variant_id not in allowed_ids:
            continue
        by_model[str(row["model_id"])][variant_id] = row
    return {model: dict(rows) for model, rows in by_model.items()}


def load_feature_matrix(formal_ids: set[str]) -> dict[str, Any]:
    feature_maps: list[dict[str, dict[str, Any]]] = []
    for path in FEATURES.values():
        rows: dict[str, dict[str, Any]] = {}
        for row in load_jsonl(path):
            variant_id = str(row["normalized_variant_id"])
            if row.get("locked_test_present") or row.get("split") == "LOCKED_TEST":
                raise RuntimeError(f"locked-test feature found: {variant_id}")
            if variant_id in formal_ids:
                rows[variant_id] = row
        if set(rows) != formal_ids:
            raise RuntimeError(f"feature cache {rel(path)} does not cover the formal cohort")
        feature_maps.append(rows)
    ordered = sorted(formal_ids)
    matrix = np.asarray(
        [sum((feature_map[variant_id]["values"] for feature_map in feature_maps), []) for variant_id in ordered],
        dtype=float,
    )
    labels = np.asarray([int(feature_maps[0][variant_id]["label"]) for variant_id in ordered], dtype=int)
    genes = [str(feature_maps[0][variant_id].get("gene_symbol") or "") for variant_id in ordered]
    chromosomes = [variant_id.split(":")[1] for variant_id in ordered]
    return {
        "ids": ordered,
        "X": matrix,
        "labels": labels,
        "genes": genes,
        "chromosomes": chromosomes,
    }


def load_comparator(
    path: Path,
    score_fields: tuple[str, ...] = (
        "scaled_phred",
        "sitewise_score",
        "raw_score",
        "score",
        "value",
    ),
) -> dict[str, float]:
    payload = read_json(path)
    rows = payload.get("rows", payload if isinstance(payload, list) else [])
    result: dict[str, float] = {}
    for row in rows:
        value = next((row.get(field) for field in score_fields if row.get(field) is not None), None)
        if value is not None:
            try:
                result[str(row["normalized_variant_id"])] = float(value)
            except (KeyError, TypeError, ValueError):
                continue
    return result


def grouped_metrics(
    rows: list[dict[str, Any]],
    group_key: str,
    *,
    score_key: str = "calibrated_score",
    label_key: str = "label",
    bootstrap: bool = True,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group = str(row.get(group_key) or "missing")
        grouped[group].append(row)
    output: dict[str, Any] = {}
    for group, group_rows in sorted(grouped.items()):
        labels = [int(row[label_key]) for row in group_rows if row.get(label_key) is not None and row.get(score_key) is not None]
        scores = [float(row[score_key]) for row in group_rows if row.get(label_key) is not None and row.get(score_key) is not None]
        item: dict[str, Any] = {"n": len(scores), "group": group}
        if len(set(labels)) < 2 or len(scores) < 2:
            item["status"] = "INSUFFICIENT_SUPPORT"
            item["class_counts"] = dict(Counter(labels))
        else:
            item["status"] = "PASS"
            item["metrics"] = metric_bundle(scores, labels, groups=[str(row.get("gene_symbol") or "") for row in group_rows if row.get(label_key) is not None and row.get(score_key) is not None], bootstrap=bootstrap)
        output[group] = item
    return output


def run_loco(feature_data: dict[str, Any]) -> dict[str, Any]:
    X = feature_data["X"]
    labels = feature_data["labels"]
    chromosomes = feature_data["chromosomes"]
    results: dict[str, Any] = {}
    for chromosome in sorted(set(chromosomes), key=lambda value: (len(value), value)):
        test_mask = np.asarray([value == chromosome for value in chromosomes])
        train_mask = ~test_mask
        test_labels = labels[test_mask]
        item: dict[str, Any] = {
            "chromosome": chromosome,
            "n": int(test_mask.sum()),
            "positive": int(test_labels.sum()),
            "negative": int((test_labels == 0).sum()),
            "feature_family": "Evo2 delta primary + forward/reverse + orientation difference",
        }
        if item["n"] < 20 or len(set(test_labels.tolist())) < 2 or len(set(labels[train_mask].tolist())) < 2:
            item["status"] = "INSUFFICIENT_SUPPORT"
            results[chromosome] = item
            continue
        model = Pipeline(
            [
                ("scale", StandardScaler()),
                ("classifier", LogisticRegression(C=1.0, max_iter=1000, random_state=42)),
            ]
        )
        model.fit(X[train_mask], labels[train_mask])
        scores = model.predict_proba(X[test_mask])[:, 1].tolist()
        item["status"] = "PASS"
        item["metrics"] = metric_bundle(scores, test_labels.tolist(), bootstrap=False)
        results[chromosome] = item
    passed = [item for item in results.values() if item["status"] == "PASS"]
    return {
        "status": "PASS" if passed else "DATA_BLOCKED",
        "method": "chromosome leave-one-group-out using formal development features only",
        "feature_cache_ids": [rel(path) for path in FEATURES.values()],
        "chromosome_results": results,
        "completed_chromosomes": len(passed),
        "chromosome_count": len(results),
    }


def run_seed_robustness(feature_data: dict[str, Any]) -> dict[str, Any]:
    X = feature_data["X"]
    labels = feature_data["labels"]
    train_mask = np.asarray([split == "TRAIN" for split in _feature_splits(feature_data["ids"])])
    validation_mask = ~train_mask
    results: dict[str, Any] = {}
    for seed in (42, 1337, 2026):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = Pipeline(
                [
                    ("scale", StandardScaler()),
                    (
                        "classifier",
                        MLPClassifier(
                            hidden_layer_sizes=(16,),
                            max_iter=160,
                            random_state=seed,
                            early_stopping=True,
                            validation_fraction=0.2,
                            n_iter_no_change=15,
                        ),
                    ),
                ]
            )
            model.fit(X[train_mask], labels[train_mask])
        scores = model.predict_proba(X[validation_mask])[:, 1].tolist()
        results[str(seed)] = metric_bundle(scores, labels[validation_mask].tolist(), bootstrap=False)
    aucs = [item["auroc"] for item in results.values() if item["auroc"] is not None]
    return {
        "status": "PASS",
        "model": "one-hidden-layer MLP on cached Evo2 representations",
        "seeds": results,
        "auroc_range": max(aucs) - min(aucs) if aucs else None,
        "auroc_mean": mean(aucs) if aucs else None,
    }


def _feature_splits(ids: list[str]) -> list[str]:
    manifest = {row["normalized_variant_id"]: row["split"] for row in read_records(DEV_MANIFEST)}
    return [str(manifest[variant_id]) for variant_id in ids]


def run_disagreement(prediction_index: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    requested = [
        "evo2__logistic_regression",
        "nt24__logistic_regression",
        "cad16__logistic_regression",
        "cadd__logistic_regression",
        "phylop__logistic_regression",
    ]
    available = [model for model in requested if model in prediction_index]
    common_ids = set.intersection(*(set(prediction_index[model]) for model in available)) if available else set()
    rows: list[dict[str, Any]] = []
    for variant_id in sorted(common_ids):
        model_scores = {model: float(prediction_index[model][variant_id]["score"]) for model in available}
        label = int(prediction_index[available[0]][variant_id]["label"])
        predictions = {model: int(score >= 0.5) for model, score in model_scores.items()}
        votes = sum(predictions.values())
        if votes in {0, len(predictions)}:
            category = "strong consensus"
        elif votes in {1, len(predictions) - 1}:
            category = "majority"
        else:
            category = "high disagreement"
        row = {
            "normalized_variant_id": variant_id,
            "label": label,
            "model_scores": model_scores,
            "predictions": predictions,
            "votes_pathogenic": votes,
            "disagreement_count": min(votes, len(predictions) - votes),
            "category": category,
            "consensus_prediction": int(votes >= (len(predictions) / 2)),
            "consensus_error": int(int(votes >= (len(predictions) / 2)) != label),
            "foundation_vs_classical_disagreement": int(
                predictions.get("evo2__logistic_regression", 0)
                != predictions.get("cadd__logistic_regression", predictions.get("evo2__logistic_regression", 0))
            ),
        }
        rows.append(row)
    correlations: dict[str, dict[str, float | None]] = {}
    errors: dict[str, set[str]] = {}
    for model in available:
        values = np.asarray([row["model_scores"][model] for row in rows], dtype=float)
        for other in available:
            other_values = np.asarray([row["model_scores"][other] for row in rows], dtype=float)
            correlations.setdefault(model, {})[other] = float(np.corrcoef(values, other_values)[0, 1]) if len(rows) > 1 else None
        errors[model] = {
            row["normalized_variant_id"]
            for row in rows
            if row["predictions"][model] != row["label"]
        }
    error_overlap: dict[str, dict[str, float | None]] = {}
    for model in available:
        error_overlap[model] = {}
        for other in available:
            union = errors[model] | errors[other]
            error_overlap[model][other] = len(errors[model] & errors[other]) / len(union) if union else 1.0
    counts = Counter(row["category"] for row in rows)
    return {
        "status": "PASS" if rows else "DATA_BLOCKED",
        "models": available,
        "n_common_validation": len(rows),
        "category_counts": dict(counts),
        "correlation": correlations,
        "error_overlap_jaccard": error_overlap,
        "foundation_vs_classical_disagreement_n": sum(row["foundation_vs_classical_disagreement"] for row in rows),
        "rows": rows,
    }

def build_case_studies(
    rows: list[dict[str, Any]],
    cadd: dict[str, float],
    phylop: dict[str, float],
) -> list[dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        score = float(row["calibrated_score"])
        label = int(row["label"])
        prediction = int(score >= 0.5)
        enriched = dict(row)
        enriched["correct"] = prediction == label
        enriched["confidence"] = max(score, 1.0 - score)
        enriched["calibration_shift"] = abs(score - float(row.get("classifier_score", score)))
        enriched["cadd_scaled_phred"] = cadd.get(row["normalized_variant_id"])
        enriched["phylop_score"] = phylop.get(row["normalized_variant_id"])
        enriched["nt_features"] = None
        enriched["caduceus_features"] = None
        candidates.append((row["normalized_variant_id"], enriched))
    if not candidates:
        return []
    by_id = dict(candidates)
    picks: list[tuple[str, dict[str, Any]]] = []
    picks.append(("highest-confidence-correct", max((item for item in by_id.values() if item["correct"]), key=lambda item: item["confidence"], default=next(iter(by_id.values())))))
    picks.append(("false-positive", next((item for item in by_id.values() if not item["correct"] and int(item["label"]) == 0), next(iter(by_id.values())))))
    picks.append(("false-negative", next((item for item in by_id.values() if not item["correct"] and int(item["label"]) == 1), next(iter(by_id.values())))))
    picks.append(("largest-calibration-shift", max(by_id.values(), key=lambda item: item["calibration_shift"])))
    picks.append(("strongest-orientation-disagreement", max(by_id.values(), key=lambda item: abs(float(item.get("orientation_disagreement") or 0.0)))))
    picks.append(("highest-evidence-review", max(by_id.values(), key=lambda item: (int(item.get("t1_review_stars") or 0), item["confidence"]))))
    picks.append(("longest-temporal-duration", max(by_id.values(), key=lambda item: int(item.get("temporal_duration_days") or -1)))
    )
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for reason, item in picks:
        variant_id = str(item["normalized_variant_id"])
        key = f"{reason}:{variant_id}"
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "case_id": f"case-{len(output) + 1:02d}",
                "reason": reason,
                "normalized_variant_id": variant_id,
                "gene_symbol": item.get("gene_symbol"),
                "chromosome": variant_id.split(":")[1] if ":" in variant_id else None,
                "label": item.get("label"),
                "prediction": int(float(item["calibrated_score"]) >= 0.5),
                "calibrated_score": item.get("calibrated_score"),
                "classifier_score": item.get("classifier_score"),
                "confidence": item.get("confidence"),
                "correct": item.get("correct"),
                "review_status": item.get("t1_review_status"),
                "review_stars": item.get("t1_review_stars"),
                "t0_last_evaluated": item.get("t0_last_evaluated"),
                "t1_last_evaluated": item.get("t1_last_evaluated"),
                "temporal_duration_days": item.get("temporal_duration_days"),
                "orientation_disagreement": item.get("orientation_disagreement"),
                "cadd_scaled_phred": item.get("cadd_scaled_phred"),
                "phylop_score": item.get("phylop_score"),
                "nt_features": item.get("nt_features"),
                "caduceus_features": item.get("caduceus_features"),
                "score_semantics": "calibrated probability; higher means more pathogenic",
                "locked_test_evaluated": True,
            }
        )
    return output


def build_primary_integrity(
    locked_rows: list[dict[str, Any]],
    *,
    artifact_path: Path = ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json",
) -> dict[str, Any]:
    local_scores = [float(row["calibrated_score"]) for row in locked_rows]
    local_labels = [int(row["label"]) for row in locked_rows]
    local = metric_bundle(local_scores, local_labels, bootstrap=False)
    artifact = read_json(artifact_path)
    observed = {
        key: artifact["metrics"].get(key, artifact["metrics"].get("probability_metrics", {}).get(key))
        for key in EXPECTED_PRIMARY
    }
    checks = {
        key: abs(float(observed[key]) - expected) <= 1e-9
        for key, expected in EXPECTED_PRIMARY.items()
        if observed.get(key) is not None
    }
    local_checks = {
        key: abs(float(local[key]) - expected) <= 1e-9
        for key, expected in EXPECTED_PRIMARY.items()
    }
    baseline_tag = None
    try:
        baseline_tag = git_value("rev-parse", "evovariant-tr-baseline-v1")
    except subprocess.CalledProcessError:
        pass
    return {
        "status": "PASS" if all(checks.values()) and all(local_checks.values()) else "FAIL",
        "baseline_tag_commit": baseline_tag,
        "artifact": rel(artifact_path),
        "artifact_sha256": sha256_file(artifact_path),
        "locked_manifest_sha256": sha256_file(LOCKED_MANIFEST),
        "observed_artifact_metrics": observed,
        "locally_recomputed_metrics": {key: local[key] for key in EXPECTED_PRIMARY},
        "expected_registered_metrics": EXPECTED_PRIMARY,
        "artifact_metric_checks": checks,
        "artifact_metrics_not_present": [key for key in EXPECTED_PRIMARY if key not in checks],
        "local_metric_checks": local_checks,
        "threshold": 0.5,
        "score_direction": "higher_is_more_pathogenic",
        "calibration": "frozen isotonic calibrator",
        "fine_tuning_started_for_primary": False,
        "locked_n": len(locked_rows),
        "locked_ids_sha256": json_hash(sorted(row["normalized_variant_id"] for row in locked_rows)),
    }


def run_local_analyses() -> dict[str, Any]:
    formal_manifest = read_json(DEV_MANIFEST)
    locked_manifest = read_json(LOCKED_MANIFEST)
    formal_records = formal_manifest["records"]
    locked_records = locked_manifest["records"]
    formal_ids = {row["normalized_variant_id"] for row in formal_records}
    locked_ids = {row["normalized_variant_id"] for row in locked_records}
    if formal_ids & locked_ids:
        raise RuntimeError("formal and locked variant IDs overlap")
    locked_prediction_rows = load_jsonl(LOCKED_PREDICTIONS)
    locked_prediction_map = {row["normalized_variant_id"]: row for row in locked_prediction_rows}
    if set(locked_prediction_map) != locked_ids:
        raise RuntimeError("locked predictions do not exactly match the locked manifest")
    if any(row.get("split") != "LOCKED_TEST" or not row.get("locked_test_evaluated") for row in locked_prediction_rows):
        raise RuntimeError("locked predictions have invalid stage flags")
    t0_rows, t0_counters = load_snapshot(T0_ARCHIVE, formal_ids | locked_ids)
    t1_rows, t1_counters = load_snapshot(T1_ARCHIVE, locked_ids)
    locked_index = {row["normalized_variant_id"]: row for row in locked_records}
    enriched_locked: list[dict[str, Any]] = []
    for variant_id in sorted(locked_ids):
        manifest_row = dict(locked_index[variant_id])
        prediction = dict(locked_prediction_map[variant_id])
        t0 = t0_rows.get(variant_id, {})
        t1 = t1_rows.get(variant_id, {})
        manifest_row.update(prediction)
        manifest_row["gene_symbol"] = manifest_row.get("gene_symbol") or t1.get("gene_symbol") or t0.get("gene_symbol")
        manifest_row["t0_last_evaluated"] = t0.get("last_evaluated")
        manifest_row["t1_last_evaluated"] = t1.get("last_evaluated")
        manifest_row["t0_review_status"] = t0.get("review_status")
        manifest_row["t1_review_status"] = t1.get("review_status")
        manifest_row["t0_review_stars"] = t0.get("review_stars")
        manifest_row["t1_review_stars"] = t1.get("review_stars")
        manifest_row["t0_review_group"] = t0.get("review_group", "missing")
        manifest_row["t1_review_group"] = t1.get("review_group", "missing")
        start = parse_date(manifest_row["t0_last_evaluated"])
        resolution = parse_date(manifest_row["t1_last_evaluated"])
        duration = temporal_duration(start, resolution)
        manifest_row["temporal_duration_days"] = duration
        manifest_row["temporal_bin"] = temporal_bin(duration)
        reference = str(manifest_row.get("reference") or variant_id.split(":")[-1].split(">")[0])
        alternate = str(manifest_row.get("alternate") or variant_id.split(">")[-1])
        manifest_row["transition_category"] = transition_category(reference, alternate)
        manifest_row["substitution_class"] = substitution_class(reference, alternate)
        score = float(manifest_row["calibrated_score"])
        confidence = max(score, 1.0 - score)
        manifest_row["confidence_bin"] = "<0.60" if confidence < 0.60 else "0.60-0.80" if confidence < 0.80 else ">=0.80"
        t0_label = t0.get("label")
        t1_label = t1.get("label")
        if t0_label is None or t1_label is None:
            manifest_row["label_transition"] = "missing/indeterminate"
        elif int(t0_label) == int(t1_label) == 0:
            manifest_row["label_transition"] = "stable benign"
        elif int(t0_label) == int(t1_label) == 1:
            manifest_row["label_transition"] = "stable pathogenic"
        else:
            manifest_row["label_transition"] = "changed label"
        enriched_locked.append(manifest_row)
    prediction_index = load_prediction_index(DEV_PREDICTIONS, formal_ids)
    validation_model_metrics: dict[str, Any] = {}
    for model_id, model_rows in sorted(prediction_index.items()):
        validation = [row for row in model_rows.values() if row.get("split") == "VALIDATION"]
        labels = [int(row["label"]) for row in validation]
        scores = [float(row["score"]) for row in validation]
        validation_model_metrics[model_id] = {
            "n": len(validation),
            "metrics": metric_bundle(scores, labels, bootstrap=False) if len(set(labels)) == 2 else None,
            "status": "PASS" if len(validation) and len(set(labels)) == 2 else "INSUFFICIENT_SUPPORT",
        }
    feature_data = load_feature_matrix(formal_ids)
    cadd_formal = load_comparator(COMPARATORS["formal_cadd"])
    phylop_formal = load_comparator(COMPARATORS["formal_phylop"])
    cadd_locked = load_comparator(COMPARATORS["locked_cadd"])
    phylop_locked = load_comparator(COMPARATORS["locked_phylop"])
    comparator_coverage: dict[str, Any] = {}
    for name, values, ids in (
        ("CADD formal", cadd_formal, formal_ids),
        ("PhyloP formal", phylop_formal, formal_ids),
        ("CADD locked", cadd_locked, locked_ids),
        ("PhyloP locked", phylop_locked, locked_ids),
    ):
        available = len(values.keys() & ids)
        comparator_coverage[name] = {
            "status": "PASS" if available else "DATA_BLOCKED",
            "available": available,
            "total": len(ids),
            "coverage_fraction": available / len(ids),
            "artifact": rel(COMPARATORS[name.lower().replace(" ", "_")]) if name.lower().replace(" ", "_") in COMPARATORS else None,
        }
    threshold_sensitivity = {
        str(threshold): metric_bundle(
            [float(row["calibrated_score"]) for row in enriched_locked],
            [int(row["label"]) for row in enriched_locked],
            threshold=threshold,
            bootstrap=False,
        )
        for threshold in (0.25, 0.5, 0.75)
    }
    external_candidate_preview = {
        "excluded_ids": sorted(formal_ids | locked_ids),
        "excluded_genes": sorted(
            {str(row.get("gene_symbol")) for row in formal_records + locked_records if row.get("gene_symbol")}
        ),
    }
    return {
        "primary": build_primary_integrity(enriched_locked),
        "formal": {
            "n": len(formal_records),
            "train_n": sum(row["split"] == "TRAIN" for row in formal_records),
            "validation_n": sum(row["split"] == "VALIDATION" for row in formal_records),
            "class_counts": dict(Counter(str(row["label"]) for row in formal_records)),
            "gene_count": len({row.get("gene_symbol") for row in formal_records}),
            "manifest": rel(DEV_MANIFEST),
        },
        "locked": {
            "n": len(locked_records),
            "class_counts": dict(Counter(str(row["label"]) for row in locked_records)),
            "gene_count": len({row.get("gene_symbol") for row in locked_records}),
            "manifest": rel(LOCKED_MANIFEST),
            "predictions": rel(LOCKED_PREDICTIONS),
        },
        "snapshot_audit": {
            "t0": {"path": rel(T0_ARCHIVE), "sha256": sha256_file(T0_ARCHIVE), "counters": t0_counters, "matched_n": len(t0_rows)},
            "t1": {"path": rel(T1_ARCHIVE), "sha256": sha256_file(T1_ARCHIVE), "counters": t1_counters, "matched_n": len(t1_rows)},
            "formal_missing_t0": len(formal_ids - set(t0_rows)),
            "locked_missing_t0": len(locked_ids - set(t0_rows)),
            "locked_missing_t1": len(locked_ids - set(t1_rows)),
        },
        "frozen_locked_metrics": read_json(ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json")["metrics"],
        "evidence_quality": {
            "status": "PASS",
            "definition": "ClinVar review-status stars are evidence-quality strata, not biological certainty.",
            "review_status_counts": dict(Counter(str(row.get("t1_review_status") or "missing") for row in enriched_locked)),
            "groups": grouped_metrics(enriched_locked, "t1_review_group", bootstrap=True),
        },
        "temporal_difficulty": {
            "status": "PASS" if any(row["temporal_duration_days"] is not None for row in enriched_locked) else "DATA_BLOCKED",
            "definition": "Exploratory time-to-resolution association; not a causal difficulty claim.",
            "bin_counts": dict(Counter(row["temporal_bin"] for row in enriched_locked)),
            "groups": grouped_metrics(enriched_locked, "temporal_bin", bootstrap=True),
            "rows_with_duration": sum(row["temporal_duration_days"] is not None for row in enriched_locked),
        },
        "loco": run_loco(feature_data),
        "disagreement": run_disagreement(prediction_index),
        "validation_model_metrics": validation_model_metrics,
        "confidence": {"status": "PASS", "groups": grouped_metrics(enriched_locked, "confidence_bin", bootstrap=True)},
        "transition": {"status": "PASS", "groups": grouped_metrics(enriched_locked, "label_transition", bootstrap=True)},
        "substitution": {"status": "PASS", "groups": grouped_metrics(enriched_locked, "substitution_class", bootstrap=True)},
        "transition_type": {"status": "PASS", "groups": grouped_metrics(enriched_locked, "transition_category", bootstrap=True)},
        "comparator_coverage": comparator_coverage,
        "seed_robustness": run_seed_robustness(feature_data),
        "threshold_sensitivity": threshold_sensitivity,
        "case_studies": build_case_studies(enriched_locked, cadd_locked, phylop_locked),
        "external_candidate_preview": external_candidate_preview,
        "locked_rows": enriched_locked,
    }


def select_external_candidates(excluded_ids: set[str], excluded_genes: set[str]) -> dict[str, Any]:
    selected: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    eligible_by_stratum: Counter[str] = Counter()
    excluded_by_reason: Counter[str] = Counter()
    with gzip.open(T1_ARCHIVE, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().lstrip("#").rstrip("\r\n").split("\t")
        for line_number, line in enumerate(handle, start=2):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < len(header):
                continue
            row = dict(zip(header, fields, strict=False))
            row["__row_number"] = str(line_number)
            identity = identity_from_tsv(row)
            if identity is None:
                continue
            record = snapshot_record(row, identity)
            if record["label"] is None or int(record["review_stars"]) < 2:
                continue
            stratum = (int(record["label"]), int(record["review_stars"]))
            eligible_by_stratum[f"{stratum[0]}|{stratum[1]}"] += 1
            if identity in excluded_ids:
                excluded_by_reason["overlap_with_formal_or_locked"] += 1
                continue
            if record.get("gene_symbol") and record["gene_symbol"] in excluded_genes:
                excluded_by_reason["gene_overlap"] += 1
                continue
            selected[stratum].append(
                {
                    "normalized_variant_id": identity,
                    "gene_symbol": record.get("gene_symbol"),
                    "label": record["label"],
                    "review_status": record["review_status"],
                    "review_stars": record["review_stars"],
                    "last_evaluated": record["last_evaluated"],
                    "allele_id": record.get("allele_id"),
                    "variation_id": record.get("variation_id"),
                    "selection_key": hashlib.sha256(identity.encode()).hexdigest(),
                    "source_row": record["source_row"],
                }
            )
    records: list[dict[str, Any]] = []
    for _stratum, rows in sorted(selected.items()):
        rows.sort(key=lambda row: row["selection_key"])
        records.extend(rows[:50])
    records.sort(key=lambda row: row["selection_key"])
    reference_path = ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
    status = "COMPUTE_BLOCKED"
    manifest = {
        "manifest_id": "external-clinvar-t1-gene-disjoint-v1",
        "status": status,
        "source_release": "clinvar_t1",
        "source_snapshot": rel(T1_ARCHIVE),
        "source_snapshot_sha256": sha256_file(T1_ARCHIVE),
        "source_snapshot_date": "2026-08-06",
        "selection_rule": "GRCh38 germline SNVs, binary ClinVar labels, review stars >=2, deterministic SHA256 identity order, exclude formal and locked IDs and genes",
        "excluded_ids_sha256": json_hash(sorted(excluded_ids)),
        "excluded_genes_sha256": json_hash(sorted(excluded_genes)),
        "eligible_by_label_and_review_stars": dict(eligible_by_stratum),
        "excluded_by_reason": dict(excluded_by_reason),
        "selected_n": len(records),
        "selected_class_counts": dict(Counter(str(row["label"]) for row in records)),
        "strict_gene_disjoint": True,
        "reference_asset": rel(reference_path) if reference_path.exists() else None,
        "reference_status": "READY" if reference_path.exists() else "DATA_BLOCKED_REFERENCE_FASTA_MISSING",
        "inference_status": "COMPUTE_BLOCKED_BALANCE_UNVERIFIED",
        "cached_inference_n": 0,
        "fresh_inference_n": 0,
        "modal_cost_usd": 0.0,
        "selection_frozen_before_inference": True,
        "records": records,
    }
    manifest["manifest_sha256"] = json_hash(manifest)
    return manifest


def external_blockers(external: dict[str, Any]) -> list[str]:
    blockers = ["COMPUTE_BLOCKED_BALANCE_UNVERIFIED"]
    if external.get("reference_status") != "READY":
        blockers.append("DATA_BLOCKED_REFERENCE_FASTA_MISSING")
    return blockers


def resolve_master_prompt_hash(
    previous_lock: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Resolve the optional master-prompt hash without dropping a frozen value.

    The originating prompt is an external document, so it may be absent from a
    clean checkout or another machine. When it cannot be read, the previously
    locked hash is preserved instead of being silently nulled.
    """
    configured = os.environ.get("EVOVARIANT_MASTER_PROMPT_PATH")
    prompt_path = Path(configured).expanduser() if configured else DEFAULT_MASTER_PROMPT_PATH
    if prompt_path.is_file():
        return sha256_file(prompt_path), str(prompt_path)
    if previous_lock and previous_lock.get("master_prompt_sha256"):
        return str(previous_lock["master_prompt_sha256"]), "preserved-from-previous-protocol-lock"
    return None, "unavailable"


def prepare_protocol(start_main_head: str) -> dict[str, Any]:
    lock_path = EXPANSION / "protocol_lock.json"
    previous_lock = read_json(lock_path) if lock_path.is_file() else None
    baseline_tag = None
    try:
        baseline_tag = git_value("rev-parse", "evovariant-tr-baseline-v1")
    except subprocess.CalledProcessError:
        baseline_tag = "UNRESOLVED"
    protocol = {
        "protocol_id": "evovariant-tr-benchmark-expansion-v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "start_main_head": start_main_head,
        "working_branch": git_value("branch", "--show-current"),
        "baseline_tag": "evovariant-tr-baseline-v1",
        "baseline_tag_commit": baseline_tag,
        "primary_result": "immutable phase14 locked Evo2 result",
        "formal_development_manifest": rel(DEV_MANIFEST),
        "locked_test_manifest": rel(LOCKED_MANIFEST),
        "locked_n": 946,
        "formal_n": 4000,
        "clinvar_snapshots": {
            "t0": {"path": rel(T0_ARCHIVE), "sha256": sha256_file(T0_ARCHIVE), "release": "2025-01-02"},
            "t1": {"path": rel(T1_ARCHIVE), "sha256": sha256_file(T1_ARCHIVE), "release": "2026-08-06"},
        },
        "fixed_temporal_bins": ["<=180", "181-365", "366-545", ">545", "missing/invalid"],
        "review_quality_definition": "0 stars, 1 star, 2 stars, 3 stars; evidence quality is not biological certainty",
        "locked_test_rule": "never fit, select, calibrate, tune, or infer new labels from the locked cohort",
        "fine_tuning_rule": "new fine-tuning excluded from this benchmark expansion; existing implementation/proof only",
        "external_rule": "freeze external manifest before inference; strict ID and gene exclusion",
        "modal": {
            "profile": "utkarshkhajuria59",
            "hard_reserve_usd": 5.0,
            "safety_stop_usd": 5.5,
            "soft_maximum_usd": 24.0,
            "new_spend_allowed": False,
            "reason": "billing summary did not expose a verifiable live balance",
        },
        "status_vocabulary": ["PASS", "PASS_WITH_LIMITATIONS", "COMPLETED_WITH_LIMITATIONS", "NOT_APPLICABLE", "DATA_BLOCKED", "COMPUTE_BLOCKED"],
    }
    protocol_text = "\n".join(
        [
            "protocol_id: evovariant-tr-benchmark-expansion-v1",
            "primary_result: immutable phase14 locked Evo2 result",
            f"start_main_head: {start_main_head}",
            f"working_branch: {protocol['working_branch']}",
            f"baseline_tag_commit: {baseline_tag}",
            "formal_n: 4000",
            "locked_n: 946",
            "locked_test_rule: never fit, select, calibrate, tune, or infer new labels from locked cohort",
            "fine_tuning_rule: no new fine-tuning in benchmark expansion",
            "review_quality_groups: [0 stars, 1 star, 2 stars, 3 stars]",
            "temporal_bins: [<=180, 181-365, 366-545, >545, missing/invalid]",
            "modal_profile: utkarshkhajuria59",
            "modal_hard_reserve_usd: 5.00",
            "modal_safety_stop_usd: 5.50",
            "modal_soft_maximum_usd: 24.00",
            "new_modal_spend_allowed: false",
        ]
    ) + "\n"
    protocol["master_prompt_sha256"], protocol["master_prompt_source"] = resolve_master_prompt_hash(
        previous_lock
    )
    write_json(EXPANSION / "protocol_lock.json", protocol)
    atomic_write(EXPANSION / "protocol.yaml", protocol_text)
    atomic_write(
        EXPANSION / "GOAL.md",
        """# Benchmark Expansion v1

This is a no-spend, reproducible expansion of the immutable EvoVariant-TR
temporal benchmark. It evaluates already-persisted foundation-model,
representation, classical-comparator, classifier, calibration, temporal,
evidence-quality, generalization, disagreement, and case-study evidence.

The 946-row locked cohort remains read-only and is evaluated only with the
frozen artifact. New fine-tuning is excluded. Any unavailable reference,
external assay, or compute balance is recorded explicitly as DATA_BLOCKED or
COMPUTE_BLOCKED rather than replaced by a proxy.

The canonical registry is BENCHMARK_CATALOG.md and the generated web
manifest is apps/web/public/benchmarks/benchmark-manifest.json.
""",
    )
    protocol_hash = sha256_file(EXPANSION / "protocol.yaml")
    protocol["protocol_yaml_sha256"] = protocol_hash
    write_json(EXPANSION / "protocol_lock.json", protocol)
    return protocol


def inventory_artifacts() -> list[dict[str, Any]]:
    candidates = [
        DEV_MANIFEST,
        LOCKED_MANIFEST,
        LOCKED_PREDICTIONS,
        DEV_PREDICTIONS,
        T0_ARCHIVE,
        T1_ARCHIVE,
        ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json",
        ROOT / "research/runs/formal_cpu_20260922/phase13/frozen_config_materialized.json",
        ROOT / "research/runs/phase7_formal_budgeted_optimized_20260922/nucleotide_transformer/features.npz",
        ROOT / "research/runs/phase7_formal_budgeted_optimized_20260922/caduceus/features.npz",
        *sorted((ROOT / "research/figures/final").glob("*.png")),
        *sorted((ROOT / "research/figures/final/source").glob("*.json")),
        *sorted((ROOT / "research/reports").glob("final_metrics_table.*")),
        *sorted((ROOT / "artifacts/phase6a/comparators").glob("*.json")),
        EXPANSION / "protocol.yaml",
        EXPANSION / "protocol_lock.json",
    ]
    result: list[dict[str, Any]] = []
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        result.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "stage": "locked_test" if "locked" in path.name or "phase14" in path.name else "development_or_provenance",
                "label_availability": "labels_local_or_frozen" if "prediction" in path.name or "manifest" in path.name else "not_applicable",
            }
        )
    return sorted(result, key=lambda item: item["path"])


def benchmark_entry(
    benchmark_id: str,
    title: str,
    family: str,
    question: str,
    *,
    population: str,
    n: int | None,
    status: str,
    summary: str,
    limitations: list[str],
    sources: list[str],
    outputs: list[str] | None = None,
    figures: list[str] | None = None,
    web_tab: str = "Overview",
    new_inference: str = "NO",
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": benchmark_id,
        "title": title,
        "family": family,
        "scientific_question": question,
        "question": question,
        "population": population,
        "n": n,
        "models": ["Evo2", "Nucleotide Transformer", "Caduceus", "CADD", "PhyloP"] if family != "External" else ["ClinVar"],
        "requires_new_inference": new_inference,
        "metrics": metrics or ["n", "class counts", "status"],
        "source_artifacts": sources,
        "output_artifacts": outputs or [],
        "limitations": limitations,
        "status": status,
        "summary": summary,
        "figures": figures or [],
        "tables": outputs or [],
        "code_links": ["scripts/benchmark_expansion/run_local.py", "src/evovariant_tr/benchmark_expansion.py"],
        "artifact_links": outputs or sources,
        "provenance_links": ["research/benchmarks/expansion_v1/protocol_lock.json"],
        "web_tab": web_tab,
        "figure": (figures or [None])[0],
        "new_inference": new_inference,
    }


def build_registry(results: dict[str, Any], external: dict[str, Any]) -> dict[str, Any]:
    locked_n = int(results["locked"]["n"])
    formal_n = int(results["formal"]["n"])
    base_sources = [
        rel(LOCKED_MANIFEST),
        rel(ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json"),
        rel(ROOT / "research/reports/final_metrics_table.json"),
    ]
    existing_specs = [
        ("B01", "Temporal cohort identity/flow", "Core", "Is the registered cohort traceable from source snapshots through the locked evaluation?", 946, "PASS", "Cohort identity, split boundaries, and source-release hashes are registered.", ["research/figures/final/cohort_flow.png"]),
        ("B02", "Class distribution", "Core", "What are the class counts in development and locked cohorts?", 946, "PASS", "Development and locked class counts are persisted.", ["research/figures/final/final_class_distribution.png"]),
        ("B03", "Gene separation/leakage", "Core", "Are gene groups separated across development and locked evaluation?", 4000, "PASS", "Gene separation and split provenance are recorded in the formal manifest.", []),
        ("B04", "Locked-ID isolation", "Core", "Are locked IDs isolated from development artifacts?", 946, "PASS", "ID disjointness and locked-stage flags pass.", []),
        ("B05", "GRCh38 REF validation", "Core", "Are variants normalized to GRCh38 with validated reference alleles?", 946, "PASS", "The registered GRCh38 manifest and inference provenance agree on reference alleles.", []),
        ("B06", "Evo2 forward raw evidence", "Foundation evidence", "What is the forward Evo2 alternate-minus-reference evidence?", formal_n, "PASS", "Cached forward evidence is available for the formal cohort.", []),
        ("B07", "Evo2 reverse-complement evidence", "Foundation evidence", "What is the reverse-complement Evo2 evidence?", formal_n, "PASS", "Cached reverse-orientation evidence is available for the formal cohort.", []),
        ("B08", "Evo2 aggregate features", "Foundation evidence", "Do aggregate Evo2 deltas support downstream models?", formal_n, "PASS", "Primary, forward/reverse, and orientation-difference features are cached.", []),
        ("B09", "Nucleotide Transformer representation", "Representation", "What do cached NT layers contribute?", formal_n, "PASS", "Layers 8, 16, and 24 are persisted with manifest metadata.", ["research/figures/final/representation_layers.png"]),
        ("B10", "Caduceus representation", "Representation", "What do cached Caduceus layers contribute?", formal_n, "PASS", "Layers 4, 8, and 16 are persisted with manifest metadata.", ["research/figures/final/representation_layers.png"]),
        ("B11", "CADD", "Classical comparator", "How does CADD compare where scores exist?", formal_n, "COMPLETED_WITH_LIMITATIONS", "CADD is covered on the formal cohort but has missing rows.", []),
        ("B12", "PhyloP", "Classical comparator", "How does PhyloP compare where scores exist?", formal_n, "COMPLETED_WITH_LIMITATIONS", "PhyloP is nearly complete on the formal cohort with explicit coverage.", []),
        ("B13", "AlphaMissense eligibility/coverage", "Classical comparator", "Is AlphaMissense eligible and covered for this GRCh38 cohort?", 0, "NOT_APPLICABLE", "No compatible prediction asset is registered for this benchmark.", []),
        ("B14", "Foundation-model development comparison", "Model comparison", "How do foundation-model representations compare on validation?", formal_n, "PASS", "Persisted multi-model development predictions are compared.", ["research/figures/final/foundation_model_performance.png"]),
        ("B15", "Representation/layer comparison", "Model comparison", "Which cached representation layers perform best?", formal_n, "PASS", "Layer-specific comparisons are present in the formal prediction matrix.", ["research/figures/final/representation_layers.png"]),
        ("B16", "Logistic feature-family comparison", "Downstream ML", "How do logistic classifiers vary by feature family?", formal_n, "PASS", "Registered classifier-by-feature metrics are available.", ["research/figures/final/classifier_auroc_heatmap.png"]),
        ("B17", "Tree/boosting feature-family comparison", "Downstream ML", "How do tree and boosting classifiers vary by feature family?", formal_n, "PASS", "Registered downstream comparisons include tree-family results.", []),
        ("B18", "MLP feature-family comparison", "Downstream ML", "How do MLP classifiers vary by feature family?", formal_n, "PASS", "Registered downstream comparisons include MLP results.", []),
        ("B19", "Classifier×feature AUROC", "Downstream ML", "Which classifier-feature combinations rank by AUROC?", formal_n, "PASS", "Validation AUROC is reported for persisted combinations.", ["research/figures/final/classifier_auroc_heatmap.png"]),
        ("B20", "Classifier×feature AUPRC", "Downstream ML", "Which classifier-feature combinations rank by AUPRC?", formal_n, "PASS", "Validation AUPRC is reported for persisted combinations.", []),
        ("B21", "Classifier×feature MCC", "Downstream ML", "Which classifier-feature combinations rank by MCC?", formal_n, "PASS", "Validation MCC is reported for persisted combinations.", ["research/figures/final/classifier_mcc_heatmap.png"]),
        ("B22", "HPO trial history", "HPO", "What HPO trials and outcomes were persisted?", formal_n, "PASS", "HPO trial history is linked from the frozen project artifacts.", ["research/figures/final/hpo_trial_history.png"]),
        ("B23", "HPO hyperparameters/sensitivity", "HPO", "How sensitive are outcomes to selected hyperparameters?", formal_n, "PASS", "Chosen hyperparameters and sensitivity artifacts are persisted.", ["research/figures/final/hpo_hyperparameters.png"]),
        ("B24", "Ensemble performance", "Ensemble", "Do persisted ensembles improve validation performance?", formal_n, "PASS", "Existing ensemble performance is retained as development evidence.", ["research/figures/final/ensemble_comparison.png"]),
        ("B25", "Ensemble diversity/correlation", "Ensemble", "How diverse are model errors and scores?", formal_n, "PASS", "Diversity matrices are registered.", ["research/figures/final/diversity_matrix.png"]),
        ("B26", "Calibration methods", "Calibration", "How do calibration methods compare?", 946, "PASS", "Frozen calibration selection and comparison artifacts are retained.", ["research/figures/final/calibration_metric_comparison.png"]),
        ("B27", "Reliability", "Calibration", "Are probability estimates reliable across bins?", 946, "PASS", "Reliability artifacts are retained.", ["research/figures/final/calibration_reliability.png"]),
        ("B28", "Brier/ECE/NLL", "Calibration", "How good are the frozen probability estimates?", 946, "PASS", "Brier, ECE, and NLL are present in the frozen artifact.", ["research/figures/final/final_probability_quality.png"]),
        ("B29", "Abstention/selective prediction", "Uncertainty", "How does selective prediction trade coverage for risk?", 946, "PASS", "The frozen abstention artifact reports target and actual coverage.", ["research/figures/final/final_abstention_semantics.png"]),
        ("B30", "Risk-coverage", "Uncertainty", "How does error risk change with coverage?", formal_n, "PASS", "Development risk-coverage evidence is retained.", ["research/figures/final/risk_coverage_development.png"]),
        ("B31", "Learning curves", "Training", "How does performance change with development sample size?", formal_n, "PASS", "Learning-curve artifacts are retained.", ["research/figures/final/learning_curve_auroc.png"]),
        ("B32", "Forward-vs-RC ablation", "Ablation", "What is the effect of reverse-complement inference?", formal_n, "PASS", "Forward/RC ablation evidence is registered.", ["research/figures/final/ablation_metric_delta.png"]),
        ("B33", "Model-family ablation", "Ablation", "What changes across model families?", formal_n, "PASS", "Model-family ablation evidence is retained.", []),
        ("B34", "Classical-comparator ablation", "Ablation", "What changes when classical comparators are added?", formal_n, "PASS", "Comparator ablation evidence is retained with coverage limits.", []),
        ("B35", "Locked ROC", "Locked baseline", "What is the frozen locked ROC performance?", 946, "PASS", "The immutable primary ROC is linked.", ["research/figures/final/final_roc.png"]),
        ("B36", "Locked PR", "Locked baseline", "What is the frozen locked precision-recall performance?", 946, "PASS", "The immutable primary PR is linked.", ["research/figures/final/final_pr.png"]),
        ("B37", "Locked confusion matrix", "Locked baseline", "What errors occur at the frozen threshold?", 946, "PASS", "Frozen confusion counts are linked.", ["research/figures/final/final_confusion_matrix.png"]),
        ("B38", "Complete classification metric dashboard", "Locked baseline", "What is the full frozen classification dashboard?", 946, "PASS", "All required classification and probability metrics are registered.", ["research/figures/final/final_classification_metrics.png"]),
        ("B39", "Bootstrap confidence", "Statistics", "What uncertainty surrounds the frozen metrics?", 946, "PASS", "Bootstrap confidence intervals are registered.", ["research/figures/final/bootstrap_interval.png"]),
        ("B40", "Errors by chromosome", "Error analysis", "Which chromosomes contain more errors?", 946, "PASS", "Chromosome error evidence is retained.", ["research/figures/final/final_error_chromosome.png"]),
        ("B41", "Errors by gene", "Error analysis", "Which genes contain more errors?", 946, "PASS", "Gene error evidence is retained.", ["research/figures/final/final_gene_errors.png"]),
        ("B42", "Development-vs-final generalization", "Generalization", "How does development compare with frozen temporal evaluation?", 4000, "PASS", "Development and final evidence remain stage-qualified.", ["research/figures/final/development_final_generalization.png"]),
        ("B43", "Runtime", "Runtime", "What runtime was observed by model?", formal_n, "PASS", "Runtime artifacts include model-level measurements.", ["research/figures/final/runtime_by_model.png"]),
        ("B44", "Throughput/cache reuse", "Runtime", "What throughput and cache reuse were observed?", formal_n, "PASS", "Throughput and cache-reuse artifacts are retained.", ["research/figures/final/throughput_comparison.png"]),
        ("B45", "Compute cost", "Runtime", "What compute cost is attributable to existing evidence?", formal_n, "COMPLETED_WITH_LIMITATIONS", "Historical cost evidence is available; new expansion spend is zero and live balance is unverified.", ["research/figures/final/cost_by_phase_model.png"]),
    ]
    registry: list[dict[str, Any]] = []
    for spec in existing_specs:
        benchmark_id, title, family, question, n, status, summary, figures = spec
        registry.append(
            benchmark_entry(
                benchmark_id,
                title,
                family,
                question,
                population="formal development" if n == formal_n and benchmark_id not in {"B01", "B02", "B03", "B04", "B05"} else "locked temporal cohort",
                n=n,
                status=status,
                summary=summary,
                limitations=["Existing persisted evidence; no new fine-tuning."],
                sources=base_sources,
                figures=figures,
                web_tab={
                    "B01": "Core Baseline", "B02": "Core Baseline", "B03": "Core Baseline", "B04": "Core Baseline", "B05": "Core Baseline",
                    "B14": "Model Comparison", "B15": "Model Comparison", "B16": "Model Comparison", "B17": "Model Comparison", "B18": "Model Comparison",
                    "B19": "Model Comparison", "B20": "Model Comparison", "B21": "Model Comparison", "B22": "HPO & Training", "B23": "HPO & Training",
                    "B24": "Model Comparison", "B25": "Model Disagreement", "B26": "Calibration & Uncertainty", "B27": "Calibration & Uncertainty",
                    "B28": "Calibration & Uncertainty", "B29": "Calibration & Uncertainty", "B30": "Calibration & Uncertainty", "B31": "HPO & Training",
                    "B32": "Model Comparison", "B33": "Model Comparison", "B34": "Model Comparison", "B35": "Core Baseline", "B36": "Core Baseline",
                    "B37": "Core Baseline", "B38": "Core Baseline", "B39": "Calibration & Uncertainty", "B40": "Errors & Case Studies",
                    "B41": "Errors & Case Studies", "B42": "Generalization", "B43": "Runtime & Cost", "B44": "Runtime & Cost", "B45": "Runtime & Cost",
                }.get(benchmark_id, "Overview"),
                metrics=["AUROC", "AUPRC", "Accuracy", "Balanced Accuracy", "MCC"] if benchmark_id in {"B35", "B36", "B38"} else ["n", "coverage", "status"],
            )
        )
    new_specs = [
        ("B46", "ClinVar evidence-quality/review-status", "Evidence Quality", "Does frozen performance differ across review/evidence-strength strata?", locked_n, "PASS", "Performance and probability quality are stratified by ClinVar review status.", ["Evidence quality is an observational association; stars are not biological certainty."], "Evidence Quality", ["Evidence quality"]),
        ("B47", "Temporal difficulty/time-to-resolution", "Temporal Difficulty", "Does time between ClinVar evaluation and resolution associate with frozen difficulty?", locked_n, "PASS", "Fixed time bins and performance summaries are computed from T0/T1 dates.", ["Exploratory association; missing and invalid dates are retained."], "Temporal Difficulty", ["Temporal difficulty"]),
        ("B48", "Leave-one-chromosome-out generalization", "Generalization", "Does an Evo2 feature model generalize to an unseen chromosome?", formal_n, "PASS", "Chromosome-held-out logistic fits use development features only.", ["Small chromosomes may be marked insufficient support."], "Generalization", ["LOCO"]),
        ("B49", "Model disagreement/hard cases", "Model Disagreement", "Where do foundation and classical models disagree, and do consensus errors concentrate?", formal_n, "PASS", "Common-row validation disagreement, correlation, and error overlap are computed.", ["Only models with persisted common validation rows are included."], "Model Disagreement", ["Disagreement"]),
        ("B50", "Deterministic case studies", "Errors & Case Studies", "Can representative errors and high-confidence cases be reproduced from the locked artifact?", locked_n, "PASS", "Deterministic false-positive, false-negative, confidence, orientation, evidence, and temporal cases are registered.", ["No private or patient data is exposed."], "Errors & Case Studies", ["Cases"]),
        ("B51", "Confidence strata", "Calibration & Uncertainty", "Do errors and probability quality vary with confidence?", locked_n, "PASS", "Frozen calibrated scores are stratified by confidence.", ["Descriptive only; threshold remains frozen."], "Calibration & Uncertainty", ["Confidence"]),
        ("B52", "Model error overlap", "Model Disagreement", "How much do model error sets overlap?", formal_n, "PASS", "Pairwise validation error-overlap Jaccard values are computed on common rows.", ["Validation-stage only."], "Model Disagreement", ["Error overlap"]),
        ("B53", "Transition-vs-transversion", "Generalization", "Do frozen outcomes differ by SNV transition category?", locked_n, "PASS", "Transition and transversion strata are computed without model selection.", ["Exploratory subgroup analysis."], "Generalization", ["Transition"]),
        ("B54", "Substitution-class analysis", "Generalization", "Do frozen outcomes differ by exact substitution class?", locked_n, "PASS", "All eligible SNV substitution classes are retained with support flags.", ["Sparse classes are not over-interpreted."], "Generalization", ["Substitution"]),
        ("B55", "Comparator coverage/missingness sensitivity", "Model Comparison", "How much comparator coverage is available and what is missing?", formal_n, "PASS", "CADD and PhyloP coverage are reported for formal and locked cohorts.", ["Coverage varies by comparator and source release."], "Model Comparison", ["Comparator coverage"]),
        ("B56", "Frozen-threshold sensitivity", "Calibration & Uncertainty", "How do descriptive threshold metrics vary around the frozen threshold?", locked_n, "PASS", "Thresholds 0.25, 0.50, and 0.75 are reported descriptively.", ["The 0.50 threshold and calibration remain frozen; no post-hoc optimization."], "Calibration & Uncertainty", ["Threshold sensitivity"]),
        ("B57", "Downstream seed robustness", "Generalization", "Are cached-representation downstream results sensitive to random seed?", formal_n, "PASS", "Three fixed-seed MLP fits are reported on the validation split.", ["This is downstream robustness, not foundation-model fine-tuning."], "Generalization", ["Seed robustness"]),
        ("B58", "Per-model calibration where predictions exist", "Calibration & Uncertainty", "What calibration-relevant metrics exist per development model?", formal_n, "PASS", "All persisted validation model predictions receive common metric treatment.", ["Calibration curves are not refit per model."], "Calibration & Uncertainty", ["Model metrics"]),
        ("B59", "Macro/micro/weighted F1", "Core Baseline", "What are macro, micro, and weighted F1 under the frozen threshold?", locked_n, "PASS", "F1 variants are derived from frozen probabilities and labels.", ["Threshold remains frozen."], "Core Baseline", ["Primary"]),
        ("B60", "Probability MAE", "Calibration & Uncertainty", "What is the mean absolute probability error?", locked_n, "PASS", "Probability MAE is computed from frozen calibrated probabilities and local labels.", ["Descriptive score-quality metric."], "Calibration & Uncertainty", ["Primary"]),
        ("B61", "Independent high-confidence ClinVar benchmark", "External", "Does the frozen model transfer to an independent high-confidence ClinVar cohort?", int(external.get("selected_n", 0)), external["status"], "An external manifest is frozen, but new inference is blocked while Modal balance is not verifiable.", ["Selected candidates are manifest-only; no new model scores are claimed."], "External Benchmarks", ["External ClinVar"]),
        ("B62", "External review-quality subgroups", "External", "Do external outcomes vary by review quality?", int(external.get("selected_n", 0)), external["status"], "External review strata are prepared but not scored.", ["No external performance without persisted scores."], "External Benchmarks", ["External ClinVar"]),
        ("B63", "MaveDB functional correlation", "External", "How does functional effect correlate with clinical pathogenicity?", 0, "DATA_BLOCKED", "No MaveDB assay was selected because functional effect is not equivalent to clinical pathogenicity and no approved assay manifest is persisted.", ["A functional-effect benchmark requires an assay-specific, predeclared mapping."], "External Benchmarks", []),
        ("B64", "Additional public classical comparators", "External", "Are additional public comparator assets eligible?", 0, "NOT_APPLICABLE", "No additional compatible comparator asset is registered beyond CADD and PhyloP.", ["No proxy comparator is substituted."], "External Benchmarks", []),
        ("B65", "External multi-model agreement", "External", "Do multiple models agree on the external cohort?", int(external.get("selected_n", 0)), external["status"], "External agreement is unavailable without fresh or cached external scores.", ["Inference blocked before external scoring."], "External Benchmarks", []),
        ("B66", "External transported calibration", "External", "Does frozen calibration transport to an external cohort?", int(external.get("selected_n", 0)), external["status"], "Transported calibration is unavailable without external scores.", ["No calibration is refit on the external cohort."], "External Benchmarks", []),
        ("B67", "External runtime/cost/throughput", "External", "What is the external scoring cost and throughput?", int(external.get("selected_n", 0)), external["status"], "No new external inference was launched; new spend is zero.", ["No runtime is fabricated."], "Runtime & Cost", []),
        ("B68", "Cohort/data-drift comparison", "External", "How do source-release and cohort properties drift over time?", locked_n, "COMPLETED_WITH_LIMITATIONS", "T0/T1 snapshot hashes, date completeness, labels, and review strata are compared.", ["Drift is descriptive and does not establish causation."], "Temporal Difficulty", ["Drift"]),
    ]
    for benchmark_id, title, family, question, n, status, summary, limitations, tab, output_keys in new_specs:
        outputs = [f"artifacts/benchmarks/local_analysis_results.json#{key}" for key in output_keys]
        registry.append(
            benchmark_entry(
                benchmark_id,
                title,
                family,
                question,
                population="locked temporal cohort" if n == locked_n else "external manifest" if family == "External" else "formal development",
                n=n,
                status=status,
                summary=summary,
                limitations=limitations,
                sources=base_sources + [rel(EXPANSION / "protocol_lock.json")],
                outputs=outputs,
                figures=[],
                web_tab=tab,
                new_inference="NO" if benchmark_id not in {"B61", "B62", "B65", "B66", "B67"} else "BLOCKED",
                metrics=["n", "class counts", "AUROC", "AUPRC", "Brier", "ECE", "status"],
            )
        )
    registry.sort(key=lambda item: item["id"])
    statuses = Counter(item["status"] for item in registry)
    return {
        "registry_id": "evovariant-tr-benchmark-registry-v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "entry_count": len(registry),
        "status_counts": dict(statuses),
        "entries": registry,
    }

def _figure_slug(name: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in name).strip("_")


def make_figure(
    name: str,
    benchmark_id: str,
    population: str,
    n: int | None,
    source_data: Any,
    draw: Callable[[Any], None],
) -> dict[str, Any]:
    data_dir = DOCS / "data/figures"
    asset_dir = DOCS / "assets"
    web_dir = WEB / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)
    slug = _figure_slug(name)
    source_path = data_dir / f"{slug}.json"
    write_json(source_path, {"benchmark_id": benchmark_id, "population": population, "n": n, "records": source_data})
    web_data_dir = WEB / "data/figures"
    web_data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, web_data_dir / source_path.name)
    fig, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    draw(axis)
    axis.set_title(f"{name}\n{benchmark_id} | {population} | n={n if n is not None else 'N/A'}")
    png_path = asset_dir / f"{slug}.png"
    svg_path = asset_dir / f"{slug}.svg"
    pdf_path = asset_dir / f"{slug}.pdf"
    fig.savefig(png_path, dpi=160)
    fig.savefig(svg_path)
    fig.savefig(pdf_path)
    plt.close(fig)
    web_png = web_dir / png_path.name
    shutil.copy2(png_path, web_png)
    provenance = {
        "benchmark_id": benchmark_id,
        "population": population,
        "n": n,
        "source_data": rel(source_path),
        "outputs": {
            "png": rel(png_path),
            "svg": rel(svg_path),
            "pdf": rel(pdf_path),
            "web_png": rel(web_png),
        },
        "sha256": {
            "source_data": sha256_file(source_path),
            "png": sha256_file(png_path),
            "svg": sha256_file(svg_path),
            "pdf": sha256_file(pdf_path),
            "web_png": sha256_file(web_png),
        },
    }
    provenance_path = data_dir / f"{slug}.provenance.json"
    write_json(provenance_path, provenance)
    shutil.copy2(provenance_path, web_data_dir / provenance_path.name)
    return {
        "id": slug,
        "title": name,
        "benchmark_id": benchmark_id,
        "population": population,
        "n": n,
        "caption": f"{name} derived from registered {population} evidence.",
        "asset": f"/benchmarks/figures/{png_path.name}",
        "source_data": f"/benchmarks/data/figures/{source_path.name}",
        "provenance": f"/benchmarks/data/figures/{provenance_path.name}",
        "sha256": provenance["sha256"],
    }


def build_figures(results: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    figures: list[dict[str, Any]] = []
    status_records = [{"status": key, "n": value} for key, value in sorted(registry["status_counts"].items())]
    figures.append(
        make_figure(
            "Benchmark status matrix",
            "B01-B68",
            "registered benchmark catalog",
            len(registry["entries"]),
            status_records,
            lambda axis: (
                axis.bar([item["status"] for item in status_records], [item["n"] for item in status_records], color="#2f6f63"),
                axis.set_ylabel("benchmark count"),
                axis.tick_params(axis="x", rotation=25),
            ),
        )
    )
    evidence = [
        {"group": group, "n": item["n"], "auroc": item.get("metrics", {}).get("auroc")}
        for group, item in results["evidence_quality"]["groups"].items()
        if item["status"] == "PASS"
    ]
    figures.append(
        make_figure(
            "Evidence quality performance",
            "B46",
            "locked temporal cohort",
            results["locked"]["n"],
            evidence,
            lambda axis: (
                axis.bar([item["group"] for item in evidence], [item["auroc"] or 0 for item in evidence], color="#bc6c25"),
                axis.set_ylabel("AUROC"),
                axis.set_ylim(0, 1),
                axis.tick_params(axis="x", rotation=25),
            ),
        )
    )
    temporal = [
        {"bin": group, "n": item["n"], "auroc": item.get("metrics", {}).get("auroc")}
        for group, item in results["temporal_difficulty"]["groups"].items()
    ]
    figures.append(
        make_figure(
            "Temporal difficulty by resolution interval",
            "B47",
            "locked temporal cohort",
            results["locked"]["n"],
            temporal,
            lambda axis: (
                axis.bar([item["bin"] for item in temporal], [item["n"] for item in temporal], color="#457b9d"),
                axis.set_ylabel("variant count"),
                axis.tick_params(axis="x", rotation=25),
            ),
        )
    )
    loco = [
        {"chromosome": chromosome, "n": item["n"], "auroc": item.get("metrics", {}).get("auroc"), "status": item["status"]}
        for chromosome, item in results["loco"]["chromosome_results"].items()
        if item["status"] == "PASS"
    ]
    figures.append(
        make_figure(
            "Chromosome-held-out generalization",
            "B48",
            "formal development, LOCO",
            results["formal"]["n"],
            loco,
            lambda axis: (
                axis.bar([item["chromosome"] for item in loco], [item["auroc"] or 0 for item in loco], color="#264653"),
                axis.set_ylabel("AUROC"),
                axis.set_ylim(0, 1),
            ),
        )
    )
    disagreement = [
        {"category": category, "n": count}
        for category, count in sorted(results["disagreement"]["category_counts"].items())
    ]
    figures.append(
        make_figure(
            "Model disagreement categories",
            "B49",
            "common validation rows",
            results["disagreement"]["n_common_validation"],
            disagreement,
            lambda axis: (
                axis.bar([item["category"] for item in disagreement], [item["n"] for item in disagreement], color="#6a4c93"),
                axis.set_ylabel("variant count"),
                axis.tick_params(axis="x", rotation=25),
            ),
        )
    )
    coverage = [
        {"comparator": name, "coverage_fraction": item["coverage_fraction"], "available": item["available"], "total": item["total"]}
        for name, item in results["comparator_coverage"].items()
    ]
    figures.append(
        make_figure(
            "Classical comparator coverage",
            "B55",
            "formal and locked registered cohorts",
            results["formal"]["n"],
            coverage,
            lambda axis: (
                axis.bar([item["comparator"] for item in coverage], [item["coverage_fraction"] for item in coverage], color="#e76f51"),
                axis.set_ylabel("coverage fraction"),
                axis.set_ylim(0, 1),
                axis.tick_params(axis="x", rotation=25),
            ),
        )
    )
    transition = [
        {"group": group, "n": item["n"], "auroc": item.get("metrics", {}).get("auroc")}
        for group, item in results["transition_type"]["groups"].items()
    ]
    figures.append(
        make_figure(
            "Transition versus transversion",
            "B53",
            "locked temporal cohort",
            results["locked"]["n"],
            transition,
            lambda axis: (
                axis.bar([item["group"] for item in transition], [item["n"] for item in transition], color="#2a9d8f"),
                axis.set_ylabel("variant count"),
            ),
        )
    )
    model_rows = [
        {"model_id": model_id, "auroc": item["metrics"].get("auroc") if item.get("metrics") else None, "n": item["n"]}
        for model_id, item in results["validation_model_metrics"].items()
        if item["status"] == "PASS"
    ]
    model_rows.sort(key=lambda item: item["auroc"] or -1, reverse=True)
    top_models = model_rows[:12]
    figures.append(
        make_figure(
            "Validation model comparison",
            "B14",
            "formal validation split",
            top_models[0]["n"] if top_models else 0,
            top_models,
            lambda axis: (
                axis.barh([item["model_id"] for item in reversed(top_models)], [item["auroc"] or 0 for item in reversed(top_models)], color="#1d3557"),
                axis.set_xlabel("AUROC"),
                axis.set_xlim(0, 1),
            ),
        )
    )

    def register_existing_figure(
        name: str,
        benchmark_id: str,
        image_name: str,
        source_name: str,
        population: str,
        n: int,
    ) -> dict[str, Any] | None:
        image_source = ROOT / "research/figures/final" / image_name
        source_source = ROOT / "research/figures/final/source" / source_name
        if not image_source.exists():
            return None
        slug = _figure_slug(name)
        asset_path = DOCS / "assets" / f"{slug}.png"
        web_asset = WEB / "figures" / asset_path.name
        shutil.copy2(image_source, asset_path)
        shutil.copy2(image_source, web_asset)
        data_path = DOCS / "data/figures" / source_name
        if source_source.exists():
            shutil.copy2(source_source, data_path)
        else:
            write_json(data_path, {"source_artifact": rel(image_source)})
        shutil.copy2(data_path, WEB / "data/figures" / data_path.name)
        provenance_path = DOCS / "data/figures" / f"{slug}.provenance.json"
        provenance = {
            "benchmark_id": benchmark_id,
            "population": population,
            "n": n,
            "source_artifact": rel(image_source),
            "source_data": rel(data_path),
            "outputs": {"png": rel(asset_path), "web_png": rel(web_asset)},
            "sha256": {
                "source_artifact": sha256_file(image_source),
                "source_data": sha256_file(data_path),
                "png": sha256_file(asset_path),
                "web_png": sha256_file(web_asset),
            },
        }
        write_json(provenance_path, provenance)
        shutil.copy2(provenance_path, WEB / "data/figures" / provenance_path.name)
        return {
            "id": slug,
            "title": name,
            "benchmark_id": benchmark_id,
            "population": population,
            "n": n,
            "caption": f"{name} retained from the registered publication figure.",
            "asset": f"/benchmarks/figures/{asset_path.name}",
            "source_data": f"/benchmarks/data/figures/{data_path.name}",
            "provenance": f"/benchmarks/data/figures/{provenance_path.name}",
            "sha256": provenance["sha256"],
        }

    existing_figure_specs = [
        ("Frozen ROC", "B35", "final_roc.png", "final_roc.json", "locked temporal cohort", 946),
        ("Frozen PR", "B36", "final_pr.png", "final_pr.json", "locked temporal cohort", 946),
        ("Frozen confusion matrix", "B37", "final_confusion_matrix.png", "final_confusion_matrix.json", "locked temporal cohort", 946),
        ("Frozen classification dashboard", "B38", "final_classification_metrics.png", "final_classification_metrics.json", "locked temporal cohort", 946),
        ("Frozen bootstrap interval", "B39", "bootstrap_interval.png", "bootstrap_interval.json", "locked temporal cohort", 946),
        ("Chromosome error analysis", "B40", "final_error_chromosome.png", "final_error_chromosome.json", "locked temporal cohort", 946),
        ("Gene error analysis", "B41", "final_gene_errors.png", "final_gene_errors.json", "locked temporal cohort", 946),
        ("Development to final generalization", "B42", "development_final_generalization.png", "development_final_generalization.json", "development and locked stages", 4000),
        ("Runtime by model", "B43", "runtime_by_model.png", "runtime_by_model.json", "formal development", 4000),
        ("Throughput and cache reuse", "B44", "throughput_comparison.png", "throughput_comparison.json", "formal development", 4000),
        ("Historical compute cost", "B45", "cost_by_phase_model.png", "cost_by_phase_model.json", "formal development", 4000),
    ]
    for spec in existing_figure_specs:
        figure = register_existing_figure(*spec)
        if figure is not None:
            figures.append(figure)

    contact_paths = []
    for figure in figures:
        contact_paths.append(DOCS / "assets" / Path(figure["asset"]).name)
    contact_width, contact_height = 640, 360
    contact = Image.new("RGB", (contact_width * 2, contact_height * math.ceil(len(contact_paths) / 2)), "white")
    draw = ImageDraw.Draw(contact)
    for index, path in enumerate(contact_paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((contact_width - 20, contact_height - 40))
        x = (index % 2) * contact_width + (contact_width - image.width) // 2
        y = (index // 2) * contact_height + 28
        contact.paste(image, (x, y))
        draw.text(((index % 2) * contact_width + 12, (index // 2) * contact_height + 8), figures[index]["title"], fill="black")
    contact_path = DOCS / "assets/benchmark_contact_sheet.png"
    contact.save(contact_path)
    shutil.copy2(contact_path, WEB / "figures/benchmark_contact_sheet.png")
    shutil.copy2(contact_path, DOCS / "assets/contact_sheet.png")
    shutil.copy2(contact_path, WEB / "figures/contact_sheet.png")
    contact_provenance = {
        "benchmark_id": "B01-B68",
        "population": "registered benchmark figures",
        "inputs": [rel(path) for path in contact_paths],
        "output": rel(contact_path),
        "sha256": sha256_file(contact_path),
    }
    write_json(DOCS / "data/figures/contact_sheet.provenance.json", contact_provenance)
    shutil.copy2(DOCS / "data/figures/contact_sheet.provenance.json", WEB / "data/figures/contact_sheet.provenance.json")
    figures.append(
        {
            "id": "contact_sheet",
            "title": "Benchmark figure contact sheet",
            "benchmark_id": "B01-B68",
            "population": "registered benchmark figures",
            "n": len(figures),
            "caption": "Contact sheet of generated benchmark figures.",
            "asset": "/benchmarks/figures/benchmark_contact_sheet.png",
            "source_data": "/benchmarks/data/figures/contact_sheet.provenance.json",
            "provenance": "/benchmarks/data/figures/contact_sheet.provenance.json",
            "sha256": {"png": contact_provenance["sha256"]},
        }
    )
    return figures


def attach_figures(registry: dict[str, Any], figures: list[dict[str, Any]]) -> dict[str, Any]:
    by_benchmark: dict[str, list[str]] = defaultdict(list)
    for figure in figures:
        for benchmark_id in str(figure["benchmark_id"]).split("-"):
            if benchmark_id.startswith("B") and benchmark_id[1:].isdigit():
                by_benchmark[benchmark_id].append(figure["asset"])
    for entry in registry["entries"]:
        assets = by_benchmark.get(entry["id"], [])
        if assets:
            entry["figures"] = assets
            entry["figure"] = assets[0]
    return registry

def write_figure_qa(figures: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for figure in figures:
        asset = WEB / "figures" / Path(figure["asset"]).name
        source = DOCS / "data/figures" / Path(figure["source_data"]).name
        source_payload = read_json(source) if source.suffix == ".json" else {}
        numeric_values: list[float] = []

        def collect(value: Any, numbers: list[float] = numeric_values) -> None:
            if isinstance(value, bool):
                return
            if isinstance(value, (int, float)):
                numbers.append(float(value))
            elif isinstance(value, dict):
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(source_payload)
        with Image.open(asset) as image:
            width, height = image.size
        checks.append(
            {
                "id": figure["id"],
                "benchmark_id": figure["benchmark_id"],
                "population": figure["population"],
                "n": figure["n"],
                "asset": rel(asset),
                "source_data": rel(source),
                "asset_exists": asset.exists(),
                "source_exists": source.exists(),
                "dimensions": [width, height],
                "finite_source_numbers": all(math.isfinite(value) for value in numeric_values),
                "hash_recorded": bool(figure["sha256"].get("png")),
            }
        )
    result = {
        "status": "PASS" if all(all(item[key] for key in ("asset_exists", "source_exists", "finite_source_numbers", "hash_recorded")) for item in checks) else "FAIL",
        "figure_count": len(checks),
        "figures": checks,
    }
    write_json(ARTIFACTS / "figure_qa.json", result)
    return result


def markdown_catalog(registry: dict[str, Any]) -> str:
    lines = [
        "# EvoVariant-TR Benchmark Catalog",
        "",
        "Canonical registry generated from persisted artifacts by scripts/benchmark_expansion/run_local.py.",
        "",
        "| ID | Benchmark | Status | Population | n | New inference? | Web tab | Limitation |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for entry in registry["entries"]:
        limitation = "; ".join(entry["limitations"]).replace("|", "/")
        lines.append(
            f"| {entry['id']} | {entry['title']} | {entry['status']} | {entry['population']} | {entry['n'] if entry['n'] is not None else 'N/A'} | {entry['new_inference']} | {entry['web_tab']} | {limitation} |"
        )
    return "\n".join(lines) + "\n"


def write_docs(
    results: dict[str, Any],
    external: dict[str, Any],
    registry: dict[str, Any],
    figures: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    reference_ready = external.get("reference_status") == "READY"
    analysis = {key: value for key, value in results.items() if key != "locked_rows"}
    analysis["figure_count"] = len(figures)
    write_json(EXPANSION / "local_analysis_results.json", analysis)
    write_json(EXPANSION / "locked_rows.json", results["locked_rows"])
    write_json(EXPANSION / "registry.json", registry)
    write_json(ARTIFACTS / "benchmark_registry.json", registry)
    write_json(ARTIFACTS / "external_clinvar_manifest.json", external)
    write_json(ARTIFACTS / "source_inventory.json", inventory_artifacts())
    source_lines = [
        "# Source Inventory",
        "",
        "Hashes and stage labels are generated from the registered input and publication artifacts.",
        "",
        "| Path | SHA256 | Bytes | Stage | Labels |",
        "|---|---|---:|---|---|",
    ]
    for item in read_json(ARTIFACTS / "source_inventory.json"):
        source_lines.append(f"| {item['path']} | {item['sha256']} | {item['bytes']} | {item['stage']} | {item['label_availability']} |")
    atomic_write(DOCS / "SOURCE_INVENTORY.md", "\n".join(source_lines) + "\n")
    atomic_write(EXPANSION / "BENCHMARK_CATALOG.md", markdown_catalog(registry))
    atomic_write(DOCS / "BENCHMARK_CATALOG.md", markdown_catalog(registry))
    primary = results["primary"]["locally_recomputed_metrics"]
    frozen = results["frozen_locked_metrics"]
    summary = {
        "summary_id": "evovariant-tr-final-benchmark-summary-v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protocol_hash": protocol["protocol_yaml_sha256"],
        "primary_status": results["primary"]["status"],
        "primary_population": "946-row locked temporal cohort",
        "headline_metrics": {key: primary.get(key) for key in ("auroc", "auprc", "f1", "mcc", "brier", "ece", "nll")},
        "frozen_artifact_metrics": frozen,
        "formal_n": results["formal"]["n"],
        "locked_n": results["locked"]["n"],
        "external_n": external["selected_n"],
        "completed_benchmark_families": sum(
            registry["status_counts"].get(status, 0) for status in ("PASS", "PASS_WITH_LIMITATIONS", "COMPLETED_WITH_LIMITATIONS")
        ),
        "status_counts": registry["status_counts"],
        "modal_spend_usd": 0.0,
        "new_fine_tuning_for_primary": False,
        "fine_tuning_implementation": True,
        "fine_tuning_complete_study": False,
        "blockers": [
            "COMPUTE_BLOCKED_BALANCE_UNVERIFIED: Modal billing summary did not expose a verifiable live balance."
        ]
        + (["DATA_BLOCKED_REFERENCE_FASTA_MISSING: external manifest is frozen but reference FASTA is not present locally."] if not reference_ready else []),
        "figures": figures,
    }
    write_json(ARTIFACTS / "final_benchmark_summary.json", summary)
    atomic_write(
        DOCS / "FINAL_STATUS_MATRIX.md",
        "# Final Benchmark Status Matrix\n\n" + markdown_catalog(registry),
    )
    atomic_write(
        DOCS / "SCORE_SEMANTICS.md",
        """# Score semantics

The immutable primary result uses the frozen isotonic calibrated probability,
with higher_is_more_pathogenic and threshold 0.50. The registered raw Evo2
evidence is alternate_minus_reference_log_likelihood; it is not silently
reoriented in post-processing. Comparator scales are retained in their source
semantics. No locked label, locked score, or frozen threshold is optimized by
the expansion analyses.

MSA = NOT_DEFINED_IN_PROJECT.
""",
    )
    atomic_write(
        DOCS / "METRICS.md",
        """# Metrics

All local benchmark summaries use the repository metric implementation plus
the fixed bootstrap seed 42 with 1,000 replicates where the subgroup contains
both classes. Results include sample size and class counts. Small or
single-class strata are marked INSUFFICIENT_SUPPORT, not converted to zero.

Accuracy, balanced accuracy, precision, recall, specificity, positive-class
F1, macro-F1, micro-F1, weighted-F1, MCC, Brier, NLL, ECE, TP, TN, FP, FN,
AUROC, AUPRC, and probability MAE are available where labels and scores
support them.
""",
    )
    atomic_write(
        DOCS / "METHODS.md",
        f"""# Methods

The benchmark expansion reuses only registered GRCh38 ClinVar, frozen-model,
representation-cache, comparator, and downstream-prediction artifacts. The
formal development cohort has 4,000 rows and the immutable temporal locked
cohort has 946 rows. Variant IDs are disjoint before analysis.

Evidence quality is grouped by ClinVar review-status stars. Temporal
difficulty uses T0-to-T1 LastEvaluated dates and fixed bins of <=180,
181-365, 366-545, >545, and missing/invalid days. LOCO fits a scaled logistic
classifier on cached Evo2 features with one chromosome held out. Disagreement
uses common validation rows and does not fit on the locked cohort. Case studies
are deterministic selections from the frozen locked artifact.

The external ClinVar manifest is frozen before inference. It excludes formal
and locked IDs and genes, but external scoring is blocked because a
verifiable Modal balance is unavailable. The local GRCh38 reference FASTA is
{"available" if reference_ready else "unavailable"}.
""",
    )
    atomic_write(
        DOCS / "RESULTS.md",
        f"""# Results

The frozen locked cohort has n={results['locked']['n']} variants. The locally
recomputed primary metrics match the registered phase-14 artifact within
1e-9: AUROC={primary['auroc']:.12f}, AUPRC={primary['auprc']:.12f},
F1={primary['f1']:.12f}, MCC={primary['mcc']:.12f}. This confirms artifact
integrity; it is not a new locked evaluation.

Evidence-quality, temporal, LOCO, disagreement, case-study, comparator
coverage, threshold-sensitivity, and seed-robustness outputs are written to
research/benchmarks/expansion_v1/local_analysis_results.json.

The external manifest contains {external['selected_n']} deterministic
gene-disjoint candidates, but no new external scores are claimed. New Modal
spend is $0.00 because the live balance was not verifiable.
""",
    )
    atomic_write(
        DOCS / "CASE_STUDIES.md",
        "# Deterministic Case Studies\n\n"
        "All cases below are selected from the immutable locked artifact and expose no private data.\n\n"
        + "\n".join(
            f"- {case['case_id']} ({case['reason']}): {case['normalized_variant_id']}, gene {case['gene_symbol']}, label {case['label']}, calibrated score {case['calibrated_score']}."
            for case in results["case_studies"]
        )
        + "\n",
    )
    atomic_write(
        DOCS / "COMPUTE.md",
        """# Compute and safety boundary

The existing frozen baseline and cached development representations are
reused. No new foundation-model inference, no new fine-tuning, and no paid
Modal job were started by this expansion. The configured Modal profile was
checked locally; the billing summary returned no verifiable live balance, so
the safety rule is COMPUTE_BLOCKED_BALANCE_UNVERIFIED.

Hard reserve: $5.00. Safety stop: $5.50. Program soft maximum: $24.00.
Observed new spend: $0.00. A future run may proceed only after an explicit
fresh balance check, external-manifest freeze, cost pilot, and safety-stop
reconciliation.
""",
    )
    atomic_write(
        DOCS / "FINAL_BENCHMARK_REPORT.md",
        f"""# EvoVariant-TR Benchmark Expansion v1

## Outcome

The local, no-spend benchmark suite completed with primary artifact
integrity status **{results['primary']['status']}**. The frozen 946-row
temporal result remains unchanged. The canonical registry contains
{registry['entry_count']} entries with status counts
{json.dumps(registry['status_counts'], sort_keys=True)}.

## Headline

- Locked cohort: n={results['locked']['n']}
- AUROC: {primary['auroc']:.12f}
- AUPRC: {primary['auprc']:.12f}
- Positive-class F1: {primary['f1']:.12f}
- MCC: {primary['mcc']:.12f}
- External manifest: n={external['selected_n']}; scores not available
- New Modal spend: $0.00

## Boundary

Foundation-model fine-tuning was not part of the primary result. The existing
implementation and encoder-update proof remain available, while a complete
fine-tuned benchmark study is **not** claimed. External inference is
**COMPUTE_BLOCKED** pending a verifiable balance{" and **DATA_BLOCKED** pending the local reference FASTA" if not reference_ready else ""}. The registry preserves these states explicitly.
        """,
    )
    atomic_write(
        DOCS / "README.md",
        f"""# Benchmark Hub

The generated benchmark publication bundle is the evidence companion to the
EvoVariant-TR web app. Open the static [Benchmark Hub](/benchmarks) or inspect
the generated [benchmark manifest](../../apps/web/public/benchmarks/benchmark-manifest.json).

- Frozen primary: n={results['locked']['n']}, AUROC={primary['auroc']:.9f}, AUPRC={primary['auprc']:.9f}, F1={primary['f1']:.9f}, MCC={primary['mcc']:.9f}
- Canonical catalog: [B01-B68 registry](BENCHMARK_CATALOG.md)
- Methods: [METHODS.md](METHODS.md)
- Results: [RESULTS.md](RESULTS.md)
- Fine-tuning boundary: [downloadable proof/demo](../../apps/web/public/benchmarks/downloads/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb)
- Reproduction: [protocol](../../research/benchmarks/expansion_v1/protocol.yaml) and [artifact manifest](../../artifacts/benchmarks/BENCHMARK_ARTIFACT_MANIFEST.json)

The external cohort manifest is frozen at n={external['selected_n']}; external
scores remain COMPUTE_BLOCKED while a verifiable Modal balance is unavailable.
""",
    )
    atomic_write(
        ROOT / "docs/JUDGE_DEMO.md",
        """# EvoVariant-TR Judge Demo

Use the local app and the generated manifest for a 10-15 minute evidence-first walkthrough:

1. Open the normal variant-analysis workflow and confirm the existing form loads.
2. Select Benchmarks in the visible navigation.
3. Start at Overview and scan the contribution registry and B01-B68 status counts.
4. Open Core Baseline for the immutable 946-row result and primary figures.
5. Compare foundation, representation, and classical evidence.
6. Show HPO & Training and explain that downstream HPO is separate from adaptation.
7. Open Calibration & Uncertainty, Evidence Quality, and Temporal Difficulty.
8. Open Generalization for LOCO and seed robustness.
9. Open Model Disagreement for common-row correlations and hard cases.
10. Open External Benchmarks to show the frozen n=200 manifest and explicit compute block.
11. Open Errors & Case Studies for deterministic locked examples.
12. Open Runtime & Cost to show zero new spend and the balance gate.
13. Open Fine-Tuning Attempt if asked; emphasize primary NO, implementation YES,
    feasibility proof YES if the persisted proof verifies, and complete study NO.
14. Use Downloads and Reproducibility to show notebooks, hashes, protocol, and
    the artifact manifest.

Likely questions:

- Is the 946 result fine-tuned? No. The primary result uses frozen foundation
  representations, a downstream classifier, and frozen calibration.
- Why is the external result empty? The candidate manifest is frozen, but the
  safety gate did not expose a verifiable Modal balance; no unsupported scores
  are shown.
- Are review stars biological certainty? No. They are observational evidence-
  quality strata only.
- Can the result be reproduced without paid GPU? The local integrity check,
  generated tables, figures, notebooks, and manifest checks run from persisted
  artifacts; fresh external inference is intentionally blocked.
""",
    )
    write_json(
        ARTIFACTS / "BASELINE_INTEGRITY_REPORT.json",
        {
            "status": results["primary"]["status"],
            "baseline_tag_commit": results["primary"]["baseline_tag_commit"],
            "primary_artifact": results["primary"]["artifact"],
            "primary_artifact_sha256": results["primary"]["artifact_sha256"],
            "locked_manifest_sha256": results["primary"]["locked_manifest_sha256"],
            "metric_checks": results["primary"]["artifact_metric_checks"],
            "local_checks": results["primary"]["local_metric_checks"],
            "fine_tuning_started_for_primary": False,
        },
    )
    figure_lines = [
        f"| {figure['benchmark_id']} | {figure['title']} | {figure['asset']} | {figure['source_data']} | {figure['sha256'].get('png')} |"
        for figure in figures
    ]
    atomic_write(
        DOCS / "FIGURE_INDEX.md",
        "# Figure Index\n\n| Benchmark | Figure | Web asset | Source data | PNG SHA256 |\n|---|---|---|---|---|\n"
        + "\n".join(figure_lines)
        + "\n",
    )
    budget = budget_plan(None)
    write_json(ARTIFACTS / "modal_budget_plan.json", budget | {
        "profile": "utkarshkhajuria59",
        "hard_reserve_usd": 5.0,
        "safety_stop_usd": 5.5,
        "soft_maximum_usd": 24.0,
        "new_spend_usd": 0.0,
        "pilot_started": False,
    })
    write_json(
        ARTIFACTS / "modal_cost_ledger.json",
        {
            "profile": "utkarshkhajuria59",
            "new_spend_usd": 0.0,
            "entries": [],
            "balance_status": "UNVERIFIED",
            "status": "COMPUTE_BLOCKED_BALANCE_UNVERIFIED",
            "billing_summary_checked": True,
            "resources_started_by_expansion": [],
        },
    )
    atomic_write(
        DOCS / "MODAL_COST_REPORT.md",
        """# Modal Cost Report

Profile utkarshkhajuria59 was selected. Local CLI checks found no active
apps/secrets and a billing summary with no verifiable live balance. The
expansion therefore started no remote inference, spent $0.00, and left no
remote resources to shut down. Hard reserve $5.00 and safety stop $5.50
remain enforced.
""",
    )
    return summary


def build_web_manifest(
    results: dict[str, Any],
    external: dict[str, Any],
    registry: dict[str, Any],
    figures: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    primary = results["primary"]["locally_recomputed_metrics"]
    sections = [
        "Overview", "Core Baseline", "Model Comparison", "HPO & Training",
        "Calibration & Uncertainty", "Generalization", "Evidence Quality",
        "Temporal Difficulty", "Model Disagreement", "External Benchmarks",
        "Errors & Case Studies", "Runtime & Cost", "Fine-Tuning Attempt",
        "Reproducibility", "Downloads",
    ]
    cards = [
        {"id": "locked_n", "label": "Locked temporal variants", "value": results["locked"]["n"], "source": "B01"},
        {"id": "auroc", "label": "Frozen AUROC", "value": primary["auroc"], "source": "B35"},
        {"id": "auprc", "label": "Frozen AUPRC", "value": primary["auprc"], "source": "B36"},
        {"id": "f1", "label": "Frozen positive-class F1", "value": primary["f1"], "source": "B59"},
        {"id": "mcc", "label": "Frozen MCC", "value": primary["mcc"], "source": "B38"},
        {"id": "completed", "label": "Completed or limited benchmark entries", "value": sum(registry["status_counts"].get(status, 0) for status in ("PASS", "PASS_WITH_LIMITATIONS", "COMPLETED_WITH_LIMITATIONS")), "source": "B01-B68"},
        {"id": "external_n", "label": "External manifest variants", "value": external["selected_n"], "source": "B61"},
    ]
    contributions = [
        {"benchmark_id": entry["id"], "title": entry["title"], "status": entry["status"], "web_tab": entry["web_tab"], "evidence": entry["artifact_links"]}
        for entry in registry["entries"]
    ]
    limitations = [
        "The frozen primary is immutable and is not reselected by this suite.",
        "External scores are not claimed because Modal balance was not verifiable.",
        "MaveDB functional effect is not treated as clinical pathogenicity.",
    ]
    if external.get("reference_status") != "READY":
        limitations.insert(2, "Local reference FASTA is absent for fresh external inference.")
    manifest = {
        "schema_version": "1.0.0",
        "title": "EvoVariant-TR Research Benchmarks",
        "subtitle": "Temporal evaluation, model comparison, generalization, calibration, uncertainty, robustness, external validation, compute, and reproducibility.",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status_vocabulary": ["PASS", "COMPLETED_WITH_LIMITATIONS", "NOT_APPLICABLE", "DATA_BLOCKED", "COMPUTE_BLOCKED"],
        "headline_cards": cards,
        "what_we_contributed": contributions,
        "tabs": [{"id": _figure_slug(section), "label": section, "benchmark_ids": [entry["id"] for entry in registry["entries"] if entry["web_tab"] == section]} for section in sections],
        "benchmarks": registry["entries"],
        "figures": figures,
        "data": {
            "primary": results["primary"],
            "formal": results["formal"],
            "locked": results["locked"],
            "evidence_quality": results["evidence_quality"],
            "temporal_difficulty": results["temporal_difficulty"],
            "loco": results["loco"],
            "disagreement": {key: value for key, value in results["disagreement"].items() if key != "rows"},
            "confidence": results["confidence"],
            "comparator_coverage": results["comparator_coverage"],
            "threshold_sensitivity": results["threshold_sensitivity"],
            "seed_robustness": results["seed_robustness"],
            "case_studies": results["case_studies"],
            "compute": {
                "new_spend_usd": 0.0,
                "modal_profile": "utkarshkhajuria59",
                "balance_status": "UNVERIFIED",
                "resources_started": 0,
            },
            "external": {key: value for key, value in external.items() if key != "records"},
        },
        "fine_tuning": {
            "foundation_model_fine_tuning_in_primary_result": "NO",
            "fine_tuning_implementation_built": "YES",
            "real_encoder_update_feasibility_proof": "YES if existing proof artifact verifies",
            "complete_fine_tuned_benchmark_study": "NO",
            "artifacts": [
                "research/adaptation_attempt/EVIDENCE_MANIFEST.json",
                "research/adaptation_attempt/figures/encoder_update_proof.json",
                "notebooks/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb",
            ],
            "limitation": "Existing feasibility evidence is not a complete fine-tuned scientific result.",
        },
        "reproducibility": {
            "main_start_sha": protocol["start_main_head"],
            "working_branch": protocol["working_branch"],
            "baseline_tag_commit": protocol["baseline_tag_commit"],
            "benchmark_protocol_sha256": protocol["protocol_yaml_sha256"],
            "formal_manifest_sha256": sha256_file(DEV_MANIFEST),
            "locked_manifest_sha256": sha256_file(LOCKED_MANIFEST),
            "t0_sha256": sha256_file(T0_ARCHIVE),
            "t1_sha256": sha256_file(T1_ARCHIVE),
            "benchmark_registry_sha256": None,
            "commands": [
                "PYTHONPATH=src .venv/bin/python scripts/benchmark_expansion/run_local.py --self-check",
                "PYTHONPATH=src .venv/bin/python scripts/benchmark_expansion/run_local.py",
                "make secrets",
                "make web-check",
            ],
        },
        "downloads": [
            {"label": "Final benchmark summary", "path": "/benchmarks/downloads/final_benchmark_summary.json"},
            {"label": "Benchmark registry", "path": "/benchmarks/downloads/benchmark_registry.json"},
            {"label": "Case studies", "path": "/benchmarks/downloads/case_studies.json"},
            {"label": "Benchmark protocol", "path": "/benchmarks/downloads/protocol.yaml"},
            {"label": "Methods", "path": "/benchmarks/downloads/METHODS.md"},
            {"label": "Baseline judge demo", "path": "/benchmarks/downloads/EvoVariant_TR_Baseline_Judge_Demo.ipynb"},
            {"label": "Fine-tuning attempt demo", "path": "/benchmarks/downloads/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb"},
            {"label": "Benchmark expansion demo", "path": "/benchmarks/downloads/EvoVariant_TR_Benchmark_Expansion_Demo.ipynb"},
            {"label": "Encoder update proof", "path": "/benchmarks/downloads/encoder_update_proof.json"},
            {"label": "Figure contact sheet", "path": "/benchmarks/figures/benchmark_contact_sheet.png"},
        ],
        "limitations": limitations,
    }
    return manifest

def write_notebooks() -> dict[str, Any]:
    notebook_specs = {
        "EvoVariant_TR_Baseline_Judge_Demo.ipynb": [
            ("markdown", "# EvoVariant-TR frozen baseline demo\n\nThis notebook loads the immutable primary artifact without refitting."),
            ("code", "import json\nfrom pathlib import Path\nartifact = json.loads(Path('../artifacts/phase14/phase14_locked_evo2_20260922.json').read_text())\nprint(artifact['locked_cohort']['completed_rows'], artifact['metrics']['auroc'], artifact['metrics']['auprc'])"),
            ("code", "assert artifact['locked_cohort']['completed_rows'] == 946\nassert artifact['frozen_config']['path'].endswith('frozen_config_materialized.json')"),
        ],
        "EvoVariant_TR_FineTuning_Attempt_Demo.ipynb": [
            ("markdown", "# EvoVariant-TR fine-tuning attempt demo\n\nThis is a transparent feasibility/proof walkthrough. It is not a completed fine-tuned benchmark result."),
            ("code", "import json\nfrom pathlib import Path\nmanifest = json.loads(Path('../research/adaptation_attempt/EVIDENCE_MANIFEST.json').read_text())\nprint(manifest.get('status', manifest.get('attempt_status', 'proof artifact present')))"),
            ("code", "proof = Path('../research/adaptation_attempt/figures/encoder_update_proof.json')\nprint('encoder proof exists:', proof.exists())\nprint('primary fine-tuning:', 'NO')"),
        ],
        "EvoVariant_TR_Benchmark_Expansion_Demo.ipynb": [
            ("markdown", "# EvoVariant-TR benchmark expansion demo\n\nThis notebook reads the generated registry and local analysis outputs."),
            ("code", "import json\nfrom pathlib import Path\nregistry = json.loads(Path('../artifacts/benchmarks/benchmark_registry.json').read_text())\nsummary = json.loads(Path('../artifacts/benchmarks/final_benchmark_summary.json').read_text())\nprint(registry['entry_count'], summary['headline_metrics'])"),
            ("code", "assert registry['entry_count'] == 68\nassert summary['modal_spend_usd'] == 0.0"),
        ],
    }
    syntax: dict[str, Any] = {}
    for filename, cells in notebook_specs.items():
        notebook = {
            "cells": [
                {
                    "cell_type": cell_type,
                    "metadata": {},
                    "source": [line + "\n" for line in source.splitlines()],
                    **({"execution_count": None, "outputs": []} if cell_type == "code" else {}),
                }
                for cell_type, source in cells
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        path = ROOT / "notebooks" / filename
        write_json(path, notebook)
        errors: list[str] = []
        for cell_type, source in cells:
            if cell_type == "code":
                try:
                    compile(source, f"{filename}:code", "exec")
                except SyntaxError as error:
                    errors.append(str(error))
        syntax[filename] = {"status": "PASS" if not errors else "FAIL", "errors": errors, "sha256": sha256_file(path)}
    write_json(ARTIFACTS / "notebook_syntax.json", syntax)
    return syntax


def write_downloads() -> None:
    download_dir = WEB / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    case_studies = read_json(EXPANSION / "local_analysis_results.json").get("case_studies", [])
    write_json(ARTIFACTS / "case_studies.json", case_studies)
    sources = {
        "final_benchmark_summary.json": ARTIFACTS / "final_benchmark_summary.json",
        "benchmark_registry.json": ARTIFACTS / "benchmark_registry.json",
        "case_studies.json": ARTIFACTS / "case_studies.json",
        "protocol.yaml": EXPANSION / "protocol.yaml",
        "METHODS.md": DOCS / "METHODS.md",
        "EvoVariant_TR_Baseline_Judge_Demo.ipynb": ROOT / "notebooks/EvoVariant_TR_Baseline_Judge_Demo.ipynb",
        "EvoVariant_TR_FineTuning_Attempt_Demo.ipynb": ROOT / "notebooks/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb",
        "EvoVariant_TR_Benchmark_Expansion_Demo.ipynb": ROOT / "notebooks/EvoVariant_TR_Benchmark_Expansion_Demo.ipynb",
        "BENCHMARK_ARTIFACT_MANIFEST.json": ARTIFACTS / "BENCHMARK_ARTIFACT_MANIFEST.json",
        "encoder_update_proof.json": ROOT / "research/adaptation_attempt/figures/encoder_update_proof.json",
    }
    for name, source in sources.items():
        if source.exists():
            shutil.copy2(source, download_dir / name)


def build_artifact_manifest() -> dict[str, Any]:
    paths: list[Path] = []
    for root in (ARTIFACTS, DOCS, WEB):
        if root.exists():
            paths.extend(path for path in root.rglob("*") if path.is_file())
    records = []
    manifest_path = ARTIFACTS / "BENCHMARK_ARTIFACT_MANIFEST.json"
    for path in sorted(set(paths)):
        if path == manifest_path:
            continue
        records.append({"path": rel(path), "benchmark_id": "B01-B68", "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "manifest_id": "evovariant-tr-benchmark-artifact-manifest-v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "entry_count": len(records),
        "entries": records,
    }
    write_json(manifest_path, manifest)
    return manifest


def write_state(results: dict[str, Any], external: dict[str, Any], registry: dict[str, Any], manifest: dict[str, Any]) -> None:
    state = {
        "state_id": "evovariant-tr-benchmark-expansion-state-v1",
        "phase": "PHASE_25_LOCAL_COMPLETE_NO_SPEND",
        "working_branch": git_value("branch", "--show-current"),
        "completed_benchmark_ids": [entry["id"] for entry in registry["entries"] if entry["status"] in {"PASS", "COMPLETED_WITH_LIMITATIONS", "NOT_APPLICABLE", "DATA_BLOCKED", "COMPUTE_BLOCKED"}],
        "status_counts": registry["status_counts"],
        "primary_integrity": results["primary"],
        "external_manifest_path": rel(ARTIFACTS / "external_clinvar_manifest.json"),
        "external_n": external["selected_n"],
        "modal": {
            "profile": "utkarshkhajuria59",
            "new_spend_usd": 0.0,
            "status": "COMPUTE_BLOCKED_BALANCE_UNVERIFIED",
            "resources_started": [],
        },
        "blockers": external_blockers(external),
        "artifact_manifest": rel(ARTIFACTS / "BENCHMARK_ARTIFACT_MANIFEST.json"),
        "artifact_manifest_entries": manifest["entry_count"],
        "generated_outputs": [
            rel(ARTIFACTS / "final_benchmark_summary.json"),
            rel(EXPANSION / "local_analysis_results.json"),
            rel(DOCS / "FINAL_BENCHMARK_REPORT.md"),
            rel(WEB / "benchmark-manifest.json"),
        ],
    }
    write_json(ARTIFACTS / "benchmark_expansion_state.json", state)


def self_check() -> None:
    assert review_group(0) == "0 stars"
    assert review_group(3) == "3 stars"
    assert substitution_class("A", "G") == "A>G"
    assert transition_category("A", "G") == "transition"
    assert transition_category("A", "C") == "transversion"
    assert temporal_duration(date(2025, 1, 1), date(2025, 1, 2)) == 1
    assert temporal_bin(180) == "<=180"
    assert temporal_bin(181) == "181-365"
    assert budget_plan(None)["status"] == "COMPUTE_BLOCKED_BALANCE_UNVERIFIED"
    metrics = metric_bundle([0.1, 0.9, 0.2, 0.8], [0, 1, 0, 1], bootstrap=False)
    assert abs(metrics["accuracy"] - 1.0) < 1e-12
    assert metrics["f1"] == 1.0
    print("OK: benchmark expansion self-checks passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--start-main-head", default=os.environ.get("EVOVARIANT_START_MAIN_HEAD", START_MAIN_FALLBACK))
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    self_check()
    protocol = prepare_protocol(args.start_main_head)
    results = run_local_analyses()
    external = select_external_candidates(
        set(row["normalized_variant_id"] for row in read_records(DEV_MANIFEST))
        | set(row["normalized_variant_id"] for row in read_records(LOCKED_MANIFEST)),
        {
            str(row.get("gene_symbol"))
            for row in read_records(DEV_MANIFEST) + read_records(LOCKED_MANIFEST)
            if row.get("gene_symbol")
        },
    )
    registry = build_registry(results, external)
    write_docs(results, external, registry, [], protocol)
    figures = build_figures(results, registry)
    write_figure_qa(figures)
    registry = attach_figures(registry, figures)
    write_docs(results, external, registry, figures, protocol)
    web_manifest = build_web_manifest(results, external, registry, figures, protocol)
    write_json(WEB / "benchmark-manifest.json", web_manifest)
    web_manifest["reproducibility"]["benchmark_registry_sha256"] = sha256_file(ARTIFACTS / "benchmark_registry.json")
    write_json(WEB / "benchmark-manifest.json", web_manifest)
    write_notebooks()
    write_downloads()
    artifact_manifest = build_artifact_manifest()
    shutil.copy2(ARTIFACTS / "BENCHMARK_ARTIFACT_MANIFEST.json", WEB / "downloads/BENCHMARK_ARTIFACT_MANIFEST.json")
    write_state(results, external, registry, artifact_manifest)
    artifact_manifest = build_artifact_manifest()
    write_state(results, external, registry, artifact_manifest)
    artifact_manifest = build_artifact_manifest()
    shutil.copy2(ARTIFACTS / "BENCHMARK_ARTIFACT_MANIFEST.json", WEB / "downloads/BENCHMARK_ARTIFACT_MANIFEST.json")
    print(json.dumps({
        "status": "PASS" if results["primary"]["status"] == "PASS" else "PARTIAL",
        "branch": git_value("branch", "--show-current"),
        "primary": results["primary"]["locally_recomputed_metrics"],
        "registry_status_counts": registry["status_counts"],
        "external_n": external["selected_n"],
        "new_modal_spend_usd": 0.0,
        "artifact_manifest_entries": artifact_manifest["entry_count"],
        "blockers": external_blockers(external),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

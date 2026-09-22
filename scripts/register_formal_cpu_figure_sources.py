#!/usr/bin/env python3
"""Materialize and register preliminary figure sources from formal CPU outputs."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.registry import Registry, RegistryError, RunStatus, verify_output_hashes

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = REPO_ROOT / "research/runs/formal_cpu_20260922"
SOURCE_ROOT = RUN_ROOT / "figure_sources"
TITLE = "Formal CPU preliminary figure sources — 2026-09-22"
PROTOCOL_SHA256 = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> Path:
    path = SOURCE_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return path


def finite(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite figure value: {value!r}")
    return result


def selected_models(phase8: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in phase8["models"]
        if row["validation_count"] == 801
        and row["validation_metrics"].get("auroc") is not None
    ]


def curve_rows(
    model_id: str, rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scores = [finite(row["score"]) for row in rows]
    labels = [int(row["label"]) for row in rows]
    if not scores or len(set(labels)) != 2:
        raise ValueError(f"curve input is incomplete for {model_id}")
    thresholds = sorted(set(scores), reverse=True)
    roc = [{"model_id": model_id, "fpr": 0.0, "tpr": 0.0, "scope": "VALIDATION development"}]
    pr = [
        {
            "model_id": model_id,
            "recall": 0.0,
            "precision": 1.0,
            "scope": "VALIDATION development",
        }
    ]
    positives = sum(labels)
    negatives = len(labels) - positives
    for threshold in thresholds:
        predicted = [score >= threshold for score in scores]
        tp = sum(pred and label == 1 for pred, label in zip(predicted, labels, strict=True))
        fp = sum(pred and label == 0 for pred, label in zip(predicted, labels, strict=True))
        roc.append({
            "model_id": model_id,
            "fpr": fp / negatives,
            "tpr": tp / positives,
            "threshold": threshold,
            "scope": "VALIDATION development",
        })
        pr.append({
            "model_id": model_id,
            "recall": tp / positives,
            "precision": tp / (tp + fp) if tp + fp else 1.0,
            "threshold": threshold,
            "scope": "VALIDATION development",
        })
    return roc, pr


def materialize() -> list[Path]:
    phase8 = read(RUN_ROOT / "phase8/summary.json")
    phase9 = read(RUN_ROOT / "phase9/summary.json")
    phase11 = read(RUN_ROOT / "phase11/ensemble_analysis.json")
    phase12 = read(RUN_ROOT / "phase12/calibration_abstention.json")
    phase13 = read(RUN_ROOT / "phase13/ablations_learning_curves_robustness.json")
    phase7 = read(REPO_ROOT / "artifacts/phase7/formal_budgeted_representation_20260922.json")
    phase6 = read(
        REPO_ROOT
        / "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json"
    )
    manifest = read(
        REPO_ROOT
        / "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
    )
    models = selected_models(phase8)
    model_ids = {row["model_id"] for row in models}
    predictions: dict[str, list[dict[str, Any]]] = {model_id: [] for model_id in model_ids}
    for line in (RUN_ROOT / "phase8/development_predictions.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("split") == "VALIDATION" and row.get("model_id") in predictions:
            if row.get("locked_test_evaluated") is not False:
                raise ValueError("figure source prediction is not explicitly development-only")
            predictions[row["model_id"]].append(row)

    benchmark = []
    confusion = []
    roc: list[dict[str, Any]] = []
    pr: list[dict[str, Any]] = []
    for row in sorted(models, key=lambda item: item["model_id"]):
        metrics = row["validation_metrics"]
        ci = metrics.get("auroc_gene_clustered_ci95", {})
        benchmark.append({
            "model_id": row["model_id"],
            "auc_roc": finite(metrics["auroc"]),
            "auc_pr": finite(metrics["auprc"]),
            "auc_roc_ci_low": finite(ci["ci95_low"]) if ci else None,
            "auc_roc_ci_high": finite(ci["ci95_high"]) if ci else None,
            "sample_count": row["validation_count"],
            "scope": "formal TRAIN/VALIDATION development; full-coverage models only",
        })
        confusion.append({
            "model_id": row["model_id"],
            **{key: int(metrics["confusion_matrix"][key]) for key in ("tn", "fp", "fn", "tp")},
            "scope": "VALIDATION development",
        })
        curves = curve_rows(row["model_id"], predictions[row["model_id"]])
        roc.extend(curves[0])
        pr.extend(curves[1])

    calibration = []
    for method, rows in phase12["reliability"].items():
        calibration.extend(
            {
                "confidence": finite(row["confidence"]),
                "observed_frequency": finite(row["observed_frequency"]),
                "sample_count": int(row["count"]),
                "method": method,
                "scope": "VALIDATION development",
            }
            for row in rows
        )
    abstention = [
        {
            "coverage": finite(row["coverage"]),
            "risk": finite(row["risk"]),
            "sample_count": int(row["n_examples"]),
            "scope": "VALIDATION development",
        }
        for row in phase12["risk_coverage"]["points"]
        if math.isfinite(float(row["coverage"])) and math.isfinite(float(row["risk"]))
    ]

    embedding = []
    for feature_set, layer in {
        "nt8": 8,
        "nt16": 16,
        "nt24": 24,
        "cad4": 4,
        "cad8": 8,
        "cad16": 16,
    }.items():
        candidates = [row for row in models if row["feature_set"] == feature_set]
        if candidates:
            best = max(candidates, key=lambda row: row["validation_metrics"]["auroc"])
            embedding.append({
                "layer": layer,
                "metric": finite(best["validation_metrics"]["auroc"]),
                "model_id": best["model_id"],
                "feature_set": feature_set,
                "scope": "VALIDATION development; full-coverage feature families",
            })

    hpo = []
    for feature_set in sorted(phase9["studies"]):
        study = read(RUN_ROOT / f"phase9/{feature_set}/hpo.json")
        for trial in study["trials"]:
            hpo.append({
                "trial_id": f"{feature_set}::trial_{trial['trial_number']}",
                "objective": finite(trial["validation_metric"]),
                "feature_set": feature_set,
                "selection_split": "VALIDATION",
                **trial["config"],
                "scope": "bounded formal development HPO",
            })

    learning_curve = [
        {
            "train_size": int(row["train_count"]),
            "metric": finite(row["validation_metrics"]["auroc"]),
            "metric_name": "validation_auroc",
            "scope": "formal development learning curve",
        }
        for row in phase13["learning_curves"]
        if row["status"] == "COMPLETED"
    ]
    error_correlation = [
        {
            "model_id": f"{row['left_model']}__vs__{row['right_model']}",
            "error_correlation": finite(row["pearson_correlation"]),
            "disagreement_rate": finite(row["disagreement_rate"]),
            "scope": "VALIDATION development",
        }
        for row in phase11["diversity"]
    ]
    ensemble = []
    for name, payload in phase11["ensemble_methods"].items():
        metrics = payload.get("metrics", payload)
        ensemble.append({
            "model_id": name,
            "metric": finite(metrics["auroc"]),
            "metric_name": "validation_auroc",
            "scope": "VALIDATION development",
        })
    ablation = [
        {
            "component": row["ablation"],
            "metric": finite(row["metrics"]["auroc"]),
            "metric_name": "validation_auroc",
            "sample_count": int(row["metrics"]["n"]),
            "scope": "formal development ablation",
        }
        for row in phase13["ablation_results"]
    ]
    subgroup = [
        {
            "subgroup": row["subgroup"],
            "metric": finite(row["auroc"]),
            "metric_name": "gene_grouped_validation_auroc",
            "sample_count": int(row["sample_count"]),
            "scope": "VALIDATION development",
        }
        for row in phase13["subgroups"]
        if row.get("auroc") is not None
    ]
    dataset_flow = [
        {
            "stage": "formal_development",
            "count": len(manifest["records"]),
            "scope": "frozen manifest",
        },
        {
            "stage": "TRAIN",
            "count": sum(row["split"] == "TRAIN" for row in manifest["records"]),
            "scope": "frozen manifest",
        },
        {
            "stage": "VALIDATION",
            "count": sum(row["split"] == "VALIDATION" for row in manifest["records"]),
            "scope": "frozen manifest",
        },
        {
            "stage": "LOCKED_TEST_EXCLUDED",
            "count": 0,
            "scope": "development-only source",
        },
    ]
    split_composition = [
        {"split": split, "count": count, "scope": "formal development manifest"}
        for split, count in (("TRAIN", 3199), ("VALIDATION", 801))
    ]
    trained_models = [
        {
            "model_id": row["model_id"],
            "metric": finite(row["validation_metrics"]["auroc"]),
            "scope": "VALIDATION development",
        }
        for row in models
    ]
    limitations = [
        {"component": key, "reason": value["reason"], "scope": "formal development continuation"}
        for key, value in phase13["robustness"].items()
        if value.get("status") != "COMPLETED" and value.get("reason")
    ]
    model_registry = [
        {"model_id": model_id, "status": status, "scope": "project model registry"}
        for model_id, status in (
            ("evo2", "INCLUDED_RAW_SCORE"),
            ("nucleotide_transformer", "INCLUDED_EMBEDDING_TRACK"),
            ("caduceus", "INCLUDED_EMBEDDING_TRACK"),
            ("cadd", "SUBSET_ONLY"),
            ("phylop", "SUBSET_ONLY"),
        )
    ]
    cost = []
    for model_id, track in sorted(phase7["model_tracks"].items()):
        cost.append({
            "run_id": f"phase7-{model_id}",
            "measured_seconds": finite(track["runtime_seconds"]),
            "estimated_usd": finite(track["cost"]["estimated_client_wall_rate_usd"]),
            "scope": "formal development representation extraction",
        })
    cost.append({
        "run_id": "phase6-evo2-formal",
        "measured_seconds": finite(phase6["runtime"]["total_remote_wall_seconds"]),
        "estimated_usd": finite(phase6["cost"]["cumulative_client_wall_rate_estimate_usd"]),
        "scope": "formal development Evo2 scoring",
    })

    values = {
        "benchmark.json": benchmark,
        "roc.json": roc,
        "pr.json": pr,
        "confusion_matrix.json": confusion,
        "calibration.json": calibration,
        "abstention.json": abstention,
        "embedding_layer.json": embedding,
        "hpo.json": hpo,
        "learning_curve.json": learning_curve,
        "error_correlation.json": error_correlation,
        "ensemble.json": ensemble,
        "ablation.json": ablation,
        "subgroup.json": subgroup,
        "dataset_flow.json": dataset_flow,
        "split_composition.json": split_composition,
        "trained_models.json": trained_models,
        "model_registry.json": model_registry,
        "failures.json": limitations,
        "cost_ledger.jsonl": None,
    }
    paths = []
    for name, value in values.items():
        if name.endswith(".jsonl"):
            path = SOURCE_ROOT / name
            path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in cost),
                encoding="utf-8",
            )
        else:
            path = write(name, value)
        paths.append(path)
    return paths


def main() -> int:
    paths = materialize()
    registry = Registry(REPO_ROOT / "experiments/registry", repo_root=REPO_ROOT)
    existing = [record for record in registry.list_runs() if record.title == TITLE]
    if existing:
        if len(existing) != 1 or existing[0].status is not RunStatus.COMPLETED:
            raise RegistryError("figure-source registry title exists in a non-terminal state")
        verify_output_hashes(existing[0], REPO_ROOT)
        print(existing[0].run_id)
        return 0
    record = registry.register(
        title=TITLE,
        evidence_stage=EvidenceStage.PRELIMINARY,
        command=".venv/bin/python scripts/register_formal_cpu_figure_sources.py",
        protocol_hash=PROTOCOL_SHA256,
        data_manifests={"formal_development_manifest_sha256": MANIFEST_SHA256},
        model_identity="formal_cpu_figure_sources",
        scorer_config={"locked_test_evaluated": False, "selection_closed": True},
        comparator_versions={},
        seed=42,
        hardware={"execution": "local CPU"},
        experiment_family="FORMAL_CPU_FIGURES",
        dataset_manifest_hash=MANIFEST_SHA256,
        split_manifest_hash=MANIFEST_SHA256,
        model_name="Formal CPU development figure sources",
        checkpoint="formal_cpu_20260922",
        model_revision="development-artifacts",
        preprocessing_version="formal_8192bp_forward_rc_v1",
        feature_version="formal_cpu_20260922",
        config={"source_scope": "TRAIN/VALIDATION only", "locked_test_evaluated": False},
        gpu="CPU",
        estimated_cost_usd=0.0,
        notes=(
            "Derived only from hash-verified formal Phase 8–13 development artifacts. "
            "No FINAL or locked-test evidence; unavailable context-length, loss, temporal, "
            "and defensible HPO-importance families remain absent."
        ),
    )
    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[str(path.relative_to(REPO_ROOT)) for path in paths],
        outputs_base_dir=REPO_ROOT,
        metrics={"source_count": len(paths), "locked_test_evaluated": False},
    )
    print(completed.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

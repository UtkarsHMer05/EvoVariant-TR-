#!/usr/bin/env python3
"""Register the verified bounded development continuation as PRELIMINARY runs.

This command is deliberately narrow.  It consumes the already verified Phase 6
artifact and the local CPU continuation artifacts, writes small tracked
provenance summaries, and registers them as completed ``PRELIMINARY`` runs.
It never promotes a result to ``FINAL`` and never reads or registers
``LOCKED_TEST`` rows.

The full raw prediction/feature files remain regenerated run data under
``research/runs``.  The tracked summaries make the registry reproducible from
the repository while preserving the source-file hashes and the explicit
development-subset boundary.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from evovariant_tr.analysis_pipeline import load_prediction_rows
from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.registry import (
    Registry,
    RegistryError,
    RunRecord,
    RunStatus,
    verify_output_hashes,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase6_phase7_development_20260921.json"
PHASE6_PATH = REPO_ROOT / "artifacts/phase6/phase6_development_evo2_20260921.json"
FEATURE_SUMMARY_PATH = REPO_ROOT / (
    "research/runs/phase7_development_subset_20260921/evo2_raw_score_features.json"
)
PHASE8_PATH = REPO_ROOT / (
    "research/runs/phase8_development_subset_20260921/baselines/training_summary.json"
)
PREDICTIONS_PATH = REPO_ROOT / (
    "research/runs/phase8_development_subset_20260921/baselines/development_predictions.jsonl"
)
PHASE9_PATH = REPO_ROOT / ("research/runs/phase9_development_subset_20260921/hpo/hpo_metadata.json")
PHASE11_PATH = REPO_ROOT / (
    "research/runs/phase11_12_development_subset_20260921/equal_weight_logistic_mlp_analysis.json"
)
PHASE13_PATH = REPO_ROOT / (
    "research/runs/phase13_development_subset_20260921/ablation_robustness.json"
)
CALIBRATION_PATH = REPO_ROOT / (
    "research/runs/phase12_calibration_development_subset_20260921/calibration_comparison.json"
)
MODEL_DIR = REPO_ROOT / "research/ml_extension/models"
OUTPUT_ROOT = REPO_ROOT / "artifacts/registry/development_subset_20260921"
REGISTRY_ROOT = REPO_ROOT / "experiments/registry"


def read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return raw


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def write_stable_json(path: Path, payload: Any) -> None:
    """Create a tracked derived artifact, refusing to replace an existing one."""
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"existing derived artifact is not JSON: {path}") from exc
        if existing != payload:
            raise RuntimeError(f"derived artifact already exists with different content: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")


def require_source(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"required development artifact is missing: {path}")
    return sha256_file(path)


def checked_number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"expected finite number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"expected finite number, got {value!r}")
    return result


def validate_scope(phase6: dict[str, Any], feature_summary: dict[str, Any]) -> None:
    if phase6.get("status") != "PARTIAL_BUDGET_STOP":
        raise RuntimeError("Phase 6 artifact is not the verified bounded-budget result")
    boundary = phase6.get("scientific_boundary", {})
    if boundary.get("locked_test_labels_accessed") is not False:
        raise RuntimeError("Phase 6 locked-test boundary is not explicitly false")
    if boundary.get("labels_sent_to_modal") is not False:
        raise RuntimeError("Phase 6 remote-label boundary is not explicitly false")
    if boundary.get("full_development_cohort_complete") is not False:
        raise RuntimeError("Phase 6 must remain explicitly subset-only")
    if feature_summary.get("locked_test_evaluated") is not False:
        raise RuntimeError("feature summary does not prove locked-test exclusion")
    if feature_summary.get("labels_sent_to_modal") is not False:
        raise RuntimeError("feature summary does not prove remote-label exclusion")


def model_metrics(phase8: dict[str, Any]) -> dict[str, dict[str, float | int]]:
    models = phase8.get("models")
    if not isinstance(models, dict):
        raise RuntimeError("Phase 8 summary has no model metrics")
    result: dict[str, dict[str, float | int]] = {}
    for model_id, model in models.items():
        if not isinstance(model_id, str) or not isinstance(model, dict):
            raise RuntimeError("malformed Phase 8 model entry")
        metrics = model.get("validation_metrics")
        if not isinstance(metrics, dict):
            raise RuntimeError(f"missing validation metrics for {model_id}")
        result[model_id] = {
            key: (int(value) if isinstance(value, int) else checked_number(value))
            for key, value in metrics.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
    return result


def confusion_rows(metrics: dict[str, dict[str, float | int]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model_id, values in sorted(metrics.items()):
        n = int(values["n"])
        positive = int(values["n_positive"])
        negative = int(values["n_negative"])
        sensitivity = float(values["sensitivity"])
        specificity = float(values["specificity"])
        tp = round(sensitivity * positive)
        tn = round(specificity * negative)
        rows.append(
            {
                "model_id": model_id,
                "tn": tn,
                "fp": negative - tn,
                "fn": positive - tp,
                "tp": tp,
                "sample_count": n,
                "scope": "VALIDATION development subset",
            }
        )
    return rows


def curve_rows(
    rows: list[Any],
    *,
    model_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validation = [row for row in rows if row.split == "VALIDATION"]
    roc_rows: list[dict[str, Any]] = []
    pr_rows: list[dict[str, Any]] = []
    for model_id in model_ids:
        selected = [row for row in validation if row.model_id == model_id]
        if not selected or {row.label for row in selected} != {0, 1}:
            raise RuntimeError(f"curve source lacks both classes for {model_id}")
        ordered = sorted(selected, key=lambda row: (-row.score, row.normalized_variant_id))
        total_positive = sum(row.label for row in ordered)
        total_negative = len(ordered) - total_positive
        tp = 0
        fp = 0
        roc_rows.append({"model_id": model_id, "fpr": 0.0, "tpr": 0.0})
        pr_rows.append(
            {
                "model_id": model_id,
                "recall": 0.0,
                "precision": 1.0,
            }
        )
        for row in ordered:
            if row.label:
                tp += 1
            else:
                fp += 1
            roc_rows.append(
                {
                    "model_id": model_id,
                    "fpr": fp / total_negative,
                    "tpr": tp / total_positive,
                }
            )
            pr_rows.append(
                {
                    "model_id": model_id,
                    "recall": tp / total_positive,
                    "precision": tp / (tp + fp) if tp + fp else 1.0,
                }
            )
    return roc_rows, pr_rows


def reliability_rows(rows: list[Any]) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.split == "VALIDATION" and row.model_id in {"logistic_regression", "mlp"}
    ]
    by_id: dict[str, Any] = {}
    for row in selected:
        by_id.setdefault(row.normalized_variant_id, {})[row.model_id] = row
    ensemble = []
    for identity, pair in sorted(by_id.items()):
        if set(pair) != {"logistic_regression", "mlp"}:
            continue
        score = (pair["logistic_regression"].score + pair["mlp"].score) / 2.0
        ensemble.append((identity, score, pair["logistic_regression"].label))
    if not ensemble:
        raise RuntimeError("no aligned ensemble validation rows for calibration")
    result: list[dict[str, Any]] = []
    for bin_index in range(10):
        low = bin_index / 10.0
        high = (bin_index + 1) / 10.0
        members = [
            row for row in ensemble if low <= row[1] < high or (bin_index == 9 and row[1] == 1.0)
        ]
        if not members:
            continue
        result.append(
            {
                "bin": bin_index,
                "confidence": sum(row[1] for row in members) / len(members),
                "observed_frequency": sum(row[2] for row in members) / len(members),
                "sample_count": len(members),
                "method": "fixed_50_50_logistic_mlp",
                "scope": "VALIDATION development subset",
            }
        )
    return result


def source_artifacts(
    *,
    approval: dict[str, Any],
    phase6: dict[str, Any],
    feature_summary: dict[str, Any],
    phase8: dict[str, Any],
    phase9: dict[str, Any],
    phase11: dict[str, Any],
    phase13: dict[str, Any],
    prediction_rows: list[Any],
) -> dict[str, Path]:
    metrics = model_metrics(phase8)
    source_dir = OUTPUT_ROOT / "figure_sources"
    phase6_dataset = phase6["dataset"]
    processed_counts = phase6_dataset["processed_split_counts"]
    roc, pr = curve_rows(prediction_rows, model_ids=sorted(metrics))

    ensemble_metrics = phase11.get("metrics")
    if not isinstance(ensemble_metrics, dict):
        raise RuntimeError("Phase 11 artifact has no ensemble metrics")

    write_stable_json(
        source_dir / "dataset_flow.json",
        [
            {
                "stage": "full_development_cohort",
                "count": phase6_dataset["full_development_records"],
                "scope": "approved development manifest",
            },
            {
                "stage": "processed_prefix",
                "count": phase6_dataset["processed_records"],
                "scope": "bounded budget stop",
            },
            {
                "stage": "remaining_development_records",
                "count": phase6_dataset["remaining_records"],
                "scope": "not scored",
            },
            {
                "stage": "locked_test_excluded",
                "count": 0,
                "scope": "no locked rows in the registered subset",
            },
        ],
    )
    write_stable_json(
        source_dir / "split_composition.json",
        [
            {"split": split, "count": count, "scope": "processed development prefix"}
            for split, count in sorted(processed_counts.items())
        ],
    )
    write_stable_json(
        source_dir / "model_registry.json",
        [
            {
                "model_id": payload["model_id"],
                "status": payload["status"],
                "scope": "project model registry; not a benchmark result",
            }
            for payload in sorted(
                (read_json(path) for path in MODEL_DIR.glob("*.json")),
                key=lambda item: item["model_id"],
            )
        ],
    )
    write_stable_json(
        source_dir / "trained_models.json",
        [
            {
                "model_id": model_id,
                "metric": values["auroc"],
                "auprc": values["auprc"],
                "sample_count": values["n"],
                "scope": "VALIDATION development subset",
            }
            for model_id, values in sorted(metrics.items())
        ],
    )
    write_stable_json(source_dir / "roc.json", roc)
    write_stable_json(source_dir / "pr.json", pr)
    write_stable_json(source_dir / "confusion_matrix.json", confusion_rows(metrics))
    write_stable_json(source_dir / "calibration.json", reliability_rows(prediction_rows))
    write_stable_json(
        source_dir / "abstention.json",
        [
            {
                "coverage": checked_number(point["coverage"]),
                "risk": checked_number(point["risk"]),
                "sample_count": int(point["n_examples"]),
                "scope": "VALIDATION development subset; fixed ensemble diagnostic",
            }
            for point in phase11["calibration"]["risk_coverage"]["points"]
        ],
    )
    write_stable_json(
        source_dir / "ensemble.json",
        [
            {
                "model_id": model_id,
                "metric": checked_number(values["auroc"]),
                "metric_name": "validation_auroc",
                "scope": "VALIDATION development subset",
            }
            for model_id, values in sorted(metrics.items())
        ]
        + [
            {
                "model_id": "fixed_50_50_logistic_mlp",
                "metric": checked_number(ensemble_metrics["auroc"]),
                "metric_name": "validation_auroc",
                "scope": "VALIDATION development subset; weights fixed before analysis",
            }
        ],
    )
    write_stable_json(
        source_dir / "hpo.json",
        [
            {
                "trial_id": f"trial_{phase9['best_trial']['trial_number']}",
                "objective": checked_number(phase9["best_trial"]["validation_metric"]),
                "selection_split": "VALIDATION",
                "scope": "bounded development HPO; best completed trial summary",
                **phase9["best_trial"]["config"],
            }
        ],
    )
    write_stable_json(
        source_dir / "learning_curve.json",
        [
            {
                "train_size": int(point["train_count"]),
                "metric": checked_number(point["validation_metrics"]["auroc"]),
                "metric_name": "validation_auroc",
                "scope": "Phase 13 development subset learning curve",
            }
            for point in phase13["learning_curves"]
        ],
    )

    ablation_rows: list[dict[str, Any]] = []
    for component, payload in sorted(phase13["orientation_and_feature_variants"].items()):
        ablation_rows.append(
            {
                "component": component,
                "metric": checked_number(payload["validation_metrics"]["auroc"]),
                "metric_name": "validation_auroc",
                "scope": "Phase 13 feasible development subset cell",
            }
        )
    for payload in phase13["predeclared_ablation_matrix"]:
        if payload.get("status") != "COMPLETED":
            continue
        ablation_rows.append(
            {
                "component": payload["ablation_id"],
                "metric": checked_number(payload["validation_metrics"]["auroc"]),
                "metric_name": "validation_auroc",
                "scope": "Phase 13 feasible development subset cell",
            }
        )
    write_stable_json(source_dir / "ablation.json", ablation_rows)

    write_stable_json(
        source_dir / "failures.json",
        [
            {"component": component, "reason": reason, "scope": "current approved subset"}
            for component, reason in sorted(phase13["deferred"].items())
        ],
    )

    return {path.name: path for path in sorted(source_dir.glob("*.json"))}


def summary_artifacts(
    *,
    approval: dict[str, Any],
    phase6: dict[str, Any],
    feature_summary: dict[str, Any],
    phase8: dict[str, Any],
    phase9: dict[str, Any],
    phase11: dict[str, Any],
    phase13: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, Path]:
    protocol_hash = str(approval["protocol"]["sha256"])
    manifest_hash = str(approval["dataset"]["development_manifest_sha256"])
    phase6_hash = sha256_file(PHASE6_PATH)
    feature_hash = sha256_file(FEATURE_SUMMARY_PATH)
    phase8_hash = sha256_file(PHASE8_PATH)
    phase9_hash = sha256_file(PHASE9_PATH)
    phase11_hash = sha256_file(PHASE11_PATH)
    phase13_hash = sha256_file(PHASE13_PATH)
    calibration_hash = sha256_file(CALIBRATION_PATH)
    base = OUTPUT_ROOT

    payloads: dict[str, dict[str, Any]] = {
        "phase7_development_subset_20260921.json": {
            "artifact_id": "phase7-development-evo2-raw-score-features-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 7,
            "status": feature_summary["status"],
            "protocol_hash": protocol_hash,
            "development_manifest_sha256": manifest_hash,
            "source_artifact": relative(FEATURE_SUMMARY_PATH),
            "source_artifact_sha256": feature_hash,
            "phase6_artifact": relative(PHASE6_PATH),
            "phase6_artifact_sha256": phase6_hash,
            "model_id": feature_summary["model_id"],
            "feature_names": feature_summary["feature_names"],
            "records": feature_summary["records"],
            "split_counts": feature_summary["split_counts"],
            "locked_test_evaluated": False,
            "labels_sent_to_modal": False,
            "selection_boundary": feature_summary["selection_boundary"],
        },
        "phase8_development_subset_20260921.json": {
            "artifact_id": "phase8-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 8,
            "status": phase8["status"],
            "protocol_hash": protocol_hash,
            "source_artifact": relative(PHASE8_PATH),
            "source_artifact_sha256": phase8_hash,
            "feature_artifact": phase8["inputs"]["feature_artifact"],
            "feature_artifact_sha256": phase8["inputs"]["feature_artifact_sha256"],
            "models": model_metrics(phase8),
            "selection_split": phase8["selection_split"],
            "locked_test_evaluated": False,
            "scope": "processed development prefix only; no full-cohort claim",
        },
        "phase9_development_subset_20260921.json": {
            "artifact_id": "phase9-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 9,
            "status": phase9["status"],
            "protocol_hash": protocol_hash,
            "source_artifact": relative(PHASE9_PATH),
            "source_artifact_sha256": phase9_hash,
            "best_trial": phase9["best_trial"],
            "search_space_size": len(phase9["search_space"]),
            "selection_split": phase9["selection_split"],
            "locked_test_evaluated": False,
            "scope": "bounded validation-only HPO on processed development prefix",
        },
        "phase11_12_development_subset_20260921.json": {
            "artifact_id": "phase11-12-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": "11-12",
            "status": phase11["status"],
            "protocol_hash": protocol_hash,
            "source_artifact": relative(PHASE11_PATH),
            "source_artifact_sha256": phase11_hash,
            "models": phase11["models"],
            "weights": phase11["weights"],
            "metrics": phase11["metrics"],
            "selection_split": phase11["selection_split"],
            "locked_test_evaluated": False,
            "scope": "fixed-weight validation-only ensemble and abstention diagnostics",
        },
        "phase13_development_subset_20260921.json": {
            "artifact_id": "phase13-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 13,
            "status": phase13["status"],
            "protocol_hash": protocol_hash,
            "source_artifact": relative(PHASE13_PATH),
            "source_artifact_sha256": phase13_hash,
            "completed_orientation_cells": sorted(phase13["orientation_and_feature_variants"]),
            "completed_learning_curve_points": len(phase13["learning_curves"]),
            "deferred_cells": phase13["deferred"],
            "selection_split": phase13["selection_split"],
            "locked_test_evaluated": False,
            "scope": "feasible development-subset matrix only; deferred cells remain explicit",
        },
        "phase12_calibration_development_subset_20260921.json": {
            "artifact_id": "phase12-calibration-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 12,
            "status": calibration["status"],
            "protocol_hash": protocol_hash,
            "source_artifact": relative(CALIBRATION_PATH),
            "source_artifact_sha256": calibration_hash,
            "models": calibration["models"],
            "weights": calibration["weights"],
            "fit_count": calibration["fit_count"],
            "evaluation_count": calibration["evaluation_count"],
            "methods": calibration["methods"],
            "validation_metrics": calibration["validation_metrics"],
            "selection_split": calibration["selection_split"],
            "evaluation_split": calibration["evaluation_split"],
            "locked_test_evaluated": False,
            "selection_boundary": calibration["selection_boundary"],
        },
        "phase13_calibration_effect_20260921.json": {
            "artifact_id": "phase13-calibration-effect-development-subset-20260921",
            "evidence_stage": "PRELIMINARY",
            "phase": 13,
            "status": "COMPLETED_DEVELOPMENT_SUBSET",
            "protocol_hash": protocol_hash,
            "source_artifact": relative(CALIBRATION_PATH),
            "source_artifact_sha256": calibration_hash,
            "component": "calibration",
            "methods_compared": ["uncalibrated", "platt", "isotonic"],
            "validation_metrics": calibration["validation_metrics"],
            "selection_split": calibration["selection_split"],
            "locked_test_evaluated": False,
            "scope": "calibration effect on the fixed development-subset ensemble",
        },
    }
    result: dict[str, Path] = {}
    for filename, payload in payloads.items():
        path = base / filename
        write_stable_json(path, payload)
        result[filename] = path
    return result


def register_completed(
    registry: Registry,
    *,
    title: str,
    experiment_family: str,
    output_paths: list[Path],
    protocol_hash: str,
    manifest_hash: str,
    model_name: str | None,
    model_identity: str | None,
    model_revision: str | None,
    command: str,
    config: dict[str, Any],
    metrics: dict[str, Any] | None,
    estimated_cost_usd: float | None,
    notes: str,
) -> RunRecord:
    relative_outputs = sorted(relative(path) for path in output_paths)
    matching = [record for record in registry.list_runs() if record.title == title]
    if matching:
        if len(matching) != 1:
            raise RegistryError(f"duplicate registry titles already exist: {title}")
        record = matching[0]
        if record.status is not RunStatus.COMPLETED:
            raise RegistryError(f"existing registry record is not terminal: {record.run_id}")
        if list(record.output_paths) != relative_outputs:
            raise RegistryError(f"existing registry output paths differ: {title}")
        verify_output_hashes(record, REPO_ROOT)
        return record

    record = registry.register(
        title=title,
        evidence_stage=EvidenceStage.PRELIMINARY,
        command=command,
        protocol_hash=protocol_hash,
        data_manifests={"development_manifest_sha256": manifest_hash},
        model_identity=model_identity,
        scorer_config={"selection_closed": False, "locked_test_evaluated": False},
        comparator_versions={"registry_script": "2026-09-21"},
        seed=42,
        hardware={"execution": "local CPU/control-plane"},
        experiment_family=experiment_family,
        dataset_manifest_hash=manifest_hash,
        split_manifest_hash=manifest_hash,
        model_name=model_name,
        checkpoint="evo2_7b" if model_identity == "evo2_7b" else None,
        model_revision=model_revision,
        model_source="https://github.com/ArcInstitute/evo2"
        if model_identity == "evo2_7b"
        else None,
        license_record={"license": "Apache-2.0"} if model_identity == "evo2_7b" else {},
        preprocessing_version="raw_score_orientation_v1" if model_identity == "evo2_7b" else None,
        feature_version="development_subset_summary_v1",
        config=config,
        gpu="H100" if experiment_family == "ZS" else "CPU",
        estimated_cost_usd=estimated_cost_usd,
        notes=notes,
    )
    return registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=relative_outputs,
        outputs_base_dir=REPO_ROOT,
        metrics=metrics or {},
        notes=notes,
    )


def main() -> int:
    approval = read_json(APPROVAL_PATH)
    phase6 = read_json(PHASE6_PATH)
    feature_summary = read_json(FEATURE_SUMMARY_PATH)
    phase8 = read_json(PHASE8_PATH)
    phase9 = read_json(PHASE9_PATH)
    phase11 = read_json(PHASE11_PATH)
    phase13 = read_json(PHASE13_PATH)
    calibration = read_json(CALIBRATION_PATH)
    for path in (
        APPROVAL_PATH,
        PHASE6_PATH,
        FEATURE_SUMMARY_PATH,
        PHASE8_PATH,
        PHASE9_PATH,
        PHASE11_PATH,
        PHASE13_PATH,
        CALIBRATION_PATH,
        PREDICTIONS_PATH,
    ):
        require_source(path)
    validate_scope(phase6, feature_summary)
    for phase in (phase8, phase9, phase11, phase13):
        if phase.get("locked_test_evaluated") is not False:
            raise RuntimeError("a downstream artifact does not explicitly exclude LOCKED_TEST")
    if calibration.get("locked_test_evaluated") is not False:
        raise RuntimeError("calibration artifact does not explicitly exclude LOCKED_TEST")

    protocol_hash = str(approval["protocol"]["sha256"])
    manifest_hash = str(approval["dataset"]["development_manifest_sha256"])
    revision = str(approval["model"]["revision"])
    prediction_rows = load_prediction_rows(PREDICTIONS_PATH)
    summaries = summary_artifacts(
        approval=approval,
        phase6=phase6,
        feature_summary=feature_summary,
        phase8=phase8,
        phase9=phase9,
        phase11=phase11,
        phase13=phase13,
        calibration=calibration,
    )
    sources = source_artifacts(
        approval=approval,
        phase6=phase6,
        feature_summary=feature_summary,
        phase8=phase8,
        phase9=phase9,
        phase11=phase11,
        phase13=phase13,
        prediction_rows=prediction_rows,
    )

    registry = Registry(REGISTRY_ROOT, repo_root=REPO_ROOT)
    command = "python scripts/register_development_subset_results.py"
    records = [
        register_completed(
            registry,
            title="Phase 6 bounded Evo2 development prefix — 2026-09-21",
            experiment_family="ZS",
            output_paths=[PHASE6_PATH],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Evo2 7B",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "scope": "bounded TRAIN/VALIDATION prefix",
                "processed_records": phase6["dataset"]["processed_records"],
            },
            metrics=None,
            estimated_cost_usd=phase6["cost"]["cumulative_client_wall_rate_estimate_usd"],
            notes=(
                "PRELIMINARY only: 2,848-row development prefix; full cohort "
                "incomplete; no locked labels; no Phase 14 claim."
            ),
        ),
        register_completed(
            registry,
            title="Phase 7 Evo2 raw-score feature adapter — 2026-09-21",
            experiment_family="REP",
            output_paths=[summaries["phase7_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Evo2 7B",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "feature_layer": feature_summary["layer"],
                "records": feature_summary["records"],
            },
            metrics=None,
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: local raw-score adapter summary; not an "
                "NT/Caduceus embedding cache and not full cohort."
            ),
        ),
        register_completed(
            registry,
            title="Phase 8 development-subset baselines — 2026-09-21",
            experiment_family="CLF",
            output_paths=[summaries["phase8_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Evo2-derived CPU baselines",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "models": sorted(phase8["models"]),
                "selection_split": phase8["selection_split"],
            },
            metrics={
                "validation_auroc": {
                    key: value["auroc"] for key, value in model_metrics(phase8).items()
                }
            },
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: validation metrics on processed development "
                "prefix; no locked-test or confirmatory claim."
            ),
        ),
        register_completed(
            registry,
            title="Phase 9 bounded development-subset HPO — 2026-09-21",
            experiment_family="HPO",
            output_paths=[summaries["phase9_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Evo2-derived logistic baseline",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "search_space_size": len(phase9["search_space"]),
                "selection_split": phase9["selection_split"],
            },
            metrics={"best_validation_auroc": phase9["best_trial"]["validation_metric"]},
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: bounded validation-only search; best "
                "configuration is not frozen for locked evaluation."
            ),
        ),
        register_completed(
            registry,
            title="Phases 11-12 fixed development-subset ensemble diagnostics — 2026-09-21",
            experiment_family="ENS_CAL_ABS",
            output_paths=[summaries["phase11_12_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Fixed 50/50 logistic + MLP",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={"weights": phase11["weights"], "selection_split": phase11["selection_split"]},
            metrics={"validation": phase11["metrics"]},
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: fixed validation-only ensemble, calibration "
                "diagnostics, and risk-coverage; no locked selection."
            ),
        ),
        register_completed(
            registry,
            title=(
                "Phase 13 feasible development-subset ablation and robustness matrix — 2026-09-21"
            ),
            experiment_family="ABL_ROB",
            output_paths=[summaries["phase13_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Evo2-derived CPU baselines",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={"selection_split": phase13["selection_split"], "status": phase13["status"]},
            metrics={"completed_learning_curve_points": len(phase13["learning_curves"])},
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: feasible orientation/feature cells and "
                "learning curves; deferred cells remain explicit."
            ),
        ),
        register_completed(
            registry,
            title="Phase 12 train-only Platt and isotonic calibration — 2026-09-21",
            experiment_family="CAL",
            output_paths=[summaries["phase12_calibration_development_subset_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Fixed 50/50 logistic + MLP calibration",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "fit_split": calibration["selection_split"],
                "evaluation_split": calibration["evaluation_split"],
                "methods": ["uncalibrated", "platt", "isotonic"],
            },
            metrics={"validation": calibration["validation_metrics"]},
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: Platt and isotonic maps fit on TRAIN and "
                "evaluated on VALIDATION; no locked-test selection."
            ),
        ),
        register_completed(
            registry,
            title="Phase 13 calibration-effect development subset — 2026-09-21",
            experiment_family="ABL_ROB",
            output_paths=[summaries["phase13_calibration_effect_20260921.json"]],
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Fixed 50/50 logistic + MLP calibration",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "fit_split": calibration["selection_split"],
                "evaluation_split": calibration["evaluation_split"],
            },
            metrics={"validation": calibration["validation_metrics"]},
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY only: calibration-effect ablation on the development "
                "subset; full-cohort robustness remains incomplete."
            ),
        ),
        register_completed(
            registry,
            title="Phase 17 preliminary registry source bundle — 2026-09-21",
            experiment_family="FIG",
            output_paths=list(sources.values()),
            protocol_hash=protocol_hash,
            manifest_hash=manifest_hash,
            model_name="Development-subset source bundle",
            model_identity="evo2_7b",
            model_revision=revision,
            command=command,
            config={
                "source_scope": "PRELIMINARY development subset",
                "locked_test_evaluated": False,
            },
            metrics=None,
            estimated_cost_usd=0.0,
            notes=(
                "PRELIMINARY source inputs only: registry figure gate must remain "
                "blocked until every required source artifact exists."
            ),
        ),
    ]

    print(
        json.dumps(
            {
                "status": "PASS",
                "evidence_stage": "PRELIMINARY",
                "registered_or_verified_runs": [
                    {
                        "run_id": record.run_id,
                        "title": record.title,
                        "artifacts": len(record.output_paths),
                    }
                    for record in records
                ],
                "generated_summary_count": len(summaries),
                "generated_figure_source_count": len(sources),
                "locked_test_evaluated": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

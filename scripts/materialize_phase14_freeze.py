#!/usr/bin/env python3
"""Materialize the already-selected Phase 14 model using development evidence only."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.analysis_plans import freeze_analysis_config  # noqa: E402
from evovariant_tr.downstream_pipeline import load_training_feature_rows  # noqa: E402
from evovariant_tr.metrics import compute_auc_roc  # noqa: E402
from evovariant_tr.prediction_calibration import fit_isotonic  # noqa: E402
from evovariant_tr.supervised import fit_logistic_regression  # noqa: E402

RUN_ROOT = REPO_ROOT / "research/runs/formal_cpu_20260922"
PHASE13_ROOT = RUN_ROOT / "phase13"
FEATURE_PATH = REPO_ROOT / "research/runs/phase13_formal_evo2_20260922/combined_evo2_features_v2.jsonl"
FEATURE_METADATA_PATH = FEATURE_PATH.with_suffix(".metadata.json")
OLD_CONFIG_PATH = PHASE13_ROOT / "frozen_config.json"
OLD_FREEZE_PATH = PHASE13_ROOT / "pre_phase14_freeze.json"
PHASE8_PATH = RUN_ROOT / "phase8/summary.json"
PHASE9_HPO_PATH = RUN_ROOT / "phase9/evo2/hpo.json"
PHASE11_PATH = RUN_ROOT / "phase11/ensemble_analysis.json"
PHASE12_PATH = RUN_ROOT / "phase12/calibration_abstention.json"
PHASE13_PATH = PHASE13_ROOT / "ablations_learning_curves_robustness.json"
PHASE6_PATH = REPO_ROOT / "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json"
TRAIN_MANIFEST = REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921/formal_train_manifest.json"
VALIDATION_MANIFEST = REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921/formal_validation_manifest.json"
DEVELOPMENT_MANIFEST = REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
LOCKED_MANIFEST = "research/ml_extension/splits/authoritative_locked_test_manifest.json"

EXPECTED_OLD_CONFIG_SHA256 = "3ab606a1e351b536f3c32ce45da956f844904ec704963f88f1cdc256d7d77424"
EXPECTED_TRAIN_MANIFEST_SHA256 = "32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1"
EXPECTED_VALIDATION_MANIFEST_SHA256 = "b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b"
EXPECTED_DEVELOPMENT_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: object) -> None:
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


def main() -> int:
    old_config = read_json(OLD_CONFIG_PATH)
    old_freeze = read_json(OLD_FREEZE_PATH)
    if freeze_analysis_config(old_config).sha256 != EXPECTED_OLD_CONFIG_SHA256:
        raise ValueError("the original frozen configuration hash changed")
    if old_freeze.get("config_sha256") != EXPECTED_OLD_CONFIG_SHA256:
        raise ValueError("the original pre-Phase-14 freeze does not bind its expected hash")
    if old_config.get("selection_closed") is not True:
        raise ValueError("the original selection is not closed")

    for path, expected in (
        (TRAIN_MANIFEST, EXPECTED_TRAIN_MANIFEST_SHA256),
        (VALIDATION_MANIFEST, EXPECTED_VALIDATION_MANIFEST_SHA256),
        (DEVELOPMENT_MANIFEST, EXPECTED_DEVELOPMENT_MANIFEST_SHA256),
    ):
        if sha256_file(path) != expected:
            raise ValueError(f"development manifest hash changed: {path}")

    phase9_hpo = read_json(PHASE9_HPO_PATH)
    best_trial = phase9_hpo.get("best_trial")
    if not isinstance(best_trial, dict) or best_trial != old_config.get("hpo"):
        raise ValueError("Phase 9 best trial differs from the selected freeze")
    params = best_trial.get("config")
    if not isinstance(params, dict):
        raise ValueError("selected HPO trial has no classifier parameters")
    hpo_seed = phase9_hpo.get("seed")
    if hpo_seed != 42:
        raise ValueError("selected HPO seed is not the recorded seed 42")

    train, validation, feature_metadata = load_training_feature_rows(FEATURE_PATH)
    if len(train) != 3199 or len(validation) != 801:
        raise ValueError("the selected Evo2 feature artifact has unexpected split counts")
    if feature_metadata.get("feature_artifact_sha256") != sha256_file(FEATURE_PATH):
        raise ValueError("feature metadata hash does not match the feature artifact")
    metadata = read_json(FEATURE_METADATA_PATH)
    if metadata.get("locked_test_count") != 0 or metadata.get("status") != "PASS_FORMAL_CPU_FEATURE_COMBINATION":
        raise ValueError("feature metadata does not prove a development-only artifact")

    model = fit_logistic_regression(train, seed=42, **params)
    validation_scores = [float(model.predict_proba(row.features)) for row in validation]
    validation_auc = compute_auc_roc(validation_scores, [row.label for row in validation])
    expected_auc = float(best_trial["validation_metric"])
    if abs(validation_auc - expected_auc) > 1e-12:
        raise ValueError(f"selected HPO validation replay changed: {validation_auc} != {expected_auc}")

    phase12 = read_json(PHASE12_PATH)
    if phase12.get("model_id") != old_config.get("model_id"):
        raise ValueError("Phase 12 calibration model does not match the selected model")
    if phase12.get("methods", {}).get("isotonic") != fit_isotonic(
        [float(model.predict_proba(row.features)) for row in train], [row.label for row in train]
    ):
        raise ValueError("Phase 12 isotonic mapping does not replay from TRAIN")

    phase6 = read_json(PHASE6_PATH)
    model_contract = phase6.get("model")
    if not isinstance(model_contract, dict) or model_contract.get("revision") != EXPECTED_MODEL_REVISION:
        raise ValueError("Phase 6 does not bind the approved Evo2 revision")
    if model_contract.get("context_length_bp") != 8192 or model_contract.get("gpu") != "H100":
        raise ValueError("Phase 6 model contract is not the approved H100/8192 contract")

    model_artifact = {
        "artifact_id": "phase14-development-fitted-model-evo2-logistic-regression-hpo-20260922",
        "status": "PASS_PHASE14_DEVELOPMENT_MODEL_MATERIALIZATION",
        "phase": 14,
        "locked_test_evaluated": False,
        "model_id": old_config["model_id"],
        "classifier": "logistic_regression",
        "fit_scope": "TRAIN only; VALIDATION used only for the already-recorded HPO objective",
        "parameters": {
            "kind": "logistic_regression",
            "weights": list(model.weights),
            "bias": model.bias,
            "seed": model.seed,
            "steps": model.steps,
        },
        "hpo": {
            "study_artifact": str(PHASE9_HPO_PATH.relative_to(REPO_ROOT)),
            "study_artifact_sha256": sha256_file(PHASE9_HPO_PATH),
            "best_trial": best_trial,
            "selection_seed": hpo_seed,
        },
        "input": {
            "feature_artifact": str(FEATURE_PATH.relative_to(REPO_ROOT)),
            "feature_artifact_sha256": sha256_file(FEATURE_PATH),
            "feature_metadata": str(FEATURE_METADATA_PATH.relative_to(REPO_ROOT)),
            "feature_metadata_sha256": sha256_file(FEATURE_METADATA_PATH),
            "feature_names": old_config["feature_names"],
            "train_count": len(train),
            "validation_count": len(validation),
            "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        },
        "validation_replay": {
            "auroc": validation_auc,
            "expected_auroc": expected_auc,
            "tolerance": 1e-12,
            "status": "PASS",
        },
        "source_protocol": {
            "formal_manifest_sha256": EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
            "record_set_sha256": EXPECTED_RECORD_SET_SHA256,
            "locked_manifest_sha256": EXPECTED_LOCKED_MANIFEST_SHA256,
        },
    }
    model_artifact_path = PHASE13_ROOT / "fitted_model_evo2_logistic_regression_hpo.json"
    atomic_json(model_artifact_path, model_artifact)

    protocol_paths = {
        "research_protocol": REPO_ROOT / "research/protocol/protocol.yaml",
        "ml_extension_protocol": REPO_ROOT / "research/ml_extension/protocol.yaml",
    }
    calibration_path = PHASE12_PATH
    source_artifacts = {
        "phase8_summary": str(PHASE8_PATH.relative_to(REPO_ROOT)),
        "phase9_hpo": str(PHASE9_HPO_PATH.relative_to(REPO_ROOT)),
        "phase11_ensemble": str(PHASE11_PATH.relative_to(REPO_ROOT)),
        "phase12_calibration_abstention": str(PHASE12_PATH.relative_to(REPO_ROOT)),
        "phase13_robustness": str(PHASE13_PATH.relative_to(REPO_ROOT)),
        "phase6_model_contract": str(PHASE6_PATH.relative_to(REPO_ROOT)),
    }
    phase12_abstention = phase12.get("abstention")
    if not isinstance(phase12_abstention, dict):
        raise ValueError("Phase 12 has no abstention analysis")
    config = {
        "config_version": "phase14-materialized-v1",
        "phase": "PRE_PHASE14_FREEZE_MATERIALIZED",
        "selection_closed": True,
        "locked_test_evaluated": False,
        "post_test_tuning_allowed": False,
        "source_freeze_config_sha256": EXPECTED_OLD_CONFIG_SHA256,
        "model_id": old_config["model_id"],
        "base_models": [old_config["model_id"]],
        "feature_set": "evo2",
        "feature_names": old_config["feature_names"],
        "preprocessing": {
            "transform": "identity",
            "feature_order": old_config["feature_names"],
            "missing_values": "reject",
            "nonfinite_values": "reject",
        },
        "model": {
            "classifier": "logistic_regression",
            "fit_scope": "TRAIN",
            "artifact_path": str(model_artifact_path.relative_to(REPO_ROOT)),
            "artifact_sha256": sha256_file(model_artifact_path),
            "hpo": best_trial,
        },
        "calibration": {
            "method": "isotonic",
            "fit_scope": "TRAIN",
            "artifact_path": str(calibration_path.relative_to(REPO_ROOT)),
            "artifact_sha256": sha256_file(calibration_path),
            "mapping_key": "methods.isotonic",
        },
        "abstention": {
            "method": "confidence_rank",
            "coverage": float(phase12_abstention["coverage_threshold"]),
            "selection_split": "VALIDATION",
            "confidence_definition": "0.5 + 0.5 * abs(tanh(raw_score / 10.0))",
            "diagnostics_artifact": str(calibration_path.relative_to(REPO_ROOT)),
            "diagnostics_artifact_sha256": sha256_file(calibration_path),
        },
        "score_direction": old_config["score_direction"],
        "score_threshold": old_config["score_threshold"],
        "threshold_source": "predeclared_calibrated_probability_cutoff",
        "bootstrap": {"replicates": old_config["bootstrap_replicates"], "seed": 42},
        "seeds": {
            "hpo_selection": hpo_seed,
            "classifier_fit": model.seed,
            "calibration_fit": None,
            "calibration_application": None,
            "bootstrap": 42,
            "paired_comparisons": 42,
            "deterministic_without_seed": ["isotonic_fit", "isotonic_application", "abstention_rank"] ,
        },
        "model_contract": {
            "model_id": model_contract["model_id"],
            "checkpoint": model_contract["checkpoint"],
            "revision": model_contract["revision"],
            "assembly": "GRCh38",
            "context_length_bp": model_contract["context_length_bp"],
            "orientation": model_contract["orientation"],
            "score_semantics": model_contract["score_semantics"],
            "gpu": model_contract["gpu"],
        },
        "data": {
            "formal_train_manifest": {
                "path": str(TRAIN_MANIFEST.relative_to(REPO_ROOT)),
                "sha256": EXPECTED_TRAIN_MANIFEST_SHA256,
            },
            "formal_validation_manifest": {
                "path": str(VALIDATION_MANIFEST.relative_to(REPO_ROOT)),
                "sha256": EXPECTED_VALIDATION_MANIFEST_SHA256,
            },
            "formal_development_manifest": {
                "path": str(DEVELOPMENT_MANIFEST.relative_to(REPO_ROOT)),
                "sha256": EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
            },
            "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
            "locked_test_manifest": {
                "path": LOCKED_MANIFEST,
                "sha256": EXPECTED_LOCKED_MANIFEST_SHA256,
                "expected_count": 946,
                "expected_label_counts": {"0": 536, "1": 410},
                "labels_accessed_during_materialization": False,
            },
        },
        "feature_provenance": {
            "artifact_path": str(FEATURE_PATH.relative_to(REPO_ROOT)),
            "artifact_sha256": sha256_file(FEATURE_PATH),
            "metadata_path": str(FEATURE_METADATA_PATH.relative_to(REPO_ROOT)),
            "metadata_sha256": sha256_file(FEATURE_METADATA_PATH),
            "source_feature_artifacts": metadata.get("source_feature_artifacts", {}),
            "comparators": {"required": False, "used": False, "reason": "feature_set=evo2"},
        },
        "protocol_hashes": {
            name: {"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256_file(path)}
            for name, path in protocol_paths.items()
        },
        "phase_artifacts": {
            name: {"path": path, "sha256": sha256_file(REPO_ROOT / path)}
            for name, path in source_artifacts.items()
        },
        "required_remote_tracks": ["evo2"],
        "not_required_remote_tracks": ["nucleotide_transformer", "caduceus"],
    }
    frozen = freeze_analysis_config(config)
    config_path = PHASE13_ROOT / "frozen_config_materialized.json"
    atomic_json(config_path, config)
    freeze_path = PHASE13_ROOT / "pre_phase14_materialized_freeze.json"
    atomic_json(
        freeze_path,
        {
            "status": "PASS_PRE_PHASE14_FREEZE_MATERIALIZED",
            "selection_closed": True,
            "locked_test_evaluated": False,
            "config_path": str(config_path.relative_to(REPO_ROOT)),
            "config_sha256": frozen.sha256,
            "source_freeze_config_sha256": EXPECTED_OLD_CONFIG_SHA256,
            "model_artifact_path": str(model_artifact_path.relative_to(REPO_ROOT)),
            "model_artifact_sha256": sha256_file(model_artifact_path),
            "locked_test_manifest_rows_read": False,
            "locked_test_labels_accessed": False,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_PRE_PHASE14_FREEZE_MATERIALIZED",
                "config": str(config_path.relative_to(REPO_ROOT)),
                "config_sha256": frozen.sha256,
                "model_artifact": str(model_artifact_path.relative_to(REPO_ROOT)),
                "model_artifact_sha256": sha256_file(model_artifact_path),
                "validation_auroc": validation_auc,
                "locked_test_manifest_rows_read": False,
                "locked_test_labels_accessed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Register the formal CPU continuation as one immutable PRELIMINARY run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.registry import Registry, RegistryError, RunStatus, verify_output_hashes

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT = REPO_ROOT / "research/runs/formal_cpu_20260922"
TITLE = "Formal 4,000-row CPU development continuation — 2026-09-22"
PROTOCOL_SHA256 = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    phase8 = read(ROOT / "phase8/summary.json")
    phase9 = read(ROOT / "phase9/summary.json")
    phase11 = read(ROOT / "phase11/ensemble_analysis.json")
    phase12 = read(ROOT / "phase12/calibration_abstention.json")
    phase13 = read(ROOT / "phase13/ablations_learning_curves_robustness.json")
    freeze = read(ROOT / "phase13/pre_phase14_freeze.json")
    outputs = [
        ROOT / "phase8/summary.json",
        ROOT / "phase8/leakage_audit.json",
        ROOT / "phase9/summary.json",
        ROOT / "phase11/ensemble_analysis.json",
        ROOT / "phase12/calibration_abstention.json",
        ROOT / "phase13/ablations_learning_curves_robustness.json",
        ROOT / "phase13/pre_phase14_freeze.json",
    ]
    if any(not path.is_file() for path in outputs):
        raise ValueError("formal CPU output set is incomplete")
    registry = Registry(REPO_ROOT / "experiments/registry", repo_root=REPO_ROOT)
    existing = [record for record in registry.list_runs() if record.title == TITLE]
    if existing:
        if len(existing) != 1 or existing[0].status is not RunStatus.COMPLETED:
            raise RegistryError("formal CPU registry title exists in a non-terminal state")
        verify_output_hashes(existing[0], REPO_ROOT)
        print(existing[0].run_id)
        return 0
    best = max(phase8["models"], key=lambda row: float(row["validation_metrics"]["auroc"]))
    record = registry.register(
        title=TITLE,
        evidence_stage=EvidenceStage.PRELIMINARY,
        command=".venv/bin/python scripts/run_formal_cpu_pipeline.py",
        protocol_hash=PROTOCOL_SHA256,
        data_manifests={"formal_development_manifest_sha256": MANIFEST_SHA256},
        model_identity="formal_multi_model_development",
        scorer_config={
            "selection_closed": True,
            "locked_test_evaluated": False,
            "final_model_id": freeze["config"]["model_id"],
        },
        comparator_versions={
            "cadd": "99621fa5d91e3409bc5433157381c4cb917ed3925a895a9132b716b01254d834",
            "phylop": "733c33f4150b84ec4a8ba7aa56ca8bff9131c5cc6c5bd552ad8f435f192ed90f",
        },
        seed=42,
        hardware={"execution": "local CPU"},
        experiment_family="FORMAL_CPU",
        dataset_manifest_hash=MANIFEST_SHA256,
        split_manifest_hash=MANIFEST_SHA256,
        model_name="Evo2/NT/Caduceus formal representation comparison",
        checkpoint="evo2_7b",
        model_revision="4b509ec2a22d6de472659f908bcb0714265ad3a7",
        preprocessing_version="formal_8192bp_forward_rc_v1",
        feature_version="formal_cpu_20260922",
        config={"frozen_config_sha256": freeze["config_sha256"]},
        gpu="CPU",
        estimated_cost_usd=0.0,
        notes=(
            "Formal TRAIN/VALIDATION only; labels attached locally; no locked rows. "
            "Phase 10 is DEFERRED_BY_COMPUTE and Phase 14 remains unopened."
        ),
    )
    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[str(path.relative_to(REPO_ROOT)) for path in outputs],
        outputs_base_dir=REPO_ROOT,
        metrics={
            "phase8_best_validation_auroc": best["validation_metrics"]["auroc"],
            "phase8_best_validation_auprc": best["validation_metrics"]["auprc"],
            "phase9_status": phase9["status"],
            "phase11_status": phase11["status"],
            "phase12_status": phase12["status"],
            "phase13_status": phase13["status"],
            "selection_closed": freeze["selection_closed"],
        },
    )
    print(completed.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

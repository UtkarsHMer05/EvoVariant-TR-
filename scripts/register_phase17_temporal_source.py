#!/usr/bin/env python3
"""Materialize the authoritative, label-aggregate temporal cohort source."""

# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.registry import Registry, RegistryError, RunStatus, verify_output_hashes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/runs/formal_cpu_20260922/figure_sources/temporal_cohort.json"
TITLE = "Authoritative temporal cohort source — 2026-09-22"
PROTOCOL_SHA256 = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"


def load(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def materialize() -> Path:
    cohort = load("research/ml_extension/splits/authoritative_cohort_manifest.json")
    summary = load("research/ml_extension/splits/phase3_manifest_summary.json")
    audit = summary["temporal_audit"]
    comparison = summary["historical_target_comparison"]
    development = summary["development_split"]
    rows = [
        {"stage": "historical_target_comparison_only", "count": 1024, "scope": "historical target; comparison only"},
        {"stage": "historical_target_B_LB", "count": comparison["final_temporal_n"] + abs(comparison["difference"]["n_blb"]), "scope": "historical target; comparison only"},
        {"stage": "historical_target_P_LP", "count": comparison["historical_target_comparison"]["n_plp"] if "historical_target_comparison" in comparison else 410, "scope": "historical target; comparison only"},
        {"stage": "authoritative_formal_temporal_cohort", "count": cohort["counts"]["total"], "scope": "accepted formal cohort"},
        {"stage": "authoritative_B_LB", "count": cohort["counts"]["blb"], "scope": "accepted formal cohort"},
        {"stage": "authoritative_P_LP", "count": cohort["counts"]["plp"], "scope": "accepted formal cohort"},
        {"stage": "authoritative_unique_genes", "count": cohort["counts"]["unique_genes"], "scope": "accepted formal cohort"},
        {"stage": "source_t0_unique_variants", "count": audit["t0_unique_vus"], "scope": "Phase 3 temporal audit"},
        {"stage": "source_absent_at_t1", "count": audit["absent_at_t1"], "scope": "Phase 3 temporal audit"},
        {"stage": "source_below_two_stars", "count": audit["below_two_stars"], "scope": "Phase 3 temporal audit"},
        {"stage": "source_not_definitive_at_t1", "count": audit["not_definitive_at_t1"], "scope": "Phase 3 temporal audit"},
        {"stage": "formal_development_total", "count": development["development_total"], "scope": "authoritative development split"},
        {"stage": "formal_development_TRAIN", "count": development["TRAIN"], "scope": "authoritative development split"},
        {"stage": "formal_development_VALIDATION", "count": development["VALIDATION"], "scope": "authoritative development split"},
        {"stage": "locked_test_excluded_from_development", "count": development["LOCKED_TEST"], "scope": "authoritative split; labels not used for development"},
    ]
    payload = {
        "schema_version": "phase17-temporal-cohort-v1",
        "status": "PASS_AUTHORITATIVE_SOURCE",
        "evidence_stage": "PRELIMINARY",
        "selection_closed": True,
        "locked_test_evaluated": False,
        "historical_target": {"count": 1024, "comparison_only": True, "blb": 614, "plp": 410},
        "authoritative_current_cohort": cohort["counts"],
        "rows": rows,
        "limitations": summary["limitations"],
        "source_artifacts": [
            {"path": "research/ml_extension/splits/authoritative_cohort_manifest.json", "sha256": _sha("research/ml_extension/splits/authoritative_cohort_manifest.json")},
            {"path": "research/ml_extension/splits/phase3_manifest_summary.json", "sha256": _sha("research/ml_extension/splits/phase3_manifest_summary.json")},
            {"path": "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json", "sha256": MANIFEST_SHA256},
        ],
    }
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    SOURCE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return SOURCE


def _sha(relative: str) -> str:
    from evovariant_tr.registry import hash_file

    return hash_file(ROOT / relative)


def main() -> int:
    source = materialize()
    registry = Registry(ROOT / "experiments/registry", repo_root=ROOT)
    existing = [record for record in registry.list_runs() if record.title == TITLE]
    if existing:
        if len(existing) != 1 or existing[0].status is not RunStatus.COMPLETED:
            raise RegistryError("temporal source title exists in a non-terminal state")
        verify_output_hashes(existing[0], ROOT)
        print(existing[0].run_id)
        return 0
    record = registry.register(
        title=TITLE,
        evidence_stage=EvidenceStage.PRELIMINARY,
        command=".venv/bin/python scripts/register_phase17_temporal_source.py",
        protocol_hash=PROTOCOL_SHA256,
        data_manifests={"formal_development_manifest_sha256": MANIFEST_SHA256},
        model_identity="authoritative_temporal_cohort_metadata",
        scorer_config={"locked_test_evaluated": False, "selection_closed": True},
        comparator_versions={},
        seed=42,
        hardware={"execution": "local CPU"},
        experiment_family="PHASE17_TEMPORAL_COHORT_SOURCE",
        dataset_manifest_hash=MANIFEST_SHA256,
        split_manifest_hash=MANIFEST_SHA256,
        model_name="Authoritative temporal cohort metadata",
        checkpoint="phase3_authoritative_cohort",
        model_revision="metadata-only",
        preprocessing_version="phase3_temporal_audit_v1",
        feature_version="none",
        config={"source_scope": "cohort aggregates only", "locked_test_evaluated": False},
        gpu="CPU",
        estimated_cost_usd=0.0,
        notes="Metadata-only temporal source; no predictions, labels transported, model selection, or remote compute.",
    )
    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[str(source.relative_to(ROOT))],
        outputs_base_dir=ROOT,
        metrics={"source_count": 1, "locked_test_evaluated": False},
    )
    print(completed.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

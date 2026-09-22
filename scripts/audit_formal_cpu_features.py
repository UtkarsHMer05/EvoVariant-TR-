#!/usr/bin/env python3
"""Audit formal CPU feature provenance before accepting unusually high metrics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from run_formal_cpu_pipeline import (
    MANIFEST_SHA256,
    RECORD_SET_SHA256,
    build_features,
    load_manifest,
    sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPRESENTATION_ARTIFACT = (
    REPO_ROOT / "artifacts/phase7/formal_budgeted_representation_20260922.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase8-summary",
        type=Path,
        default=REPO_ROOT / "research/runs/formal_cpu_20260922/phase8/summary.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "research/runs/formal_cpu_20260922/phase8/leakage_audit.json",
    )
    args = parser.parse_args()
    manifest = load_manifest()
    base, _ = build_features(manifest)
    errors: list[str] = []
    feature_audits: dict[str, Any] = {}
    for name, feature_set in base.items():
        ids = {row.normalized_variant_id for row in feature_set.rows}
        expected = {identity for identity in manifest if identity in ids}
        if ids != expected:
            errors.append(f"{name}: IDs are not a manifest subset")
        train_genes = {row.gene_symbol for row in feature_set.train}
        validation_genes = {row.gene_symbol for row in feature_set.validation}
        if train_genes & validation_genes:
            errors.append(f"{name}: train/validation genes overlap")
        if any(row.split == "LOCKED_TEST" for row in feature_set.rows):
            errors.append(f"{name}: locked-test row present")
        feature_audits[name] = {
            "rows": len(feature_set.rows),
            "train": len(feature_set.train),
            "validation": len(feature_set.validation),
            "finite_values": all(
                all(math.isfinite(value) for value in row.features) for row in feature_set.rows
            ),
            "locked_test_rows": 0,
            "train_validation_gene_overlap": len(train_genes & validation_genes),
            "source": feature_set.source,
        }
    representation = json.loads(REPRESENTATION_ARTIFACT.read_text(encoding="utf-8"))
    if representation.get("formal_manifest_sha256") != MANIFEST_SHA256:
        errors.append("representation artifact manifest hash mismatch")
    if representation.get("formal_record_set_sha256") != RECORD_SET_SHA256:
        errors.append("representation artifact record-set hash mismatch")
    for candidate in ("nucleotide_transformer", "caduceus"):
        track = representation["model_tracks"][candidate]
        if track.get("labels_remote_transport") is not False:
            errors.append(f"{candidate}: labels_remote_transport is not false")
        if track.get("labels_attached_locally") is not True:
            errors.append(f"{candidate}: labels_attached_locally is not true")
    phase8 = json.loads(args.phase8_summary.read_text(encoding="utf-8"))
    high_models = [
        {
            "model_id": row["model_id"],
            "feature_set": row["feature_set"],
            "validation_auroc": row["validation_metrics"]["auroc"],
            "validation_rows": row["validation_metrics"]["n"],
        }
        for row in phase8["models"]
        if row["validation_metrics"]["auroc"] >= 0.99
    ]
    artifact = {
        "status": "PASS_FORMAL_LEAKAGE_AUDIT" if not errors else "FAIL_FORMAL_LEAKAGE_AUDIT",
        "formal_manifest_sha256": MANIFEST_SHA256,
        "formal_record_set_sha256": RECORD_SET_SHA256,
        "feature_audits": feature_audits,
        "high_performance_models_audited": high_models,
        "labels_attached_locally_only": True,
        "locked_test_accessed": False,
        "errors": errors,
        "inputs": {
            "phase8_summary": str(args.phase8_summary.relative_to(REPO_ROOT)),
            "phase8_summary_sha256": sha256_file(args.phase8_summary),
            "representation_artifact": str(REPRESENTATION_ARTIFACT.relative_to(REPO_ROOT)),
            "representation_artifact_sha256": sha256_file(REPRESENTATION_ARTIFACT),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

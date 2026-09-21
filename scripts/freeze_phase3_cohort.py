#!/usr/bin/env python3
"""Freeze the ML-extension cohort and small tracked provenance manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(path)


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def freeze(repo_root: Path, output_dir: Path) -> dict[str, object]:
    derived = repo_root / "data/derived/ml_extension/phase3"
    audit_path = repo_root / "artifacts/phase3_integrity_audit_20260921.json"
    reference_path = repo_root / "artifacts/reference/grch38_validation_20260921.json"
    source_paths = {
        "temporal_audit": derived / "temporal_audit.json",
        "split_manifest": derived / "split_manifest.json",
        "locked_test_ids": derived / "locked_test_ids.json",
        "phase3_summary": derived / "phase3_summary.json",
        "integrity_audit": audit_path,
        "reference_manifest": repo_root / "data/manifests/grch38.json",
        "reference_validation": reference_path,
    }
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing freeze inputs: " + ", ".join(missing))

    temporal = json.loads(source_paths["temporal_audit"].read_text(encoding="utf-8"))
    split = json.loads(source_paths["split_manifest"].read_text(encoding="utf-8"))
    locked_ids = json.loads(source_paths["locked_test_ids"].read_text(encoding="utf-8"))
    audit = json.loads(source_paths["integrity_audit"].read_text(encoding="utf-8"))
    reference = json.loads(source_paths["reference_validation"].read_text(encoding="utf-8"))
    records = sorted(temporal["final_records"], key=lambda row: row["normalized_variant_id"])
    ids = [row["normalized_variant_id"] for row in records]
    if ids != sorted(locked_ids["ids"]):
        raise ValueError("derived locked IDs do not match temporal final records")
    if len(records) != 946 or sum(int(row["label"]) == 0 for row in records) != 536 or sum(
        int(row["label"]) == 1 for row in records
    ) != 410:
        raise ValueError("authoritative cohort counts differ from ML-DEV-001")
    if (
        reference.get("status") != "PASS"
        or reference.get("unresolved_reference_mismatch_count") != 0
    ):
        raise ValueError("independent reference validation must PASS before cohort freeze")

    generated_at = datetime.now(UTC).isoformat()
    source_hashes = {name: _sha256(path) for name, path in source_paths.items()}
    locked_manifest = {
        "manifest_id": "evovariant-tr-ml-extension-authoritative-locked-test-v1",
        "protocol_version": "1.1.0",
        "deviation_id": "ML-DEV-001",
        "generated_at_utc": generated_at,
        "code_commit": _git_commit(repo_root),
        "assembly": "GRCh38",
        "source_archives": {
            "t0_sha256": audit["source_archives"]["t0"]["sha256"],
            "t1_sha256": audit["source_archives"]["t1"]["sha256"],
        },
        "counts": {
            "total": len(records),
            "blb": sum(int(row["label"]) == 0 for row in records),
            "plp": sum(int(row["label"]) == 1 for row in records),
            "gene_labels": len({row["gene_symbol"] for row in records if row["gene_symbol"]}),
        },
        "record_set_sha256": _canonical_hash(records),
        "records": records,
    }
    locked_path = output_dir / "authoritative_locked_test_manifest.json"
    locked_hash = _write(locked_path, locked_manifest)

    split_summary = {
        "manifest_id": "evovariant-tr-ml-extension-authoritative-split-summary-v1",
        "protocol_version": "1.1.0",
        "deviation_id": "ML-DEV-001",
        "generated_at_utc": generated_at,
        "code_commit": _git_commit(repo_root),
        "generated_split_manifest_path": "data/derived/ml_extension/phase3/split_manifest.json",
        "generated_split_manifest_sha256": source_hashes["split_manifest"],
        "split_hash": split["split_hash"],
        "counts": split["counts"],
        "invariants": split["invariants"],
    }
    split_summary_hash = _write(output_dir / "authoritative_split_manifest.json", split_summary)

    cohort_summary = {
        "manifest_id": "evovariant-tr-ml-extension-authoritative-cohort-v1",
        "protocol_version": "1.1.0",
        "deviation_id": "ML-DEV-001",
        "generated_at_utc": generated_at,
        "code_commit": _git_commit(repo_root),
        "locked_test_manifest": {
            "path": "research/ml_extension/splits/authoritative_locked_test_manifest.json",
            "sha256": locked_hash,
        },
        "counts": locked_manifest["counts"],
        "source_archives": locked_manifest["source_archives"],
        "reference_validation": {
            "path": "artifacts/reference/grch38_validation_20260921.json",
            "sha256": source_hashes["reference_validation"],
        },
        "reference_source_manifest": {
            "path": "data/manifests/grch38.json",
            "sha256": source_hashes["reference_manifest"],
        },
        "historical_target_for_comparison_only": {
            "t0_unique_vus": 1403225,
            "final_temporal_n": 1024,
            "blb": 614,
            "plp": 410,
        },
        "authoritative_difference_from_historical_target": {
            "t0_unique_vus": -330,
            "final_temporal_n": -78,
            "blb": -78,
            "plp": 0,
        },
        "source_artifact_sha256": source_hashes,
        "phase3_audit_status": audit["status"],
        "reference_status": reference["status"],
        "phase3_gate_basis": "ML-DEV-001 plus independent reference PASS",
    }
    cohort_hash = _write(output_dir / "authoritative_cohort_manifest.json", cohort_summary)

    exclusions = {
        "manifest_id": "evovariant-tr-ml-extension-authoritative-exclusion-report-v1",
        "protocol_version": "1.1.0",
        "deviation_id": "ML-DEV-001",
        "generated_at_utc": generated_at,
        "code_commit": _git_commit(repo_root),
        "source_archive_hashes": locked_manifest["source_archives"],
        "t0_filter_funnel": audit["archive_scans"]["t0"],
        "t1_filter_funnel": audit["archive_scans"]["t1"],
        "temporal_resolution": audit["temporal_resolution"],
        "policy": "no records added or excluded solely to match the historical aggregate target",
    }
    exclusion_hash = _write(output_dir / "authoritative_exclusion_report.json", exclusions)

    hashes = {
        "manifest_id": "evovariant-tr-ml-extension-authoritative-hashes-v1",
        "protocol_version": "1.1.0",
        "deviation_id": "ML-DEV-001",
        "generated_at_utc": generated_at,
        "code_commit": _git_commit(repo_root),
        "files": {
            "authoritative_cohort_manifest": {
                "path": "research/ml_extension/splits/authoritative_cohort_manifest.json",
                "sha256": cohort_hash,
            },
            "authoritative_locked_test_manifest": {
                "path": "research/ml_extension/splits/authoritative_locked_test_manifest.json",
                "sha256": locked_hash,
            },
            "authoritative_split_manifest": {
                "path": "research/ml_extension/splits/authoritative_split_manifest.json",
                "sha256": split_summary_hash,
            },
            "authoritative_exclusion_report": {
                "path": "research/ml_extension/splits/authoritative_exclusion_report.json",
                "sha256": exclusion_hash,
            },
            "generated_temporal_audit": {
                "path": "data/derived/ml_extension/phase3/temporal_audit.json",
                "sha256": source_hashes["temporal_audit"],
            },
            "generated_split_manifest": {
                "path": "data/derived/ml_extension/phase3/split_manifest.json",
                "sha256": source_hashes["split_manifest"],
            },
            "reference_validation": {
                "path": "artifacts/reference/grch38_validation_20260921.json",
                "sha256": source_hashes["reference_validation"],
            },
            "reference_source_manifest": {
                "path": "data/manifests/grch38.json",
                "sha256": source_hashes["reference_manifest"],
            },
        },
        "locked_test_record_set_sha256": locked_manifest["record_set_sha256"],
    }
    _write(output_dir / "authoritative_cohort_hashes.json", hashes)
    return {
        "status": "PASS",
        "locked_test_manifest_sha256": locked_hash,
        "locked_test_record_set_sha256": locked_manifest["record_set_sha256"],
        "cohort_manifest_sha256": cohort_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("research/ml_extension/splits")
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    result = freeze(root, output_dir)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Data-only QC package for EvoVariant-TR cohort outputs (Milestone 40).

This script generates a comprehensive QC report that verifies:
1. Primary cohort structural integrity (counts, flow consistency).
2. Calibration cohort structural integrity.
3. Data integrity (SHA-256 hash verification of source archives).
4. Disjointness of VUS and calibration cohorts at t0.

The QC report is saved as `research/results/qc_report.json`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

CHUNK_SIZE = 1 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def qc_primary_cohort(cohort_path: Path) -> dict[str, Any]:
    """Verify primary cohort structural integrity."""
    errors: list[str] = []
    data = json.loads(cohort_path.read_text())

    n_total = data.get("n_total", 0)
    n_pos = data.get("n_resolved_pathogenic", 0)
    n_neg = data.get("n_resolved_benign", 0)
    n_unc = data.get("n_unresolved", 0)
    n_exc = data.get("n_excluded", 0)

    actual_total = n_pos + n_neg + n_unc + n_exc
    if actual_total != n_total:
        errors.append(
            f"Primary cohort count mismatch: {n_pos}+{n_neg}+{n_unc}+{n_exc}="
            f"{actual_total} != n_total={n_total}"
        )

    flow = data.get("flow", {})
    vus_meets_gate = flow.get("t0_vus_meets_star_gate", 0)
    if vus_meets_gate != n_total:
        errors.append(
            f"Flow mismatch: t0_vus_meets_star_gate={vus_meets_gate} "
            f"!= n_total={n_total}"
        )

    return {
        "name": "primary_cohort",
        "n_total": n_total,
        "n_resolved_pathogenic": n_pos,
        "n_resolved_benign": n_neg,
        "n_unresolved": n_unc,
        "n_excluded": n_exc,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def qc_calibration_cohort(cohort_path: Path) -> dict[str, Any]:
    """Verify calibration cohort structural integrity."""
    errors: list[str] = []
    data = json.loads(cohort_path.read_text())

    n_total = data.get("n_total", 0)
    counts = data.get("class_counts", {})
    sum_counts = sum(counts.values())
    if sum_counts != n_total:
        errors.append(
            f"Calibration count mismatch: sum(class_counts)={sum_counts} "
            f"!= n_total={n_total}"
        )

    n_stable = data.get("n_stable", 0)
    n_changed = data.get("n_changed", 0)
    n_excluded = data.get("n_excluded_no_t1", 0)
    if n_stable + n_changed + n_excluded != n_total:
        errors.append(
            f"Calibration flow mismatch: {n_stable}+{n_changed}+{n_excluded} "
            f"!= n_total={n_total}"
        )

    return {
        "name": "calibration_cohort",
        "n_total": n_total,
        "n_stable": n_stable,
        "n_changed": n_changed,
        "n_excluded_no_t1": n_excluded,
        "class_counts": counts,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def qc_data_integrity(
    manifests: list[Path], data_files: list[Path]
) -> dict[str, Any]:
    """Verify data file SHA-256 hashes match manifests."""
    errors: list[str] = []
    results: list[dict[str, Any]] = []

    for manifest_path, data_path in zip(manifests, data_files):
        manifest = json.loads(manifest_path.read_text())
        expected_hash = manifest.get("sha256")
        expected_size = manifest.get("size_bytes")

        if not expected_hash:
            errors.append(f"Manifest {manifest_path} has no sha256 field")
            continue

        if not data_path.exists():
            errors.append(f"Data file not found: {data_path}")
            results.append({
                "file": str(data_path),
                "status": "FAIL",
                "error": "file not found",
            })
            continue

        actual_hash = sha256_file(data_path)
        actual_size = data_path.stat().st_size
        hash_ok = actual_hash == expected_hash
        size_ok = expected_size is None or actual_size == expected_size

        if not hash_ok:
            errors.append(f"SHA-256 mismatch for {data_path.name}")
        if not size_ok:
            errors.append(f"Size mismatch for {data_path.name}")

        results.append({
            "file": str(data_path),
            "sha256_match": hash_ok,
            "size_match": size_ok,
            "status": "PASS" if hash_ok and size_ok else "FAIL",
        })

    return {
        "name": "data_integrity",
        "checks": results,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def qc_disjoint(disjoint_path: Path) -> dict[str, Any]:
    """Verify that primary (VUS) and calibration cohorts are disjoint."""
    errors: list[str] = []
    data = json.loads(disjoint_path.read_text())

    overlap = data.get("overlap_count", -1)
    is_disjoint = data.get("is_disjoint", False)

    if not is_disjoint:
        errors.append(
            f"Cohorts are not disjoint: {overlap} overlapping identities"
        )

    return {
        "name": "disjointness",
        "overlap_count": overlap,
        "is_disjoint": is_disjoint,
        "errors": errors,
        "status": "PASS" if is_disjoint else "FAIL",
    }


def generate_qc_report(output_path: str | Path) -> dict[str, Any]:
    """Generate the full QC report and save to output_path."""
    results_dir = REPO_ROOT / "research" / "results"
    manifests_dir = REPO_ROOT / "research" / "data_manifests"

    checks = [
        qc_primary_cohort(results_dir / "cohort_primary.json"),
        qc_calibration_cohort(results_dir / "cohort_calibration.json"),
        qc_data_integrity(
            [
                manifests_dir / "clinvar_t0.json",
                manifests_dir / "clinvar_t1.json",
            ],
            [
                REPO_ROOT / "data" / "raw" / "clinvar" / "variant_summary_2025-01.txt.gz",
                REPO_ROOT / "data" / "raw" / "clinvar" / "variant_summary_2026-08.txt.gz",
            ],
        ),
        qc_disjoint(results_dir / "disjoint_check.json"),
    ]

    all_errors: list[str] = []
    for check in checks:
        all_errors.extend(check.get("errors", []))

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS" if not all_errors else "FAIL",
        "checks": checks,
        "total_errors": len(all_errors),
        "all_errors": all_errors,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))

    return report


def main() -> int:
    output_path = REPO_ROOT / "research" / "results" / "qc_report.json"
    report = generate_qc_report(output_path)
    print(json.dumps(report, indent=2))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
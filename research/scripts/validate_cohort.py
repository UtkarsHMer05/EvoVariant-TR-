#!/usr/bin/env python3
"""Validate primary cohort output against the research checkpoint.

Verifies:
1. The cohort output JSON contains expected fields.
2. The SHA-256 of the source archives match the manifest.
3. The flow counts are internally consistent (positive + negative + unresolved == total).

Usage:
    python research/scripts/validate_cohort.py --cohort research/results/cohort_primary.json \
        --manifest research/data_manifests/clinvar_t0.json --data data/raw/clinvar/variant_summary_2025-01.txt.gz
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

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


def validate_cohort_json(cohort_path: Path) -> list[str]:
    """Validate cohort JSON structure and internal consistency."""
    errors: list[str] = []

    if not cohort_path.exists():
        errors.append(f"Cohort file not found: {cohort_path}")
        return errors

    data = json.loads(cohort_path.read_text())

    required_fields = {
        "n_total", "n_resolved_pathogenic", "n_resolved_benign",
        "n_unresolved", "n_excluded", "class_counts", "flow",
    }
    missing = required_fields - set(data.keys())
    if missing:
        errors.append(f"Missing required fields: {missing}")

    n_total = data.get("n_total", 0)
    n_pos = data.get("n_resolved_pathogenic", 0)
    n_neg = data.get("n_resolved_benign", 0)
    n_unc = data.get("n_unresolved", 0)

    if n_pos + n_neg + n_unc != n_total:
        errors.append(
            f"Count mismatch: {n_pos}+{n_neg}+{n_unc}={n_pos + n_neg + n_unc} "
            f"!= n_total={n_total}"
        )

    return errors


def validate_manifest_hash(manifest_path: Path, data_path: Path) -> list[str]:
    """Validate that the data file's SHA-256 matches the manifest."""
    errors: list[str] = []

    if not manifest_path.exists():
        errors.append(f"Manifest not found: {manifest_path}")
        return errors

    if not data_path.exists():
        errors.append(f"Data file not found: {data_path}")
        return errors

    manifest = json.loads(manifest_path.read_text())
    expected_hash = manifest.get("sha256")
    if not expected_hash:
        errors.append(f"Manifest {manifest_path} has no sha256 field")
        return errors

    actual_hash = sha256_file(data_path)
    if actual_hash != expected_hash:
        errors.append(
            f"SHA-256 mismatch for {data_path.name}:\n"
            f"  manifest: {expected_hash}\n"
            f"  actual:   {actual_hash}"
        )

    manifest_size = manifest.get("size_bytes")
    if manifest_size and data_path.stat().st_size != manifest_size:
        errors.append(
            f"Size mismatch: manifest={manifest_size}, "
            f"actual={data_path.stat().st_size}"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True,
                        help="Path to cohort output JSON")
    parser.add_argument("--manifest", type=Path, required=True,
                        help="Path to data manifest JSON")
    parser.add_argument("--data", type=Path, required=True,
                        help="Path to the data file to verify")
    args = parser.parse_args(argv)

    all_errors: list[str] = []

    all_errors.extend(validate_cohort_json(args.cohort))
    all_errors.extend(validate_manifest_hash(args.manifest, args.data))

    if all_errors:
        print("VALIDATION FAILED:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("VALIDATION PASSED: cohort output is consistent and data hashes match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
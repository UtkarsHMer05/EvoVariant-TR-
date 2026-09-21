#!/usr/bin/env python3
"""Run the standalone independent GRCh38 base audit for the authoritative cohort."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from evovariant_tr.reference import ReferenceGenome, sha256_file


def validate(
    *,
    repo_root: Path,
    temporal_path: Path,
    output_path: Path,
) -> dict[str, object]:
    reference_dir = repo_root / "data/reference"
    fasta = reference_dir / "Homo_sapiens_assembly38.fasta"
    fai = reference_dir / "Homo_sapiens_assembly38.fasta.fai"
    temporal = json.loads(temporal_path.read_text(encoding="utf-8"))
    records = temporal.get("final_records")
    if not isinstance(records, list):
        raise ValueError(f"temporal artifact has no final_records list: {temporal_path}")
    genome = ReferenceGenome(fasta)
    mismatches: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    for row in records:
        chromosome = str(row["chromosome"])
        position = int(row["position_1based"])
        declared = str(row["reference"])
        base = genome.get_base(chromosome, position)
        lookup_chromosome = chromosome
        if base is None and not chromosome.startswith("chr"):
            lookup_chromosome = f"chr{chromosome}"
            base = genome.get_base(lookup_chromosome, position)
        evidence = {
            "normalized_variant_id": row["normalized_variant_id"],
            "chromosome": chromosome,
            "lookup_chromosome": lookup_chromosome,
            "position_1based": position,
            "declared_reference": declared,
            "reference_base": base,
        }
        if base is None:
            missing.append(evidence)
        elif base != declared:
            mismatches.append(evidence)

    report: dict[str, object] = {
        "artifact_id": "phase3-reference-validation-20260921",
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "PASS" if not mismatches and not missing else "FAIL",
        "assembly": "GRCh38",
        "reference_manifest": "data/manifests/grch38.json",
        "fasta": {
            "path": "data/reference/Homo_sapiens_assembly38.fasta",
            "byte_size": fasta.stat().st_size,
            "sha256": sha256_file(fasta),
        },
        "fai": {
            "path": "data/reference/Homo_sapiens_assembly38.fasta.fai",
            "byte_size": fai.stat().st_size,
            "sha256": sha256_file(fai),
        },
        "input_temporal_artifact": str(temporal_path.relative_to(repo_root)),
        "checked_variant_count": len(records),
        "unresolved_reference_mismatch_count": len(mismatches),
        "missing_coordinate_count": len(missing),
        "mismatches": mismatches,
        "missing_coordinates": missing,
        "decision": (
            "all authoritative temporal records match the independent GRCh38 base audit"
            if not mismatches and not missing
            else "do not promote Phase 3; investigate mismatches or missing coordinates"
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--temporal",
        type=Path,
        default=Path("data/derived/ml_extension/phase3/temporal_audit.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/reference/grch38_validation_20260921.json"),
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    temporal = args.temporal if args.temporal.is_absolute() else root / args.temporal
    output = args.output if args.output.is_absolute() else root / args.output
    report = validate(repo_root=root, temporal_path=temporal, output_path=output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "checked_variant_count": report["checked_variant_count"],
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

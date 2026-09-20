"""Validated CSV batch ingestion and resumability contract."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_VARIANT_COLUMNS = ("assembly", "chromosome", "position_1based", "reference", "alternate")


@dataclass(frozen=True)
class BatchVariant:
    assembly: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    normalized_variant_id: str


def parse_variant_csv(path: str | Path) -> list[BatchVariant]:
    """Parse a canonical CSV and reject malformed rows before queueing work."""
    target = Path(path)
    with target.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_VARIANT_COLUMNS if column not in fields]
        if missing:
            raise ValueError(f"batch CSV is missing required columns: {missing}")
        variants: list[BatchVariant] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                assembly = str(row["assembly"]).strip()
                chromosome = str(row["chromosome"]).strip().removeprefix("chr")
                position = int(str(row["position_1based"]).strip())
                reference = str(row["reference"]).strip().upper()
                alternate = str(row["alternate"]).strip().upper()
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid batch row {line_number}") from exc
            if assembly != "GRCh38" or position < 1:
                raise ValueError(f"batch row {line_number} violates GRCh38 coordinate contract")
            if len(reference) != 1 or len(alternate) != 1 or reference == alternate:
                raise ValueError(f"batch row {line_number} is not a biallelic SNV")
            if reference not in "ACGT" or alternate not in "ACGT":
                raise ValueError(f"batch row {line_number} contains a non-ACGT allele")
            identity = f"GRCh38:{chromosome.upper()}:{position}:{reference}>{alternate}"
            variants.append(
                BatchVariant(assembly, chromosome, position, reference, alternate, identity)
            )
    identities = [variant.normalized_variant_id for variant in variants]
    if len(identities) != len(set(identities)):
        raise ValueError("batch contains duplicate normalized variant IDs")
    return variants


def batch_progress(
    *,
    total: int,
    completed: int,
    failed: int,
) -> dict[str, Any]:
    """Report resumable progress without treating failed shards as completed."""
    if total < 0 or completed < 0 or failed < 0 or completed + failed > total:
        raise ValueError("invalid batch progress counts")
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "remaining": total - completed - failed,
        "coverage": completed / total if total else 0.0,
        "resumable": failed > 0 or completed < total,
    }

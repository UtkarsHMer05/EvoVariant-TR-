"""Immutable formal-data loading and paired sequence construction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from evovariant_tr.sequence_mutate import VariantIdentity, mutate_reference, reverse_complement

FORMAL_DIR = Path("research/ml_extension/splits/formal_budgeted_20260921")
LOCKED_MANIFEST = Path("research/ml_extension/splits/authoritative_locked_test_manifest.json")
FORMAL_RECORD_COUNT = 4000
TRAIN_RECORD_COUNT = 3199
VALIDATION_RECORD_COUNT = 801
EXPECTED_MANIFEST_SHA256 = {
    "formal_development_manifest.json": "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782",
    "formal_train_manifest.json": "32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1",
    "formal_validation_manifest.json": "b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b",
}
EXPECTED_LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_LABEL_COUNTS = {
    "train": {0: 2645, 1: 554},
    "validation": {0: 581, 1: 220},
}


class DataIntegrityError(RuntimeError):
    """Raised when the frozen formal data contract is violated."""


@dataclass(frozen=True)
class VariantRow:
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    gene_symbol: str
    label: int
    normalized_variant_id: str
    assembly: str = "GRCh38"

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "VariantRow":
        required = {
            "chromosome",
            "position_1based",
            "reference",
            "alternate",
            "gene_symbol",
            "label",
            "normalized_variant_id",
            "assembly",
        }
        missing = required - value.keys()
        if missing:
            raise DataIntegrityError(f"record missing fields: {sorted(missing)}")
        return cls(
            chromosome=str(value["chromosome"]),
            position_1based=int(value["position_1based"]),
            reference=str(value["reference"]).upper(),
            alternate=str(value["alternate"]).upper(),
            gene_symbol=str(value["gene_symbol"]),
            label=int(value["label"]),
            normalized_variant_id=str(value["normalized_variant_id"]),
            assembly=str(value["assembly"]),
        )

    @property
    def variant(self) -> VariantIdentity:
        return VariantIdentity(
            chrom=self.chromosome,
            start=self.position_1based,
            ref=self.reference,
            alt=self.alternate,
        )


@dataclass(frozen=True)
class SequencePair:
    reference: str
    alternate: str
    reference_rc: str
    alternate_rc: str


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_path(root: Path, filename: str) -> Path:
    return root / FORMAL_DIR / filename


def _load_manifest_rows(
    root: Path,
    filename: str,
    expected_count: int,
    expected_split: str,
) -> list[VariantRow]:
    path = _manifest_path(root, filename)
    if not path.is_file():
        raise DataIntegrityError(f"missing formal manifest: {path}")
    actual_hash = sha256_file(path)
    expected_hash = EXPECTED_MANIFEST_SHA256[filename]
    if actual_hash != expected_hash:
        raise DataIntegrityError(
            f"{filename} hash mismatch: expected {expected_hash}, got {actual_hash}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != expected_count:
        raise DataIntegrityError(
            f"{filename} record count mismatch: expected {expected_count}, "
            f"got {len(records) if isinstance(records, list) else None}"
        )
    rows = [VariantRow.from_mapping(record) for record in records]
    if any(record.get("split") != expected_split for record in records):
        raise DataIntegrityError(f"{filename} contains a non-{expected_split} split")
    return rows


def load_formal_rows(root: str | Path = ".") -> tuple[list[VariantRow], list[VariantRow]]:
    """Load and verify only the formal TRAIN and VALIDATION rows."""
    root_path = Path(root)
    train = _load_manifest_rows(root_path, "formal_train_manifest.json", TRAIN_RECORD_COUNT, "TRAIN")
    validation = _load_manifest_rows(
        root_path, "formal_validation_manifest.json", VALIDATION_RECORD_COUNT, "VALIDATION"
    )
    if len(train) + len(validation) != FORMAL_RECORD_COUNT:
        raise DataIntegrityError("formal development row count mismatch")
    if {row.normalized_variant_id for row in train} & {
        row.normalized_variant_id for row in validation
    }:
        raise DataIntegrityError("TRAIN/VALIDATION normalized-ID overlap")
    if {row.gene_symbol for row in train} & {row.gene_symbol for row in validation}:
        raise DataIntegrityError("TRAIN/VALIDATION gene overlap")
    for name, rows in (("train", train), ("validation", validation)):
        counts = {label: sum(row.label == label for row in rows) for label in (0, 1)}
        if counts != EXPECTED_LABEL_COUNTS[name]:
            raise DataIntegrityError(f"{name} label counts mismatch: {counts}")
    return train, validation


def verify_formal_data(root: str | Path = ".") -> dict[str, Any]:
    """Return auditable formal-data invariants without exposing locked labels."""
    root_path = Path(root)
    train, validation = load_formal_rows(root_path)
    locked_path = root_path / LOCKED_MANIFEST
    if sha256_file(locked_path) != EXPECTED_LOCKED_MANIFEST_SHA256:
        raise DataIntegrityError("locked-test manifest hash mismatch")
    locked = json.loads(locked_path.read_text(encoding="utf-8"))
    locked_ids = {
        str(record["normalized_variant_id"])
        for record in locked.get("records", [])
        if "normalized_variant_id" in record
    }
    development_ids = {row.normalized_variant_id for row in (*train, *validation)}
    overlap = development_ids & locked_ids
    if overlap:
        raise DataIntegrityError(f"formal data overlaps locked test: {len(overlap)}")
    return {
        "formal_record_count": len(train) + len(validation),
        "train_record_count": len(train),
        "validation_record_count": len(validation),
        "train_label_counts": EXPECTED_LABEL_COUNTS["train"],
        "validation_label_counts": EXPECTED_LABEL_COUNTS["validation"],
        "train_validation_gene_overlap": 0,
        "train_validation_id_overlap": 0,
        "locked_id_overlap": 0,
        "manifest_sha256": dict(EXPECTED_MANIFEST_SHA256),
        "locked_manifest_sha256": EXPECTED_LOCKED_MANIFEST_SHA256,
    }


def resolve_contig(fasta: Any, chromosome: str) -> str:
    candidates = [chromosome, f"chr{chromosome}"]
    if chromosome in {"MT", "M", "chrM"}:
        candidates.extend(["MT", "chrM", "M"])
    for candidate in dict.fromkeys(candidates):
        try:
            fasta[candidate]
            return candidate
        except (KeyError, ValueError):
            continue
    raise DataIntegrityError(f"reference contig not found for chromosome {chromosome}")


def reference_window(fasta: Any, row: VariantRow, window_size: int = 8192) -> tuple[str, int]:
    """Return a fixed-length GRCh38 window and the zero-based variant offset."""
    if window_size < 1 or window_size % 2:
        raise ValueError("window_size must be a positive even number")
    contig = resolve_contig(fasta, row.chromosome)
    contig_length = len(fasta[contig])
    start_1based = row.position_1based - window_size // 2
    start_1based = max(1, min(start_1based, contig_length - window_size + 1))
    end_1based = start_1based + window_size - 1
    sequence = str(fasta[contig][start_1based - 1 : end_1based]).upper()
    if len(sequence) != window_size:
        raise DataIntegrityError(f"reference window length {len(sequence)} != {window_size}")
    offset = row.position_1based - start_1based
    return sequence, offset


def paired_sequences(
    fasta: Any,
    row: VariantRow,
    window_size: int = 8192,
) -> SequencePair:
    reference, offset = reference_window(fasta, row, window_size)
    alternate = mutate_reference(reference, row.variant, offset)
    if len(alternate) != len(reference):
        raise DataIntegrityError("formal adaptation currently requires SNV pairs")
    reference_rc = reverse_complement(reference)
    alternate_rc = reverse_complement(alternate)
    return SequencePair(reference, alternate, reference_rc, alternate_rc)


def iter_paired_sequences(
    fasta: Any,
    rows: Iterable[VariantRow],
    window_size: int = 8192,
) -> Iterable[SequencePair]:
    for row in rows:
        yield paired_sequences(fasta, row, window_size)


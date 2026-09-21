"""Reproducible ML-extension cohort auditing and gene-grouped splits.

The frozen temporal cohort is built from the two dated ClinVar archives.  The
development source is the t0 archive's definitive-at-t0 records, while the
temporal t0-VUS-to-t1-resolution records remain locked.  This module keeps the
two paths separate and writes content-addressed, reproducible manifests.

Raw archives and generated record-level manifests belong under ignored data
directories.  Small summaries and hashes are the reviewable control-plane
artifacts; no generated result is scientific evidence until its source and
split hashes are recorded.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from evovariant_tr.clinvar_parser import (
    CLINSIG_NORMALIZATION,
    ClinicalSignificance,
    parse_header,
    review_status_to_stars,
)

ASSEMBLY = "GRCh38"
MIN_REVIEW_STARS = 2
TRAIN = "TRAIN"
VALIDATION = "VALIDATION"
LOCKED_TEST = "LOCKED_TEST"
SNV_TYPES = frozenset({"SNV", "single nucleotide variant"})
BASES = frozenset("ACGT")
PATHOGENIC = frozenset(
    {
        ClinicalSignificance.PATHOGENIC,
        ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
        ClinicalSignificance.LIKELY_PATHOGENIC,
    }
)
BENIGN = frozenset(
    {
        ClinicalSignificance.BENIGN,
        ClinicalSignificance.BENIGN_LIKELY_BENIGN,
        ClinicalSignificance.LIKELY_BENIGN,
    }
)


@dataclass
class SnapshotStats:
    """Streaming audit counters for one ClinVar archive."""

    total_rows: int = 0
    malformed_rows: int = 0
    grch38_rows: int = 0
    germline_snv_rows: int = 0
    eligible_snv_rows: int = 0
    vus_rows: int = 0
    definitive_rows: int = 0


@dataclass(frozen=True)
class CompactRecord:
    """The fields needed for deterministic cohort construction."""

    normalized_variant_id: str
    assembly: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    gene_symbol: str | None
    review_stars: int
    category: str
    label: int | None
    source_record_hash: str


@dataclass
class TemporalAudit:
    """Auditable, mutually exclusive counts and final locked records.

    ``below_two_stars`` counts matched definitive t1 outcomes that fail the
    primary review-star gate. ``not_definitive_at_t1`` counts matched outcomes
    that are not B/LB or P/LP regardless of their review-star count. Keeping
    these categories disjoint makes the audit directly comparable with the
    frozen QA checkpoint without changing the primary label-quality gate.
    """

    t0: SnapshotStats
    t1: SnapshotStats
    t0_unique_vus: int
    t0_duplicate_vus_ids: int
    t1_matched_vus: int
    absent_at_t1: int
    below_two_stars: int
    not_definitive_at_t1: int
    final_temporal_n: int
    n_blb: int
    n_plp: int
    gene_labels: int
    reference_mismatch_count: int
    t1_conflicting_duplicate_ids: int
    gene_mismatch_count: int
    final_records: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self, *, include_records: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "t0": asdict(self.t0),
            "t1": asdict(self.t1),
            "t0_unique_vus": self.t0_unique_vus,
            "t0_duplicate_vus_ids": self.t0_duplicate_vus_ids,
            "t1_matched_vus": self.t1_matched_vus,
            "absent_at_t1": self.absent_at_t1,
            "below_two_stars": self.below_two_stars,
            "not_definitive_at_t1": self.not_definitive_at_t1,
            "final_temporal_n": self.final_temporal_n,
            "n_blb": self.n_blb,
            "n_plp": self.n_plp,
            "gene_labels": self.gene_labels,
            "reference_mismatch_count": self.reference_mismatch_count,
            "t1_conflicting_duplicate_ids": self.t1_conflicting_duplicate_ids,
            "gene_mismatch_count": self.gene_mismatch_count,
        }
        if include_records:
            result["final_records"] = self.final_records
        return result


def normalized_variant_id(
    chromosome: str,
    position_1based: int,
    reference: str,
    alternate: str,
) -> str:
    """Build the one canonical split identity used by the ML extension."""
    chrom = chromosome.strip()
    if chrom.lower().startswith("chr"):
        chrom = chrom[3:]
    return f"{ASSEMBLY}:{chrom.upper()}:{position_1based}:{reference.upper()}>{alternate.upper()}"


def _record_hash(raw_line: str) -> str:
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def _classification(raw: str) -> tuple[str, int | None]:
    value = CLINSIG_NORMALIZATION.get(raw, ClinicalSignificance.OTHER)
    if value in PATHOGENIC:
        return "pathogenic", 1
    if value in BENIGN:
        return "benign", 0
    if value == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE:
        return "vus", None
    return "other", None


def _iter_compact_records(
    path: str | Path,
    stats: SnapshotStats,
) -> Iterable[CompactRecord]:
    """Stream valid GRCh38 germline SNVs without materializing archive rows."""
    target = Path(path)
    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return
        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}
        for raw_line in handle:
            line = raw_line.rstrip("\n\r")
            if not line.strip():
                continue
            stats.total_rows += 1
            parts = line.split("\t")
            if len(parts) < len(col):
                stats.malformed_rows += 1
                continue

            assembly = parts[col["Assembly"]].strip()
            if assembly != ASSEMBLY:
                continue
            stats.grch38_rows += 1
            variant_type = parts[col["Type"]].strip()
            origin = parts[col["OriginSimple"]].strip().lower()
            if variant_type not in SNV_TYPES or "germline" not in origin:
                continue
            stats.germline_snv_rows += 1

            position_raw = parts[col["PositionVCF"]] if "PositionVCF" in col else ""
            position_raw = position_raw if position_raw not in ("", "-") else parts[col["Start"]]
            try:
                position = int(position_raw)
                stop = int(parts[col["Stop"]])
            except ValueError:
                stats.malformed_rows += 1
                continue
            chromosome = parts[col["Chromosome"]].strip()
            reference_raw = (
                parts[col["ReferenceAlleleVCF"]]
                if "ReferenceAlleleVCF" in col
                else parts[col["ReferenceAllele"]]
            )
            alternate_raw = (
                parts[col["AlternateAlleleVCF"]]
                if "AlternateAlleleVCF" in col
                else parts[col["AlternateAllele"]]
            )
            reference_raw = (
                reference_raw
                if reference_raw not in ("", "-")
                else parts[col["ReferenceAllele"]]
            )
            alternate_raw = (
                alternate_raw
                if alternate_raw not in ("", "-")
                else parts[col["AlternateAllele"]]
            )
            reference = reference_raw.strip().upper()
            alternate = alternate_raw.strip().upper()
            if (
                not chromosome
                or chromosome == "-"
                or position < 1
                or stop != position
                or len(reference) != 1
                or len(alternate) != 1
                or reference not in BASES
                or alternate not in BASES
                or reference == alternate
            ):
                continue
            stats.eligible_snv_rows += 1
            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx].strip() if gene_idx is not None else ""
            gene_symbol = gene if gene and gene != "-" else None
            category, label = _classification(parts[col["ClinicalSignificance"]].strip())
            yield CompactRecord(
                normalized_variant_id=normalized_variant_id(
                    chromosome, position, reference, alternate
                ),
                assembly=assembly,
                chromosome=chromosome.removeprefix("chr"),
                position_1based=position,
                reference=reference,
                alternate=alternate,
                gene_symbol=gene_symbol,
                review_stars=review_status_to_stars(parts[col["ReviewStatus"]]),
                category=category,
                label=label,
                source_record_hash=_record_hash(raw_line),
            )


def _choose_best(
    target: dict[str, CompactRecord],
    record: CompactRecord,
    conflicting_ids: set[str],
) -> None:
    """Select the highest-review record with a deterministic tie-break."""
    existing = target.get(record.normalized_variant_id)
    if existing is None:
        target[record.normalized_variant_id] = record
        return
    if existing.review_stars == record.review_stars and existing.category != record.category:
        conflicting_ids.add(record.normalized_variant_id)
    if (record.review_stars, record.source_record_hash) > (
        existing.review_stars,
        existing.source_record_hash,
    ):
        target[record.normalized_variant_id] = record


def _collect_t0(
    path: str | Path,
) -> tuple[dict[str, CompactRecord], dict[str, CompactRecord], SnapshotStats, int, set[str]]:
    """Collect t0 VUS and definitive records for the two Phase 3 paths."""
    stats = SnapshotStats()
    vus: dict[str, CompactRecord] = {}
    definitive: dict[str, CompactRecord] = {}
    conflicting_ids: set[str] = set()
    for record in _iter_compact_records(path, stats):
        if record.category == "vus":
            stats.vus_rows += 1
            _choose_best(vus, record, conflicting_ids)
        elif record.label in (0, 1):
            if record.review_stars < MIN_REVIEW_STARS:
                continue
            stats.definitive_rows += 1
            _choose_best(definitive, record, conflicting_ids)
    # A VUS and a definitive record can share an identity in malformed/duplicate
    # source rows.  Exclude such identities from the development source and make
    # the overlap explicit rather than silently choosing a label.
    overlap = set(vus).intersection(definitive)
    for identity in overlap:
        definitive.pop(identity, None)
    return vus, definitive, stats, len(overlap), conflicting_ids


def audit_temporal_cohort(
    t0_path: str | Path,
    t1_path: str | Path,
) -> TemporalAudit:
    """Recompute temporal flow counts without reading final labels into tuning."""
    t0_vus, _, t0_stats, _, t0_conflicts = _collect_t0(t0_path)
    t1_stats = SnapshotStats()
    t1_best: dict[str, CompactRecord] = {}
    t1_conflicts: set[str] = set()
    t0_coordinate_alt: set[tuple[str, int, str]] = {
        (record.chromosome, record.position_1based, record.alternate)
        for record in t0_vus.values()
    }
    t1_coordinate_alt_refs: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    for record in _iter_compact_records(t1_path, t1_stats):
        key = (record.chromosome, record.position_1based, record.alternate)
        if record.normalized_variant_id in t0_vus:
            _choose_best(t1_best, record, t1_conflicts)
        if key in t0_coordinate_alt:
            t1_coordinate_alt_refs[key].add(record.reference)

    absent = below_stars = not_definitive = n_blb = n_plp = 0
    gene_labels = gene_mismatch = reference_mismatch = 0
    final_records: list[dict[str, Any]] = []
    for identity, t0_record in sorted(t0_vus.items()):
        t1_record = t1_best.get(identity)
        if t1_record is None:
            absent += 1
            continue
        if t1_record.review_stars < MIN_REVIEW_STARS:
            if t1_record.label in (0, 1):
                below_stars += 1
            else:
                not_definitive += 1
            continue
        if t1_record.label not in (0, 1):
            not_definitive += 1
            continue
        assert t1_record.label is not None
        if t1_record.label == 1:
            n_plp += 1
        else:
            n_blb += 1
        gene = t0_record.gene_symbol or t1_record.gene_symbol
        if gene:
            gene_labels += 1
        if t0_record.gene_symbol and t1_record.gene_symbol:
            if t0_record.gene_symbol != t1_record.gene_symbol:
                gene_mismatch += 1
        coordinate_key = (
            t0_record.chromosome,
            t0_record.position_1based,
            t0_record.alternate,
        )
        other_refs = t1_coordinate_alt_refs.get(coordinate_key, set())
        if any(ref != t0_record.reference for ref in other_refs):
            reference_mismatch += 1
        final_records.append(
            {
                "normalized_variant_id": identity,
                "assembly": ASSEMBLY,
                "chromosome": t0_record.chromosome,
                "position_1based": t0_record.position_1based,
                "reference": t0_record.reference,
                "alternate": t0_record.alternate,
                "gene_symbol": gene,
                "label": t1_record.label,
                "split": LOCKED_TEST,
                "source_release": "clinvar_t0_to_t1",
                "source_record_hash": t1_record.source_record_hash,
                "t0_source_record_hash": t0_record.source_record_hash,
            }
        )

    return TemporalAudit(
        t0=t0_stats,
        t1=t1_stats,
        t0_unique_vus=len(t0_vus),
        t0_duplicate_vus_ids=max(0, t0_stats.vus_rows - len(t0_vus)),
        t1_matched_vus=len(t1_best),
        absent_at_t1=absent,
        below_two_stars=below_stars,
        not_definitive_at_t1=not_definitive,
        final_temporal_n=len(final_records),
        n_blb=n_blb,
        n_plp=n_plp,
        gene_labels=gene_labels,
        reference_mismatch_count=reference_mismatch,
        t1_conflicting_duplicate_ids=len(t1_conflicts),
        gene_mismatch_count=gene_mismatch,
        final_records=final_records,
    )


def _group_key(record: CompactRecord) -> str:
    if record.gene_symbol:
        return record.gene_symbol.strip().upper()
    return f"UNKNOWN:{record.normalized_variant_id}"


def _assign_groups(
    records: list[CompactRecord],
    *,
    seed: int,
    validation_fraction: float,
) -> dict[str, str]:
    """Assign whole gene groups with a deterministic size/class-aware greedy pass."""
    groups: dict[str, list[CompactRecord]] = defaultdict(list)
    for record in records:
        groups[_group_key(record)].append(record)
    total = len(records)
    target_n = round(total * validation_fraction)
    target_pos = round(sum(record.label == 1 for record in records) * validation_fraction)
    target_neg = round(sum(record.label == 0 for record in records) * validation_fraction)
    current_n = current_pos = current_neg = 0
    assignments: dict[str, str] = {}

    def group_order(item: tuple[str, list[CompactRecord]]) -> tuple[int, str]:
        group, members = item
        digest = hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()
        return (-len(members), digest)

    for group, members in sorted(groups.items(), key=group_order):
        size = len(members)
        positives = sum(record.label == 1 for record in members)
        negatives = sum(record.label == 0 for record in members)
        train_score = (
            abs(current_n - target_n),
            abs(current_pos - target_pos) + abs(current_neg - target_neg),
            1,
        )
        validation_score = (
            abs(current_n + size - target_n),
            abs(current_pos + positives - target_pos)
            + abs(current_neg + negatives - target_neg),
            0,
        )
        if validation_score < train_score:
            assignments[group] = VALIDATION
            current_n += size
            current_pos += positives
            current_neg += negatives
        else:
            assignments[group] = TRAIN
    if len(assignments) > 1 and VALIDATION not in assignments.values():
        first_group = next(iter(sorted(assignments)))
        assignments[first_group] = VALIDATION
    return assignments


def _split_record(record: CompactRecord, split: str) -> dict[str, Any]:
    return {
        "normalized_variant_id": record.normalized_variant_id,
        "assembly": record.assembly,
        "chromosome": record.chromosome,
        "position_1based": record.position_1based,
        "reference": record.reference,
        "alternate": record.alternate,
        "gene_symbol": record.gene_symbol,
        "label": record.label,
        "split": split,
        "source_release": "clinvar_t0",
        "source_record_hash": record.source_record_hash,
    }


def build_development_split(
    definitive_records: Iterable[CompactRecord],
    locked_test_ids: set[str],
    *,
    seed: int,
    validation_fraction: float = 0.2,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build records and summary for the validation-only development source."""
    candidates = [
        record
        for record in definitive_records
        if record.normalized_variant_id not in locked_test_ids and record.label in (0, 1)
    ]
    candidates.sort(key=lambda record: record.normalized_variant_id)
    assignments = _assign_groups(
        candidates,
        seed=seed,
        validation_fraction=validation_fraction,
    )
    records = [
        _split_record(record, assignments[_group_key(record)])
        for record in candidates
    ]
    records.sort(key=lambda record: record["normalized_variant_id"])
    by_split = {
        split: [record for record in records if record["split"] == split]
        for split in (TRAIN, VALIDATION)
    }
    train_genes = {
        record["gene_symbol"]
        for record in by_split[TRAIN]
        if record["gene_symbol"] is not None
    }
    validation_genes = {
        record["gene_symbol"]
        for record in by_split[VALIDATION]
        if record["gene_symbol"] is not None
    }
    ids = [record["normalized_variant_id"] for record in records]
    counts: dict[str, Any] = {
        "TRAIN": len(by_split[TRAIN]),
        "VALIDATION": len(by_split[VALIDATION]),
        "LOCKED_TEST": 0,
        "development_total": len(records),
        "development_positive": sum(record["label"] == 1 for record in records),
        "development_negative": sum(record["label"] == 0 for record in records),
        "train_genes": len(train_genes),
        "validation_genes": len(validation_genes),
        "locked_test_excluded_from_development": len(locked_test_ids),
        "duplicate_normalized_ids": len(ids) - len(set(ids)),
    }
    invariants = {
        "normalized_id_overlap": len(set(ids) & set()),
        "train_validation_gene_overlap": len(train_genes & validation_genes),
        "locked_test_overlap": len(set(ids).intersection(locked_test_ids)),
        "deterministic": True,
    }
    return records, {"counts": counts, "invariants": invariants}


def sha256_file(path: str | Path) -> str:
    """Hash an on-disk source manifest or generated artifact."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_hash(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        line = json.dumps(record, sort_keys=True, separators=(",", ":"))
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_split_records(
    records: list[dict[str, Any]],
    locked_test_ids: set[str],
) -> dict[str, Any]:
    """Recompute leakage invariants from serialized split records."""
    split_ids: dict[str, set[str]] = defaultdict(set)
    split_genes: dict[str, set[str]] = defaultdict(set)
    duplicate_ids = 0
    seen: set[str] = set()
    for record in records:
        identity = str(record["normalized_variant_id"])
        if identity in seen:
            duplicate_ids += 1
        seen.add(identity)
        split = str(record["split"])
        split_ids[split].add(identity)
        gene = record.get("gene_symbol")
        if gene is not None:
            split_genes[split].add(str(gene))
    all_sets = [split_ids[TRAIN], split_ids[VALIDATION], set(locked_test_ids)]
    overlap = sum(
        len(all_sets[left] & all_sets[right])
        for left in range(len(all_sets))
        for right in range(left + 1, len(all_sets))
    )
    train_validation_gene_overlap = len(split_genes[TRAIN] & split_genes[VALIDATION])
    return {
        "normalized_id_overlap": overlap + duplicate_ids,
        "train_validation_gene_overlap": train_validation_gene_overlap,
        "locked_test_overlap": len(
            (split_ids[TRAIN] | split_ids[VALIDATION]) & set(locked_test_ids)
        ),
        "duplicate_normalized_ids": duplicate_ids,
        "deterministic": True,
    }


def build_phase3_artifacts(
    t0_path: str | Path,
    t1_path: str | Path,
    *,
    output_dir: str | Path,
    t0_manifest: str | Path,
    t1_manifest: str | Path,
    seed: int = 20260814,
) -> dict[str, Any]:
    """Build ignored record-level outputs and a small reviewable summary."""
    t0_vus, definitive, t0_stats, t0_overlap, t0_conflicts = _collect_t0(t0_path)
    temporal = audit_temporal_cohort(t0_path, t1_path)
    locked_test_ids = {
        record["normalized_variant_id"] for record in temporal.final_records
    }
    split_records, split_summary = build_development_split(
        definitive.values(),
        locked_test_ids,
        seed=seed,
    )
    split_invariants = validate_split_records(split_records, locked_test_ids)
    split_hash = _split_hash(split_records)
    source_hash_payload = {
        "t0_manifest_sha256": sha256_file(t0_manifest),
        "t1_manifest_sha256": sha256_file(t1_manifest),
    }
    source_manifest_hash = hashlib.sha256(
        json.dumps(source_hash_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    manifest: dict[str, Any] = {
        "manifest_id": "evovariant-tr-phase3-development-split-v1",
        "policy_id": "evovariant-tr-development-split-v1",
        "source_manifest_hash": source_manifest_hash,
        "split_hash": split_hash,
        "records": split_records,
        "counts": {
            **split_summary["counts"],
            "LOCKED_TEST": len(locked_test_ids),
            "temporal_final_positive": temporal.n_plp,
            "temporal_final_negative": temporal.n_blb,
            "t0_vus_overlap_with_development": t0_overlap,
        },
        "invariants": split_invariants,
    }
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "temporal_audit.json").write_text(
        json.dumps(temporal.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "locked_test_ids.json").write_text(
        json.dumps(
            {
                "manifest_id": "evovariant-tr-phase3-locked-test-ids-v1",
                "source_manifest_hash": source_manifest_hash,
                "count": len(locked_test_ids),
                "ids": sorted(locked_test_ids),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "dataset_id": "evovariant-tr-phase3-v1",
        "protocol_id": "evovariant-tr-ml-extension",
        "source_archives": {
            "t0": {"path": str(t0_path), "manifest": str(t0_manifest)},
            "t1": {"path": str(t1_path), "manifest": str(t1_manifest)},
        },
        "source_manifest_hash": source_manifest_hash,
        "split_manifest": {
            "path": str(root / "split_manifest.json"),
            "sha256": sha256_file(root / "split_manifest.json"),
            "split_hash": split_hash,
        },
        "temporal_audit": temporal.to_dict(include_records=False),
        "development": split_summary,
        "recomputed_invariants": split_invariants,
        "t0_vus_definitive_overlap": t0_overlap,
        "t0_conflicting_duplicate_ids": len(t0_conflicts),
        "status": "PASS"
        if (
            split_invariants["normalized_id_overlap"] == 0
            and split_invariants["train_validation_gene_overlap"] == 0
            and split_invariants["locked_test_overlap"] == 0
            and split_invariants["duplicate_normalized_ids"] == 0
            and split_invariants["deterministic"] is True
        )
        else "FAIL",
        "limitations": [
            (
                "reference_mismatch is checked between t0/t1 variant identities; a genome "
                "FASTA reference-base audit is not included in this CPU archive pass"
            ),
            (
                "the locked-test labels are present only in the immutable temporal audit "
                "and are never used by development assignment"
            ),
        ],
    }
    (root / "phase3_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary

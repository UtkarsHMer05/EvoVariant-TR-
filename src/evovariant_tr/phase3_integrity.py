"""Evidence-first Phase 3 archive, temporal, and split integrity audit.

This module is deliberately separate from the split builder's output contract.
It re-reads the frozen ClinVar archives and checks the source/filter funnel,
date and review metadata, normalized identities, temporal resolution, and the
generated split artifacts.  A validation-only handoff count is reported for
comparison, never used to add or remove records.

The audit is CPU-only.  A local GRCh38 FASTA is required for an independent
reference-base check; assembly and t0/t1 identity consistency are still
reported when that asset is absent, but they do not promote the Phase 3 gate.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from evovariant_tr.clinvar_parser import parse_header, review_status_to_stars
from evovariant_tr.config import load_protocol
from evovariant_tr.control_plane import sha256_file
from evovariant_tr.manifest import ManifestError, load_manifest, verify_manifest
from evovariant_tr.reference import ReferenceGenome
from evovariant_tr.splits import (
    ASSEMBLY,
    BASES,
    LOCKED_TEST,
    MIN_REVIEW_STARS,
    SNV_TYPES,
    CompactRecord,
    _classification,
    build_phase3_artifacts,
    normalized_variant_id,
    validate_split_records,
)

_ID_PATTERN = re.compile(r"^GRCh38:[^:]+:[1-9][0-9]*:[ACGT]>[ACGT]$")
_DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y")


@dataclass(frozen=True)
class _ScannedRow:
    """One eligible row retained only when it can affect a selected identity."""

    record: CompactRecord
    raw_clinical_significance: str
    raw_review_status: str
    last_evaluated_raw: str
    last_evaluated: date | None
    date_status: str


@dataclass
class _ArchiveScan:
    """Detailed counters and selected rows from one archive pass."""

    role: str
    stats: Counter[str]
    filter_funnel: Counter[str]
    rejection_reasons: Counter[str]
    clinical_significance_counts: Counter[str]
    review_status_counts: Counter[str]
    review_star_counts: Counter[str]
    chromosome_counts: Counter[str]
    chromosome_alias_counts: Counter[str]
    gene_counts: Counter[str]
    date_counts: Counter[str]
    date_min: date | None
    date_max: date | None
    selected_records: dict[str, _ScannedRow]
    conflicting_ids: set[str]
    coordinate_alt_refs: dict[tuple[str, int, str], set[str]]


def _parse_last_evaluated(raw: str) -> tuple[date | None, str]:
    """Parse the two formats present in ClinVar ``LastEvaluated`` fields."""
    value = raw.strip()
    if not value or value == "-":
        return None, "missing"
    try:
        return date.fromisoformat(value), "valid"
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date(), "valid"
        except ValueError:
            continue
    return None, "invalid"


def _choose_scanned(
    target: dict[str, _ScannedRow],
    row: _ScannedRow,
    conflicting_ids: set[str],
) -> None:
    """Mirror the split builder's review-star/hash tie-break for audit rows."""
    identity = row.record.normalized_variant_id
    existing = target.get(identity)
    if existing is None:
        target[identity] = row
        return
    if (
        existing.record.review_stars == row.record.review_stars
        and existing.record.category != row.record.category
    ):
        conflicting_ids.add(identity)
    if (
        row.record.review_stars,
        row.record.source_record_hash,
    ) > (
        existing.record.review_stars,
        existing.record.source_record_hash,
    ):
        target[identity] = row


def _scan_archive(
    path: Path,
    *,
    role: str,
    release_date: date,
    target_ids: set[str] | None = None,
    coordinate_alt_keys: set[tuple[str, int, str]] | None = None,
) -> _ArchiveScan:
    """Scan one archive with explicit rejection and metadata accounting."""
    stats: Counter[str] = Counter()
    funnel: Counter[str] = Counter()
    rejections: Counter[str] = Counter()
    clinical_significance: Counter[str] = Counter()
    review_status: Counter[str] = Counter()
    review_stars: Counter[str] = Counter()
    chromosome_counts: Counter[str] = Counter()
    chromosome_aliases: Counter[str] = Counter()
    gene_counts: Counter[str] = Counter()
    date_counts: Counter[str] = Counter()
    selected: dict[str, _ScannedRow] = {}
    conflicts: set[str] = set()
    coordinate_refs: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    date_min: date | None = None
    date_max: date | None = None

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            raise ValueError(f"archive has no header: {path}")
        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}
        for raw_line in handle:
            line = raw_line.rstrip("\n\r")
            if not line.strip():
                continue
            stats["total_rows"] += 1
            parts = line.split("\t")
            if len(parts) < len(col):
                stats["malformed_rows"] += 1
                rejections["malformed"] += 1
                continue

            raw_significance = parts[col["ClinicalSignificance"]].strip()
            if raw_significance == "Uncertain significance":
                funnel["exact_vus_rows"] += 1
            assembly = parts[col["Assembly"]].strip()
            if assembly != ASSEMBLY:
                if raw_significance == "Uncertain significance":
                    rejections["exact_vus_not_grch38"] += 1
                continue
            stats["grch38_rows"] += 1
            if raw_significance == "Uncertain significance":
                funnel["grch38_exact_vus_rows"] += 1

            origin = parts[col["OriginSimple"]].strip().lower()
            if "germline" not in origin:
                if raw_significance == "Uncertain significance":
                    rejections["exact_vus_not_germline"] += 1
                continue
            stats["germline_rows"] += 1
            if raw_significance == "Uncertain significance":
                funnel["grch38_germline_exact_vus_rows"] += 1

            variant_type = parts[col["Type"]].strip()
            if variant_type not in SNV_TYPES:
                if raw_significance == "Uncertain significance":
                    rejections["exact_vus_not_snv"] += 1
                continue
            stats["germline_snv_rows"] += 1
            if raw_significance == "Uncertain significance":
                funnel["grch38_germline_snv_exact_vus_rows"] += 1

            position_raw = parts[col["PositionVCF"]] if "PositionVCF" in col else ""
            position_raw = position_raw if position_raw not in ("", "-") else parts[col["Start"]]
            try:
                position = int(position_raw)
                stop = int(parts[col["Stop"]])
            except ValueError:
                stats["malformed_rows"] += 1
                rejections["coordinate_parse"] += int(raw_significance == "Uncertain significance")
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
            reference_source = "vcf"
            alternate_source = "vcf"
            if reference_raw in ("", "-"):
                reference_raw = parts[col["ReferenceAllele"]]
                reference_source = "legacy_fallback"
            if alternate_raw in ("", "-"):
                alternate_raw = parts[col["AlternateAllele"]]
                alternate_source = "legacy_fallback"
            reference = reference_raw.strip().upper()
            alternate = alternate_raw.strip().upper()
            rejection: str | None = None
            if not chromosome or chromosome == "-":
                rejection = "missing_chromosome"
            elif position < 1:
                rejection = "position_less_than_one"
            elif stop != position:
                rejection = "stop_differs_from_position"
            elif len(reference) != 1 or len(alternate) != 1:
                rejection = "non_single_base_allele"
            elif reference not in BASES or alternate not in BASES:
                rejection = "non_acgt_allele"
            elif reference == alternate:
                rejection = "reference_equals_alternate"
            if rejection is not None:
                if raw_significance == "Uncertain significance":
                    rejections[rejection] += 1
                continue

            stats["eligible_snv_rows"] += 1
            if raw_significance == "Uncertain significance":
                funnel["eligible_exact_vus_rows"] += 1
            if chromosome.lower().startswith("chr"):
                chromosome_aliases["chr_prefixed"] += 1
            else:
                chromosome_aliases["unprefixed"] += 1
            canonical_chromosome = (
                chromosome[3:] if chromosome.lower().startswith("chr") else chromosome
            )
            canonical_chromosome = canonical_chromosome.upper()
            chromosome_counts[canonical_chromosome] += 1

            raw_review = parts[col["ReviewStatus"]].strip()
            stars = review_status_to_stars(raw_review)
            review_status[raw_review] += 1
            review_stars[str(stars)] += 1
            clinical_significance[raw_significance] += 1
            gene_raw = parts[col["GeneSymbol"]].strip() if "GeneSymbol" in col else ""
            gene = gene_raw if gene_raw and gene_raw != "-" else None
            gene_counts[gene if gene is not None else "<MISSING>"] += 1
            last_raw = parts[col["LastEvaluated"]].strip() if "LastEvaluated" in col else ""
            parsed_date, date_status = _parse_last_evaluated(last_raw)
            date_counts[date_status] += 1
            if parsed_date is not None:
                date_counts["future_than_release"] += int(parsed_date > release_date)
                if date_min is None or parsed_date < date_min:
                    date_min = parsed_date
                if date_max is None or parsed_date > date_max:
                    date_max = parsed_date

            category, label = _classification(raw_significance)
            record = CompactRecord(
                normalized_variant_id=normalized_variant_id(
                    chromosome, position, reference, alternate
                ),
                assembly=assembly,
                chromosome=canonical_chromosome,
                position_1based=position,
                reference=reference,
                alternate=alternate,
                gene_symbol=gene,
                review_stars=stars,
                category=category,
                label=label,
                source_record_hash=hashlib.sha256(raw_line.encode("utf-8")).hexdigest(),
            )
            row = _ScannedRow(
                record=record,
                raw_clinical_significance=raw_significance,
                raw_review_status=raw_review,
                last_evaluated_raw=last_raw,
                last_evaluated=parsed_date,
                date_status=date_status,
            )
            identity = record.normalized_variant_id
            if role == "t0" and category == "vus":
                _choose_scanned(selected, row, conflicts)
            elif role == "t1" and target_ids is not None and identity in target_ids:
                stats["matched_t0_ids_rows"] += 1
                _choose_scanned(selected, row, conflicts)
            if role == "t1" and coordinate_alt_keys is not None:
                key = (canonical_chromosome, position, alternate)
                if key in coordinate_alt_keys:
                    coordinate_refs[key].add(reference)

            if reference_source == "legacy_fallback" or alternate_source == "legacy_fallback":
                stats["legacy_allele_fallback_rows"] += 1
            else:
                stats["vcf_allele_rows"] += 1

    return _ArchiveScan(
        role=role,
        stats=stats,
        filter_funnel=funnel,
        rejection_reasons=rejections,
        clinical_significance_counts=clinical_significance,
        review_status_counts=review_status,
        review_star_counts=review_stars,
        chromosome_counts=chromosome_counts,
        chromosome_alias_counts=chromosome_aliases,
        gene_counts=gene_counts,
        date_counts=date_counts,
        date_min=date_min,
        date_max=date_max,
        selected_records=selected,
        conflicting_ids=conflicts,
        coordinate_alt_refs=dict(coordinate_refs),
    )


def _counter(data: Counter[str]) -> dict[str, int]:
    """Return a deterministic JSON-compatible counter mapping."""
    return {key: int(data[key]) for key in sorted(data)}


def _date_audit(scan: _ArchiveScan) -> dict[str, Any]:
    return {
        "counts": _counter(scan.date_counts),
        "minimum": scan.date_min.isoformat() if scan.date_min else None,
        "maximum": scan.date_max.isoformat() if scan.date_max else None,
        "future_than_release_rows": scan.date_counts["future_than_release"],
    }


def _selected_date_audit(
    rows: dict[str, _ScannedRow], release_date: date
) -> dict[str, int]:
    counts: Counter[str] = Counter(row.date_status for row in rows.values())
    counts["future_than_release"] = sum(
        row.last_evaluated is not None and row.last_evaluated > release_date
        for row in rows.values()
    )
    return _counter(counts)


def _display_path(path: Path, root: Path) -> str:
    """Use repository-relative paths in tracked audit artifacts."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _manifest_evidence(
    path: Path,
    archive: Path,
    expected_date: date,
    display_root: Path,
) -> dict[str, Any]:
    manifest = load_manifest(path)
    if len(manifest.entries) != 1 or manifest.entries[0].path != archive.name:
        raise ManifestError(
            f"{path} must contain exactly one entry for {archive.name!r}"
        )
    failures = verify_manifest(manifest, archive.parent)
    entry = manifest.entries[0]
    return {
        "manifest": _display_path(path, display_root),
        "archive": _display_path(archive, display_root),
        "manifest_sha256": sha256_file(path),
        "archive_sha256": entry.sha256,
        "archive_size_bytes": entry.size_bytes,
        "source_url": entry.source_url,
        "release_date": entry.release_date.isoformat() if entry.release_date else None,
        "expected_release_date": expected_date.isoformat(),
        "verification_status": "PASS" if not failures else "FAIL",
        "verification_failures": [
            {"path": failure.path, "kind": failure.kind, "detail": failure.detail}
            for failure in failures
        ],
    }


def _schema_valid(
    path: Path, data: dict[str, Any], schema_path: Path
) -> tuple[bool, str | None]:
    try:
        import jsonschema
    except ImportError as exc:
        return False, f"{path}: jsonschema is unavailable: {exc}"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return False, f"{path}: schema validation unavailable or invalid: {exc}"
    except jsonschema.ValidationError as exc:
        return False, f"{path}: {exc.message}"
    return True, None


def _gate(status: str, detail: str) -> dict[str, str]:
    return {"status": status, "detail": detail}


def _reference_audit(
    reference_dir: Path,
    final_records: list[dict[str, Any]],
    display_root: Path,
) -> dict[str, Any]:
    fasta = reference_dir / "Homo_sapiens_assembly38.fasta"
    fai = reference_dir / "Homo_sapiens_assembly38.fasta.fai"
    if not fasta.is_file() or not fai.is_file():
        return {
            "status": "NOT_RUN",
            "gate_pass": False,
            "fasta": _display_path(fasta, display_root),
            "fai": _display_path(fai, display_root),
            "checked_variant_count": 0,
            "mismatch_count": None,
            "reason": "local frozen GRCh38 FASTA and .fai index are unavailable",
        }
    genome = ReferenceGenome(fasta)
    mismatches = 0
    missing = 0
    for row in final_records:
        chrom = str(row["chromosome"])
        base = genome.get_base(chrom, int(row["position_1based"]))
        if base is None:
            base = genome.get_base(f"chr{chrom}", int(row["position_1based"]))
        if base is None:
            missing += 1
        elif base != row["reference"]:
            mismatches += 1
    checked = len(final_records)
    return {
        "status": "PASS" if missing == 0 and mismatches == 0 else "FAIL",
        "gate_pass": missing == 0 and mismatches == 0,
        "fasta": _display_path(fasta, display_root),
        "fai": _display_path(fai, display_root),
        "checked_variant_count": checked,
        "mismatch_count": mismatches,
        "missing_coordinate_count": missing,
        "reason": (
            "all final temporal reference bases matched"
            if missing == 0 and mismatches == 0
            else "reference lookup mismatch or missing coordinate"
        ),
    }


def build_phase3_integrity_audit(
    *,
    repo_root: str | Path = ".",
    output_path: str | Path | None = None,
    run_determinism: bool = True,
) -> dict[str, Any]:
    """Build a machine-readable Phase 3 integrity audit and return its payload."""
    root = Path(repo_root).resolve()
    t0 = root / "data/raw/clinvar/variant_summary_2025-01.txt.gz"
    t1 = root / "data/raw/clinvar/variant_summary_2026-08.txt.gz"
    t0_manifest = root / "research/data_manifests/clinvar_t0.json"
    t1_manifest = root / "research/data_manifests/clinvar_t1.json"
    derived = root / "data/derived/ml_extension/phase3"
    current_summary_path = derived / "phase3_summary.json"
    current_temporal_path = derived / "temporal_audit.json"
    current_split_path = derived / "split_manifest.json"
    current_locked_path = derived / "locked_test_ids.json"

    protocol = load_protocol(root / "research/protocol/protocol.yaml")
    expected_t0 = protocol.temporal_design.t0_release.release_date
    expected_t1 = protocol.temporal_design.t1_release.release_date
    t0_source = _manifest_evidence(t0_manifest, t0, expected_t0, root)
    t1_source = _manifest_evidence(t1_manifest, t1, expected_t1, root)

    t0_scan = _scan_archive(t0, role="t0", release_date=expected_t0)
    t0_ids = set(t0_scan.selected_records)
    t0_coordinates = {
        (
            row.record.chromosome,
            row.record.position_1based,
            row.record.alternate,
        )
        for row in t0_scan.selected_records.values()
    }
    t1_scan = _scan_archive(
        t1,
        role="t1",
        release_date=expected_t1,
        target_ids=t0_ids,
        coordinate_alt_keys=t0_coordinates,
    )

    absent = below_stars = not_definitive = n_blb = n_plp = 0
    gene_labels = gene_mismatch = reference_mismatch = 0
    final_records: list[dict[str, Any]] = []
    final_gene_counts: Counter[str] = Counter()
    for identity, t0_row in sorted(t0_scan.selected_records.items()):
        t1_row = t1_scan.selected_records.get(identity)
        if t1_row is None:
            absent += 1
            continue
        if t1_row.record.review_stars < MIN_REVIEW_STARS:
            if t1_row.record.label in (0, 1):
                below_stars += 1
            else:
                not_definitive += 1
            continue
        if t1_row.record.label not in (0, 1):
            not_definitive += 1
            continue
        label = int(t1_row.record.label)
        if label == 1:
            n_plp += 1
        else:
            n_blb += 1
        gene = t0_row.record.gene_symbol or t1_row.record.gene_symbol
        if gene:
            gene_labels += 1
            final_gene_counts[gene.upper()] += 1
        else:
            final_gene_counts["<MISSING>"] += 1
        if t0_row.record.gene_symbol and t1_row.record.gene_symbol:
            gene_mismatch += int(t0_row.record.gene_symbol != t1_row.record.gene_symbol)
        coordinate_key = (
            t0_row.record.chromosome,
            t0_row.record.position_1based,
            t0_row.record.alternate,
        )
        reference_mismatch += int(
            any(
                ref != t0_row.record.reference
                for ref in t1_scan.coordinate_alt_refs.get(coordinate_key, set())
            )
        )
        final_records.append(
            {
                "normalized_variant_id": identity,
                "assembly": ASSEMBLY,
                "chromosome": t0_row.record.chromosome,
                "position_1based": t0_row.record.position_1based,
                "reference": t0_row.record.reference,
                "alternate": t0_row.record.alternate,
                "gene_symbol": gene,
                "label": label,
                "split": LOCKED_TEST,
            }
        )

    temporal = {
        "t0_unique_vus": len(t0_scan.selected_records),
        "t0_valid_vus_rows": t0_scan.filter_funnel["eligible_exact_vus_rows"],
        "t0_duplicate_vus_ids": max(
            0,
            t0_scan.filter_funnel["eligible_exact_vus_rows"] - len(t0_scan.selected_records),
        ),
        "t1_matched_vus": len(t1_scan.selected_records),
        "t1_matched_vus_rows": t1_scan.stats["matched_t0_ids_rows"],
        "absent_at_t1": absent,
        "below_two_stars": below_stars,
        "not_definitive_at_t1": not_definitive,
        "final_temporal_n": len(final_records),
        "n_blb": n_blb,
        "n_plp": n_plp,
        "gene_labels": gene_labels,
        "gene_mismatch_count": gene_mismatch,
        "reference_mismatch_count": reference_mismatch,
        "t0_conflicting_duplicate_ids": len(t0_scan.conflicting_ids),
        "t1_conflicting_duplicate_ids": len(t1_scan.conflicting_ids),
        "partition_sum": absent + below_stars + not_definitive + len(final_records),
        "partition_matches_t0_denominator": (
            absent + below_stars + not_definitive + len(final_records)
            == len(t0_scan.selected_records)
        ),
    }

    split_checks: dict[str, Any]
    determinism: dict[str, Any]
    if all(
        path.is_file()
        for path in (
            current_summary_path,
            current_temporal_path,
            current_split_path,
            current_locked_path,
        )
    ):
        current_summary = json.loads(current_summary_path.read_text(encoding="utf-8"))
        current_temporal = json.loads(current_temporal_path.read_text(encoding="utf-8"))
        current_split = json.loads(current_split_path.read_text(encoding="utf-8"))
        current_locked = json.loads(current_locked_path.read_text(encoding="utf-8"))
        locked_ids = set(str(value) for value in current_locked.get("ids", []))
        split_records = list(current_split.get("records", []))
        recomputed_invariants = validate_split_records(split_records, locked_ids)
        schema_ok, schema_error = _schema_valid(
            current_split_path,
            current_split,
            root / "research/schemas/split_manifest.schema.json",
        )
        split_checks = {
            "status": (
                "PASS"
                if schema_ok and recomputed_invariants == current_split.get("invariants")
                else "FAIL"
            ),
            "current_summary_status": current_summary.get("status"),
            "current_split_manifest_sha256": sha256_file(current_split_path),
            "current_temporal_audit_sha256": sha256_file(current_temporal_path),
            "current_locked_test_ids_sha256": sha256_file(current_locked_path),
            "schema_valid": schema_ok,
            "schema_error": schema_error,
            "recomputed_invariants": recomputed_invariants,
            "serialized_invariants": current_split.get("invariants"),
            "development_counts": current_split.get("counts", {}),
            "locked_test_count": len(locked_ids),
            "development_id_count": len(
                {str(row["normalized_variant_id"]) for row in split_records}
            ),
            "development_locked_id_overlap": len(
                {str(row["normalized_variant_id"]) for row in split_records} & locked_ids
            ),
            "t0_vus_development_id_overlap": len(
                {str(row["normalized_variant_id"]) for row in split_records} & t0_ids
            ),
            "gene_distribution": {
                "train_validation_gene_overlap": recomputed_invariants[
                    "train_validation_gene_overlap"
                ],
                "train_genes": current_split.get("counts", {}).get("train_genes"),
                "validation_genes": current_split.get("counts", {}).get("validation_genes"),
            },
        }
        # Compare only the audit fields generated by this implementation; the
        # current temporal artifact also contains the full locked records.
        current_temporal_projection = {
            key: current_temporal.get(key)
            for key in (
                "t0_unique_vus",
                "t0_duplicate_vus_ids",
                "t1_matched_vus",
                "absent_at_t1",
                "below_two_stars",
                "not_definitive_at_t1",
                "final_temporal_n",
                "n_blb",
                "n_plp",
                "gene_labels",
                "reference_mismatch_count",
                "t1_conflicting_duplicate_ids",
                "gene_mismatch_count",
            )
        }
        split_checks["current_temporal_projection"] = current_temporal_projection
        split_checks["recomputed_temporal_projection"] = {
            key: temporal[key]
            for key in current_temporal_projection
            if key in temporal
        }
        split_checks["current_temporal_projection_matches"] = all(
            current_temporal_projection[key]
            == split_checks["recomputed_temporal_projection"].get(key)
            for key in current_temporal_projection
        )
        if run_determinism:
            with tempfile.TemporaryDirectory(prefix="evovariant-tr-phase3-audit-") as temp_dir:
                temp_root = Path(temp_dir)
                first = build_phase3_artifacts(
                    t0,
                    t1,
                    output_dir=temp_root / "first",
                    t0_manifest=t0_manifest,
                    t1_manifest=t1_manifest,
                )
                second = build_phase3_artifacts(
                    t0,
                    t1,
                    output_dir=temp_root / "second",
                    t0_manifest=t0_manifest,
                    t1_manifest=t1_manifest,
                )
                artifact_names = (
                    "temporal_audit.json",
                    "split_manifest.json",
                    "locked_test_ids.json",
                )
                first_hashes = {
                    name: sha256_file(temp_root / "first" / name) for name in artifact_names
                }
                second_hashes = {
                    name: sha256_file(temp_root / "second" / name) for name in artifact_names
                }
                determinism = {
                    "status": "PASS" if first_hashes == second_hashes else "FAIL",
                    "first_hashes": first_hashes,
                    "second_hashes": second_hashes,
                    "fresh_matches_checked_in_split": (
                        first_hashes["split_manifest.json"]
                        == sha256_file(current_split_path)
                    ),
                    "fresh_summary_statuses": [first["status"], second["status"]],
                }
        else:
            determinism = {
                "status": "NOT_RUN",
                "reason": "deterministic rebuild disabled by caller",
            }
    else:
        split_checks = {
            "status": "NOT_RUN",
            "reason": "derived Phase 3 artifacts are incomplete",
        }
        determinism = {
            "status": "NOT_RUN",
            "reason": "derived Phase 3 artifacts are incomplete",
        }

    target = protocol.qa_checkpoint_validation_target_only
    target_values = {
        "t0_unique_vus": target.t0_unique_vus,
        "absent_at_t1": target.absent_at_t1,
        "not_definitive_at_t1": target.not_definitive_at_t1,
        "below_two_stars": target.below_two_stars,
        "final_temporal_n": target.final_temporal_n,
        "n_blb": target.n_blb,
        "n_plp": target.n_plp,
        "gene_labels": target.gene_labels,
        "reference_mismatch_count": target.reference_mismatch_among_final_candidates,
    }
    actual_values: dict[str, int] = {
        key: int(temporal[key]) for key in target_values
    }
    deltas = {key: actual_values[key] - int(target_values[key]) for key in target_values}

    normalized_ids = list(t0_ids) + [row["normalized_variant_id"] for row in final_records]
    invalid_ids = sorted(identity for identity in normalized_ids if not _ID_PATTERN.match(identity))
    release_dates_pass = (
        t0_source["verification_status"] == "PASS"
        and t1_source["verification_status"] == "PASS"
        and t0_source["release_date"] == t0_source["expected_release_date"]
        and t1_source["release_date"] == t1_source["expected_release_date"]
    )
    temporal_pass = (
        temporal["partition_matches_t0_denominator"]
        and temporal["t0_conflicting_duplicate_ids"] == 0
        and temporal["t1_conflicting_duplicate_ids"] == 0
        and temporal["reference_mismatch_count"] == 0
    )
    overlap_pass = (
        split_checks.get("status") == "PASS"
        and split_checks.get("development_locked_id_overlap") == 0
        and split_checks.get("t0_vus_development_id_overlap") == 0
    )
    source_hash_pass = (
        t0_source["verification_status"] == "PASS"
        and t1_source["verification_status"] == "PASS"
    )
    structural_id_pass = (
        not invalid_ids
        and t0_scan.stats["eligible_snv_rows"]
        >= t0_scan.filter_funnel["eligible_exact_vus_rows"]
    )
    date_pass = (
        t0_scan.date_counts["future_than_release"] == 0
        and t1_scan.date_counts["future_than_release"] == 0
    )
    reference = _reference_audit(root / "data/reference", final_records, root)
    gates = {
        "source_archive_hash_and_size": _gate(
            "PASS" if source_hash_pass else "FAIL",
            "both raw archives pass their manifest byte-size, SHA-256, and gzip verification",
        ),
        "release_dates": _gate(
            "PASS" if release_dates_pass else "FAIL",
            (
                "manifest release dates match the frozen t0/t1 protocol dates"
                if release_dates_pass
                else "manifest release dates or archive verification differ from protocol"
            ),
        ),
        "normalized_id_chromosome_ref_alt_snv": _gate(
            "PASS" if structural_id_pass else "FAIL",
            (
                "eligible records use GRCh38 canonical chromosome/position and "
                "single-base ACGT REF/ALT identities"
            ),
        ),
        "duplicate_and_conflict_resolution": _gate(
            "PASS" if temporal_pass else "FAIL",
            (
                "selected t0/t1 identities have no same-review conflicting labels "
                "and temporal categories partition cleanly"
            ),
        ),
        "review_filter_and_temporal_resolution": _gate(
            "PASS" if temporal_pass else "FAIL",
            (
                "t1 definitive labels use the frozen >=2-star gate and all matched "
                "outcomes are accounted for"
            ),
        ),
        "date_and_future_information": _gate(
            "PASS" if date_pass else "FAIL",
            (
                "no parsed LastEvaluated value in either archive is later than that "
                "archive's release date"
            ),
        ),
        "overlap_and_gene_leakage": _gate(
            "PASS" if overlap_pass else "FAIL",
            (
                "serialized split IDs and development gene groups are disjoint under "
                "the checked split policy"
            ),
        ),
        "deterministic_regeneration": _gate(
            determinism.get("status", "NOT_RUN"),
            "two fresh builds produce identical temporal, split, and locked-ID artifact hashes",
        ),
        "generated_hash_and_schema": _gate(
            (
                "PASS"
                if split_checks.get("status") == "PASS"
                else str(split_checks.get("status", "NOT_RUN"))
            ),
            "generated split manifest schema, hashes, and recomputed invariants agree",
        ),
        "independent_grch38_reference_base": _gate(
            str(reference["status"]),
            str(reference["reason"]),
        ),
        "handoff_target_identity_reconciliation": _gate(
            "BLOCKED_MISSING_TARGET_ID_SET",
            (
                "the validation-only target counts are recorded for comparison, but "
                "no target IDs/source records were supplied"
            ),
        ),
    }
    gate_statuses = [value["status"] for value in gates.values()]
    overall_status = "PASS" if all(status == "PASS" for status in gate_statuses) else "BLOCKED"

    payload: dict[str, Any] = {
        "artifact_id": "phase3-integrity-audit-20260921",
        "audit_date": datetime.now().date().isoformat(),
        "status": overall_status,
        "phase3_gate": "PASS" if overall_status == "PASS" else "BLOCKED",
        "protocol": {
            "path": "research/protocol/protocol.yaml",
            "t0_release_date": expected_t0.isoformat(),
            "t1_release_date": expected_t1.isoformat(),
            "assembly": protocol.temporal_design.reference_assembly,
            "min_review_stars": MIN_REVIEW_STARS,
            "primary_unit": protocol.temporal_design.primary_unit,
        },
        "source_archives": {"t0": t0_source, "t1": t1_source},
        "archive_scans": {
            "t0": {
                "stats": _counter(t0_scan.stats),
                "filter_funnel": _counter(t0_scan.filter_funnel),
                "rejection_reasons": _counter(t0_scan.rejection_reasons),
                "clinical_significance_counts": _counter(t0_scan.clinical_significance_counts),
                "review_status_counts": _counter(t0_scan.review_status_counts),
                "review_star_counts": _counter(t0_scan.review_star_counts),
                "chromosome_counts": _counter(t0_scan.chromosome_counts),
                "chromosome_alias_counts": _counter(t0_scan.chromosome_alias_counts),
                "gene_counts": _counter(t0_scan.gene_counts),
                "dates": _date_audit(t0_scan),
                "selected_vus_date_status": _selected_date_audit(
                    t0_scan.selected_records, expected_t0
                ),
            },
            "t1": {
                "stats": _counter(t1_scan.stats),
                "filter_funnel": _counter(t1_scan.filter_funnel),
                "rejection_reasons": _counter(t1_scan.rejection_reasons),
                "clinical_significance_counts": _counter(t1_scan.clinical_significance_counts),
                "review_status_counts": _counter(t1_scan.review_status_counts),
                "review_star_counts": _counter(t1_scan.review_star_counts),
                "chromosome_counts": _counter(t1_scan.chromosome_counts),
                "chromosome_alias_counts": _counter(t1_scan.chromosome_alias_counts),
                "gene_counts": _counter(t1_scan.gene_counts),
                "dates": _date_audit(t1_scan),
                "matched_t0_date_status": _selected_date_audit(
                    t1_scan.selected_records, expected_t1
                ),
            },
        },
        "temporal_resolution": temporal,
        "final_class_distribution": {"BLB": n_blb, "PLP": n_plp},
        "final_gene_distribution": {
            "gene_labeled": gene_labels,
            "gene_missing": final_gene_counts["<MISSING>"],
            "unique_gene_count": len([key for key in final_gene_counts if key != "<MISSING>"]),
            "top_20": dict(final_gene_counts.most_common(20)),
        },
        "split_and_leakage": split_checks,
        "deterministic_rebuild": determinism,
        "reference_base_audit": reference,
        "target_reconciliation": {
            "target_is_validation_only": True,
            "target_values": target_values,
            "actual_values": actual_values,
        "actual_minus_target": deltas,
            "target_id_set": "UNAVAILABLE",
            "decision": "DO_NOT_FORCE_TARGET_COUNTS",
        },
        "gates": gates,
        "limitations": [
            (
                "The handoff target ID/source set is unavailable, so identity-level "
                "reconciliation cannot be completed."
            ),
            (
                "The local frozen GRCh38 FASTA and .fai index are unavailable; assembly "
                "and t0/t1 identity reference checks are not a substitute for independent "
                "base validation."
            ),
            (
                "Locked labels are audited for temporal construction only and are not used "
                "to select development records or model settings."
            ),
        ],
    }
    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload

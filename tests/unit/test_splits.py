"""Tests for deterministic ML-extension data audits and gene-grouped splits."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from evovariant_tr.splits import (
    VALIDATION,
    CompactRecord,
    audit_temporal_cohort,
    build_development_split,
    build_phase3_artifacts,
    normalized_variant_id,
    validate_split_records,
)

HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated"
)


def _write_gz(path: Path, rows: list[list[str]]) -> Path:
    content = HEADER + "\n" + "\n".join("\t".join(row) for row in rows) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(content)
    return path


def _row(
    allele_id: str,
    significance: str,
    review_status: str,
    position: str,
    alternate: str,
    gene: str,
) -> list[str]:
    return [
        allele_id,
        "SNV",
        significance,
        review_status,
        "GRCh38",
        "1",
        position,
        position,
        "A",
        alternate,
        allele_id,
        "",
        "germline",
        gene,
        "",
        "",
    ]


def _record(identity: str, gene: str, label: int, source_hash: str) -> CompactRecord:
    return CompactRecord(
        normalized_variant_id=identity,
        assembly="GRCh38",
        chromosome=identity.split(":")[1],
        position_1based=int(identity.split(":")[2].split(":")[0]),
        reference="A",
        alternate="T",
        gene_symbol=gene,
        review_stars=2,
        category="pathogenic" if label else "benign",
        label=label,
        source_record_hash=source_hash,
    )


def test_normalized_id_strips_chr_prefix() -> None:
    assert normalized_variant_id("chr7", 100, "a", "t") == "GRCh38:7:100:A>T"


def test_gene_grouped_split_has_no_gene_overlap() -> None:
    records = [
        _record("GRCh38:1:1:A>T", "GENE_A", 1, "a" * 64),
        _record("GRCh38:1:2:A>T", "GENE_A", 0, "b" * 64),
        _record("GRCh38:2:1:A>T", "GENE_B", 1, "c" * 64),
        _record("GRCh38:2:2:A>T", "GENE_B", 0, "d" * 64),
        _record("GRCh38:3:1:A>T", "GENE_C", 1, "e" * 64),
    ]
    split_records, summary = build_development_split(
        records,
        {"GRCh38:9:9:A>T"},
        seed=20260814,
    )
    assert summary["invariants"]["train_validation_gene_overlap"] == 0
    assert summary["invariants"]["locked_test_overlap"] == 0
    assert validate_split_records(split_records, {"GRCh38:9:9:A>T"})[
        "normalized_id_overlap"
    ] == 0
    assert any(record["split"] == VALIDATION for record in split_records)


def test_temporal_audit_separates_absent_low_star_and_final(tmp_path: Path) -> None:
    t0 = _write_gz(
        tmp_path / "t0.txt.gz",
        [
            _row("1", "Uncertain significance", "reviewed by expert panel", "1", "T", "GENE_A"),
            _row("2", "Uncertain significance", "reviewed by expert panel", "2", "C", "GENE_B"),
            _row("3", "Uncertain significance", "reviewed by expert panel", "3", "G", "GENE_C"),
        ],
    )
    t1 = _write_gz(
        tmp_path / "t1.txt.gz",
        [
            _row("11", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE_A"),
            _row("12", "Benign", "no assertion criteria provided", "2", "C", "GENE_B"),
        ],
    )
    audit = audit_temporal_cohort(t0, t1)
    assert audit.t0_unique_vus == 3
    assert audit.absent_at_t1 == 1
    assert audit.below_two_stars == 1
    assert audit.final_temporal_n == 1
    assert audit.n_plp == 1
    assert audit.n_blb == 0


def test_phase3_artifacts_are_serialized_with_hashes(tmp_path: Path) -> None:
    t0 = _write_gz(
        tmp_path / "t0.txt.gz",
        [_row("1", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE_A")],
    )
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    t0_manifest = tmp_path / "t0.json"
    t1_manifest = tmp_path / "t1.json"
    t0_manifest.write_text(json.dumps({"name": "t0"}), encoding="utf-8")
    t1_manifest.write_text(json.dumps({"name": "t1"}), encoding="utf-8")
    summary = build_phase3_artifacts(
        t0,
        t1,
        output_dir=tmp_path / "out",
        t0_manifest=t0_manifest,
        t1_manifest=t1_manifest,
    )
    assert summary["status"] == "PASS"
    assert len(summary["source_manifest_hash"]) == 64
    assert (tmp_path / "out" / "split_manifest.json").is_file()

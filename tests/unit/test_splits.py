"""Tests for deterministic ML-extension data audits and gene-grouped splits."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from evovariant_tr.manifest import ManifestError, build_entry, build_manifest, write_manifest
from evovariant_tr.splits import (
    VALIDATION,
    CompactRecord,
    SnapshotStats,
    _assign_groups,
    _choose_best,
    _classification,
    _collect_t0,
    _group_key,
    _iter_compact_records,
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
            _row("4", "Uncertain significance", "reviewed by expert panel", "4", "C", "GENE_D"),
        ],
    )
    t1 = _write_gz(
        tmp_path / "t1.txt.gz",
        [
            _row("11", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE_A"),
            _row("12", "Benign", "no assertion criteria provided", "2", "C", "GENE_B"),
            _row(
                "13", "Uncertain significance", "no assertion criteria provided", "4", "C", "GENE_D"
            ),
        ],
    )
    audit = audit_temporal_cohort(t0, t1)
    assert audit.t0_unique_vus == 4
    assert audit.absent_at_t1 == 1
    assert audit.below_two_stars == 1
    assert audit.not_definitive_at_t1 == 1
    assert audit.final_temporal_n == 1
    assert audit.n_plp == 1
    assert audit.n_blb == 0


def test_phase3_artifacts_are_serialized_with_hashes(tmp_path: Path) -> None:
    t0 = _write_gz(
        tmp_path / "t0.txt.gz",
        [_row("1", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE_A")],
    )
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    t0_manifest = write_manifest(
        build_manifest("t0", tmp_path, [build_entry(t0.name, tmp_path)]),
        tmp_path / "t0.json",
    )
    t1_manifest = write_manifest(
        build_manifest("t1", tmp_path, [build_entry(t1.name, tmp_path)]),
        tmp_path / "t1.json",
    )
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


def test_phase3_artifacts_fail_closed_on_source_archive_mismatch(tmp_path: Path) -> None:
    t0 = _write_gz(
        tmp_path / "t0.txt.gz",
        [_row("1", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE_A")],
    )
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    t0_manifest = write_manifest(
        build_manifest("t0", tmp_path, [build_entry(t0.name, tmp_path)]),
        tmp_path / "t0.json",
    )
    t1_manifest = write_manifest(
        build_manifest("t1", tmp_path, [build_entry(t1.name, tmp_path)]),
        tmp_path / "t1.json",
    )
    t0.write_bytes(t0.read_bytes() + b"tampered")

    with pytest.raises(ManifestError, match="source archive verification failed"):
        build_phase3_artifacts(
            t0,
            t1,
            output_dir=tmp_path / "out",
            t0_manifest=t0_manifest,
            t1_manifest=t1_manifest,
        )


def test_split_helpers_cover_malformed_and_noncanonical_source_rows(
    tmp_path: Path,
) -> None:
    assert _classification("Benign") == ("benign", 0)
    assert _classification("not_provided") == ("other", None)

    empty = tmp_path / "empty.txt.gz"
    with gzip.open(empty, "wt", encoding="utf-8"):
        pass
    assert list(_iter_compact_records(empty, SnapshotStats())) == []

    wrong_assembly = _row("2", "Pathogenic", "reviewed by expert panel", "2", "T", "GENE")
    wrong_assembly[4] = "GRCh37"
    non_snv = _row("3", "Pathogenic", "reviewed by expert panel", "3", "T", "GENE")
    non_snv[1] = "Deletion"
    somatic = _row("4", "Pathogenic", "reviewed by expert panel", "4", "T", "GENE")
    somatic[12] = "somatic"
    bad_position = _row("5", "Pathogenic", "reviewed by expert panel", "5", "T", "GENE")
    bad_position[6] = "not-an-int"
    invalid_base = _row("6", "Pathogenic", "reviewed by expert panel", "6", "N", "GENE")
    short = ["too", "short"]
    source = tmp_path / "malformed.txt.gz"
    _write_gz(source, [short, wrong_assembly, non_snv, somatic, bad_position, invalid_base])
    stats = SnapshotStats()
    records = list(_iter_compact_records(source, stats))
    assert records == []
    assert stats.total_rows == 6
    assert stats.malformed_rows == 2
    assert stats.grch38_rows == 4
    assert stats.germline_snv_rows == 2


def test_split_helpers_choose_best_and_preserve_unknown_groups(tmp_path: Path) -> None:
    first = _record("GRCh38:1:1:A>T", "GENE_A", 1, "a" * 64)
    second = _record("GRCh38:1:1:A>T", "GENE_A", 0, "b" * 64)
    selected: dict[str, CompactRecord] = {}
    conflicts: set[str] = set()
    _choose_best(selected, first, conflicts)
    _choose_best(selected, second, conflicts)
    assert selected[first.normalized_variant_id] == second
    assert first.normalized_variant_id in conflicts
    assert _group_key(_record("GRCh38:1:2:A>T", "", 1, "c" * 64)).startswith("UNKNOWN:")

    all_train = _assign_groups(
        [
            _record("GRCh38:1:3:A>T", "GENE_A", 1, "d" * 64),
            _record("GRCh38:1:4:A>T", "GENE_B", 0, "e" * 64),
        ],
        seed=1,
        validation_fraction=0.0,
    )
    assert VALIDATION in all_train.values()

    duplicate_records = [
        {"normalized_variant_id": "same", "split": "TRAIN", "gene_symbol": "GENE"},
        {"normalized_variant_id": "same", "split": "TRAIN", "gene_symbol": "GENE"},
    ]
    invariants = validate_split_records(duplicate_records, set())
    assert invariants["duplicate_normalized_ids"] == 1


def test_split_helpers_cover_temporal_categories_and_overlap(tmp_path: Path) -> None:
    overlap_path = _write_gz(
        tmp_path / "overlap.txt.gz",
        [
            _row("1", "Uncertain significance", "reviewed by expert panel", "1", "T", "GENE"),
            _row("2", "Pathogenic", "reviewed by expert panel", "1", "T", "GENE"),
            _row("3", "Pathogenic", "criteria provided, single submitter", "2", "C", "GENE"),
        ],
    )
    vus, definitive, stats, overlap, _ = _collect_t0(overlap_path)
    assert len(vus) == 1
    assert len(definitive) == 0
    assert overlap == 1
    assert stats.definitive_rows == 1

    t1_rows = [
        _row("20", "Benign", "no assertion criteria", "11", "T", "GENE_B"),
        _row("21", "Uncertain significance", "reviewed by expert panel", "12", "T", "GENE_C"),
        _row("22", "Benign", "reviewed by expert panel", "13", "T", "GENE_CHANGED"),
        _row("23", "Pathogenic", "reviewed by expert panel", "14", "T", "GENE_E"),
        _row("24", "Benign", "reviewed by expert panel", "14", "T", "GENE_E"),
        _row("25", "Pathogenic", "reviewed by expert panel", "14", "T", "GENE_E"),
    ]
    alternate_reference = _row(
        "26", "Pathogenic", "reviewed by expert panel", "14", "T", "GENE_E"
    )
    alternate_reference[8] = "C"
    t1_rows.append(alternate_reference)
    audit = audit_temporal_cohort(
        _write_gz(tmp_path / "temporal-t0-copy.txt.gz", [
            _row("10", "Uncertain significance", "reviewed by expert panel", "10", "T", "GENE_A"),
            _row("11", "Uncertain significance", "reviewed by expert panel", "11", "T", "GENE_B"),
            _row("12", "Uncertain significance", "reviewed by expert panel", "12", "T", "GENE_C"),
            _row("13", "Uncertain significance", "reviewed by expert panel", "13", "T", "GENE_D"),
            _row("14", "Uncertain significance", "reviewed by expert panel", "14", "T", "GENE_E"),
        ]),
        _write_gz(tmp_path / "temporal-t1.txt.gz", t1_rows),
    )
    assert audit.absent_at_t1 == 1
    assert audit.below_two_stars == 1
    assert audit.not_definitive_at_t1 == 1
    assert audit.n_blb >= 1
    assert audit.n_plp >= 1
    assert audit.gene_mismatch_count == 1
    assert audit.reference_mismatch_count == 1
    assert audit.t1_conflicting_duplicate_ids >= 1

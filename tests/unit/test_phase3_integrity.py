"""Unit tests for the detailed Phase 3 integrity audit helpers."""

from __future__ import annotations

import gzip
import json
import shutil
from datetime import date
from pathlib import Path

from evovariant_tr.manifest import build_entry, build_manifest, write_manifest
from evovariant_tr.phase3_integrity import (
    _display_path,
    _parse_last_evaluated,
    _reference_audit,
    _scan_archive,
    _schema_valid,
    _selected_date_audit,
    build_phase3_integrity_audit,
)
from evovariant_tr.splits import build_phase3_artifacts

HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated"
)


def _row(
    allele_id: str,
    significance: str,
    review_status: str,
    position: str,
    reference: str,
    alternate: str,
    gene: str,
    *,
    assembly: str = "GRCh38",
    variant_type: str = "SNV",
    last_evaluated: str = "Jan 01, 2025",
) -> list[str]:
    return [
        allele_id,
        variant_type,
        significance,
        review_status,
        assembly,
        "1",
        position,
        position,
        reference,
        alternate,
        allele_id,
        "",
        "germline",
        gene,
        "",
        last_evaluated,
    ]


def _write_gz(path: Path, rows: list[list[str]]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(HEADER + "\n")
        for row in rows:
            handle.write("\t".join(row) + "\n")
    return path


def test_last_evaluated_parser_accepts_archive_formats() -> None:
    assert _parse_last_evaluated("2025-01-02") == (date(2025, 1, 2), "valid")
    assert _parse_last_evaluated("Jan 02, 2025") == (date(2025, 1, 2), "valid")
    assert _parse_last_evaluated("-") == (None, "missing")
    assert _parse_last_evaluated("not-a-date") == (None, "invalid")


def test_archive_scan_accounts_filter_funnel_and_selected_vus(tmp_path: Path) -> None:
    somatic = _row(
        "5", "Uncertain significance", "reviewed by expert panel",
        "14", "A", "T", "GENE_E",
    )
    somatic[12] = "somatic"
    missing_chromosome = _row(
        "6", "Uncertain significance", "reviewed by expert panel",
        "15", "A", "T", "GENE_F",
    )
    missing_chromosome[5] = "-"
    mismatched_stop = _row(
        "7", "Uncertain significance", "reviewed by expert panel",
        "16", "A", "T", "GENE_G",
    )
    mismatched_stop[7] = "17"
    chr_row = _row(
        "13", "Uncertain significance", "reviewed by expert panel",
        "21", "A", "T", "GENE_M",
    )
    chr_row[5] = "chr1"
    rows = [
        _row(
            "1", "Uncertain significance", "reviewed by expert panel",
            "10", "A", "T", "GENE_A",
        ),
        _row(
            "2", "Uncertain significance", "reviewed by expert panel",
            "11", "A", "N", "GENE_B",
        ),
        _row(
            "3", "Uncertain significance", "reviewed by expert panel",
            "12", "A", "T", "GENE_C", assembly="GRCh37",
        ),
        somatic,
        _row(
            "8", "Uncertain significance", "reviewed by expert panel",
            "18", "A", "T", "GENE_H", variant_type="Deletion",
        ),
        _row(
            "9", "Uncertain significance", "reviewed by expert panel",
            "bad", "A", "T", "GENE_I",
        ),
        missing_chromosome,
        _row(
            "10", "Uncertain significance", "reviewed by expert panel",
            "0", "A", "T", "GENE_J",
        ),
        mismatched_stop,
        _row(
            "11", "Uncertain significance", "reviewed by expert panel",
            "19", "AT", "T", "GENE_K",
        ),
        _row(
            "12", "Uncertain significance", "reviewed by expert panel",
            "20", "A", "A", "GENE_L",
        ),
        chr_row,
        _row("14", "Pathogenic", "reviewed by expert panel", "13", "A", "T", "GENE_D"),
        ["too", "short"],
    ]
    archive = _write_gz(
        tmp_path / "t0.txt.gz",
        rows,
    )
    scan = _scan_archive(archive, role="t0", release_date=date(2025, 1, 2))

    assert scan.filter_funnel["exact_vus_rows"] == 12
    assert scan.filter_funnel["eligible_exact_vus_rows"] == 2
    assert scan.rejection_reasons["non_acgt_allele"] == 1
    assert scan.rejection_reasons["exact_vus_not_grch38"] == 1
    assert scan.rejection_reasons["exact_vus_not_germline"] == 1
    assert scan.rejection_reasons["exact_vus_not_snv"] == 1
    assert scan.rejection_reasons["coordinate_parse"] == 1
    assert scan.rejection_reasons["missing_chromosome"] == 1
    assert scan.rejection_reasons["position_less_than_one"] == 1
    assert scan.rejection_reasons["stop_differs_from_position"] == 1
    assert scan.rejection_reasons["non_single_base_allele"] == 1
    assert scan.rejection_reasons["reference_equals_alternate"] == 1
    assert len(scan.selected_records) == 2
    assert scan.date_counts["future_than_release"] == 0
    assert scan.chromosome_alias_counts["unprefixed"] == 2
    assert scan.chromosome_alias_counts["chr_prefixed"] == 1


def test_archive_scan_tracks_t1_conflicts_and_reference_coordinate_mismatch(
    tmp_path: Path,
) -> None:
    t0 = _scan_archive(
        _write_gz(
            tmp_path / "t0.txt.gz",
            [
                _row(
                    "1", "Uncertain significance", "reviewed by expert panel",
                    "10", "A", "T", "GENE_A",
                )
            ],
        ),
        role="t0",
        release_date=date(2025, 1, 2),
    )
    identity = next(iter(t0.selected_records))
    coordinate = next(
        (
            row.record.chromosome,
            row.record.position_1based,
            row.record.alternate,
        )
        for row in t0.selected_records.values()
    )
    t1 = _scan_archive(
        _write_gz(
            tmp_path / "t1.txt.gz",
            [
                _row(
                    "2",
                    "Pathogenic",
                    "reviewed by expert panel",
                    "10",
                    "A",
                    "T",
                    "GENE_A",
                    last_evaluated="Aug 01, 2026",
                ),
                _row(
                    "3",
                    "Benign",
                    "reviewed by expert panel",
                    "10",
                    "A",
                    "T",
                    "GENE_A",
                    last_evaluated="Aug 01, 2026",
                ),
                _row(
                    "4",
                    "Pathogenic",
                    "reviewed by expert panel",
                    "10",
                    "C",
                    "T",
                    "GENE_A",
                    last_evaluated="Aug 01, 2026",
                ),
            ],
        ),
        role="t1",
        release_date=date(2026, 8, 6),
        target_ids={identity},
        coordinate_alt_keys={coordinate},
    )

    assert t1.stats["matched_t0_ids_rows"] == 2
    assert identity in t1.conflicting_ids
    assert t1.coordinate_alt_refs[coordinate] == {"A", "C"}
    assert t1.date_counts["future_than_release"] == 0


def test_tiny_repository_audit_rebuilds_and_records_external_gates(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    t0 = repo / "data/raw/clinvar/variant_summary_2025-01.txt.gz"
    t1 = repo / "data/raw/clinvar/variant_summary_2026-08.txt.gz"
    t0.parent.mkdir(parents=True)
    (repo / "research/data_manifests").mkdir(parents=True)
    (repo / "research/protocol").mkdir(parents=True)
    (repo / "research/schemas").mkdir(parents=True)
    source_root = Path(__file__).resolve().parents[2]
    shutil.copy2(
        source_root / "research/protocol/protocol.yaml",
        repo / "research/protocol/protocol.yaml",
    )
    shutil.copy2(
        source_root / "research/schemas/split_manifest.schema.json",
        repo / "research/schemas/split_manifest.schema.json",
    )
    _write_gz(
        t0,
        [
            _row(
                "1", "Uncertain significance", "reviewed by expert panel",
                "10", "A", "T", "GENE_A",
            ),
            _row(
                "2", "Uncertain significance", "reviewed by expert panel",
                "11", "A", "T", "GENE_B",
            ),
            _row(
                "3", "Uncertain significance", "reviewed by expert panel",
                "12", "A", "T", "GENE_C",
            ),
            _row(
                "4", "Uncertain significance", "reviewed by expert panel",
                "13", "A", "T", "GENE_D",
            ),
            _row(
                "5", "Uncertain significance", "reviewed by expert panel",
                "14", "A", "T", "-",
            ),
            _row(
                "6", "Benign", "reviewed by expert panel",
                "20", "C", "T", "GENE_B",
            ),
        ],
    )
    _write_gz(
        t1,
        [
            _row(
                "7", "Pathogenic", "reviewed by expert panel",
                "10", "A", "T", "GENE_CHANGED",
                last_evaluated="Aug 07, 2026",
            ),
            _row(
                "8", "Pathogenic", "reviewed by expert panel",
                "10", "C", "T", "GENE_A",
                last_evaluated="Aug 01, 2026",
            ),
            _row(
                "9", "Benign", "criteria provided, single submitter",
                "12", "A", "T", "GENE_C",
                last_evaluated="Aug 01, 2026",
            ),
            _row(
                "10", "Uncertain significance", "reviewed by expert panel",
                "13", "A", "T", "GENE_D",
                last_evaluated="Aug 01, 2026",
            ),
            _row(
                "11", "Benign", "reviewed by expert panel",
                "14", "A", "T", "-",
                last_evaluated="Aug 01, 2026",
            ),
        ],
    )
    t0_manifest = write_manifest(
        build_manifest("t0", t0.parent, [build_entry(t0.name, t0.parent)]),
        repo / "research/data_manifests/clinvar_t0.json",
    )
    t1_manifest = write_manifest(
        build_manifest("t1", t1.parent, [build_entry(t1.name, t1.parent)]),
        repo / "research/data_manifests/clinvar_t1.json",
    )
    build_phase3_artifacts(
        t0,
        t1,
        output_dir=repo / "data/derived/ml_extension/phase3",
        t0_manifest=t0_manifest,
        t1_manifest=t1_manifest,
    )

    output = repo / "artifacts/phase3-integrity.json"
    audit = build_phase3_integrity_audit(
        repo_root=repo,
        output_path=output,
        run_determinism=True,
    )

    assert audit["status"] == "BLOCKED"
    assert audit["temporal_resolution"]["final_temporal_n"] == 2
    assert audit["temporal_resolution"]["absent_at_t1"] == 1
    assert audit["temporal_resolution"]["below_two_stars"] == 1
    assert audit["temporal_resolution"]["not_definitive_at_t1"] == 1
    assert audit["temporal_resolution"]["reference_mismatch_count"] == 1
    assert audit["temporal_resolution"]["gene_mismatch_count"] == 1
    assert audit["deterministic_rebuild"]["status"] == "PASS"
    assert audit["split_and_leakage"]["status"] == "PASS"
    assert audit["reference_base_audit"]["status"] == "NOT_RUN"
    assert audit["gates"]["date_and_future_information"]["status"] == "FAIL"
    assert json.loads(output.read_text(encoding="utf-8"))["phase3_gate"] == "BLOCKED"

    cli_output = repo / "artifacts/phase3-integrity-cli.json"
    from evovariant_tr.cli import main

    assert (
        main(
            [
                "phase3-integrity-audit",
                "--repo-root",
                str(repo),
                "--output",
                str(cli_output),
                "--skip-determinism",
            ]
        )
        == 0
    )
    assert cli_output.is_file()


def test_reference_audit_passes_with_indexed_fixture(tmp_path: Path) -> None:
    reference_dir = tmp_path / "data/reference"
    reference_dir.mkdir(parents=True)
    fasta = reference_dir / "Homo_sapiens_assembly38.fasta"
    fasta.write_text(">chr1\nACGT\n", encoding="ascii")
    (reference_dir / "Homo_sapiens_assembly38.fasta.fai").write_text(
        "chr1\t4\t6\t4\t5\n", encoding="ascii"
    )
    result = _reference_audit(
        reference_dir,
        [{"chromosome": "1", "position_1based": 1, "reference": "A"}],
        tmp_path,
    )
    assert result["status"] == "PASS"
    assert result["checked_variant_count"] == 1

    failed = _reference_audit(
        reference_dir,
        [
            {"chromosome": "1", "position_1based": 2, "reference": "A"},
            {"chromosome": "1", "position_1based": 9, "reference": "A"},
        ],
        tmp_path,
    )
    assert failed["status"] == "FAIL"
    assert failed["mismatch_count"] == 1
    assert failed["missing_coordinate_count"] == 1


def test_phase3_integrity_small_helpers_cover_path_and_schema_failures(
    tmp_path: Path,
) -> None:
    assert _display_path(tmp_path / "inside.txt", tmp_path) == "inside.txt"
    outside = Path("/tmp/phase3-integrity-outside.txt")
    assert _display_path(outside, tmp_path) == outside.as_posix()
    assert _selected_date_audit({}, date(2020, 1, 1)) == {"future_than_release": 0}
    valid, error = _schema_valid(
        tmp_path / "missing.json",
        {},
        tmp_path / "missing.schema.json",
    )
    assert valid is False
    assert error is not None

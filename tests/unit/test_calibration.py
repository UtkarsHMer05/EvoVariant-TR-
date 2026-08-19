"""Tests for calibration.py — Milestone 38 calibration cohort."""

from __future__ import annotations

import gzip
from datetime import date
from pathlib import Path

import pytest

from evovariant_tr.calibration import (
    CalibrationOutcome,
    _load_definitive_snapshot,
    build_calibration_cohort,
    check_disjoint,
    gene_group_splits,
)

HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated"
)


def _write_gz(path: Path, rows: list[list[str]]) -> Path:
    content = HEADER.lstrip("#") + "\n"
    for row in rows:
        content += "\t".join(row) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def t0_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Benign",
         "criteria provided, multiple submitters, no conflicts", "GRCh38",
         "7", "200", "200", "C", "G", "102", "RCV000000002", "germline",
         "BRCA1", "222", "2024-03-20"],
        ["3", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "300", "300", "G", "A",
         "103", "RCV000000003", "germline", "BRCA1", "333", "2024-06-10"],
        ["4", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "400", "400", "T", "C",
         "104", "RCV000000004", "germline", "PALB2", "444", "2024-01-01"],
    ]
    return _write_gz(tmp_path / "t0.txt.gz", rows)


@pytest.fixture
def t1_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "201", "RCV000000201", "germline", "BRCA1", "111", "2026-08-01"],
        ["2", "single nucleotide variant", "Benign",
         "criteria provided, multiple submitters, no conflicts", "GRCh38",
         "7", "200", "200", "C", "G", "202", "RCV000000202", "germline",
         "BRCA1", "222", "2026-08-01"],
        ["5", "single nucleotide variant", "Benign",
         "reviewed by expert panel", "GRCh38", "7", "500", "500", "A", "C",
         "205", "RCV000000205", "germline", "CHEK2", "555", "2026-08-01"],
    ]
    return _write_gz(tmp_path / "t1.txt.gz", rows)


def test_calibration_outcome_values():
    assert CalibrationOutcome.STABLE.value == "stable"
    assert CalibrationOutcome.CHANGED_TO_PATHOGENIC.value == "changed_to_pathogenic"
    assert CalibrationOutcome.CHANGED_TO_BENIGN.value == "changed_to_benign"
    assert CalibrationOutcome.CHANGED_TO_VUS.value == "changed_to_vus"
    assert CalibrationOutcome.EXCLUDED.value == "excluded"


def test_build_calibration_cohort_basic(t0_file, t1_file):
    """Build calibration cohort from synthetic data."""
    cohort = build_calibration_cohort(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )

    # t0 definitive: alleles 1 (Path), 2 (Benign), 4 (Path)
    assert cohort.t0_definitive == 3
    assert cohort.n_total == 3

    # Alleles 1 and 2 are stable, allele 4 has no t1 record
    assert cohort.stable == 2
    assert cohort.excluded_no_t1 == 1

    counts = cohort.class_counts()
    assert counts["stable"] == 2
    assert counts["excluded"] == 1


def test_build_calibration_cohort_empty(tmp_path):
    t0 = _write_gz(tmp_path / "t0.txt.gz", [])
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.n_total == 0
    assert cohort.t0_definitive == 0


def test_build_calibration_cohort_to_dict(t0_file, t1_file):
    cohort = build_calibration_cohort(t0_file, t1_file)
    d = cohort.to_dict()
    assert d["n_total"] == 3
    assert d["t0_definitive"] == 3
    assert d["n_stable"] == 2
    assert "class_counts" in d


def test_check_disjoint(tmp_path: Path):
    """Verify VUS and definitive cohorts are disjoint at t0."""
    rows = [
        ["1", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "200", "200", "C", "G",
         "102", "RCV000000002", "germline", "BRCA1", "222", "2024-03-20"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    result = check_disjoint(t0)
    assert result["vus_count"] == 1
    assert result["definitive_count"] == 1
    assert result["overlap_count"] == 0
    assert result["is_disjoint"] is True


def test_check_disjoint_empty(tmp_path: Path):
    t0 = _write_gz(tmp_path / "t0.txt.gz", [])
    result = check_disjoint(t0)
    assert result["vus_count"] == 0
    assert result["definitive_count"] == 0
    assert result["is_disjoint"] is True


def test_calibration_excludes_somatic(tmp_path: Path):
    """Somatic variants should not be in the calibration cohort."""
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "somatic", "BRCA1", "111", "2024-01-15"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.t0_definitive == 0


def test_calibration_excludes_low_stars(tmp_path: Path):
    """Variants with <2 review stars should not be in the calibration cohort."""
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "no assertion criteria provided", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.t0_definitive == 0


def test_calibration_vus_excluded_from_cohort(tmp_path: Path):
    """VUS variants should not appear in the calibration cohort."""
    rows = [
        ["1", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    t1 = _write_gz(tmp_path / "t1.txt.gz", rows)
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.t0_definitive == 0


def test_calibration_changed_to_pathogenic(tmp_path: Path):
    """A definitional variant that changes classification should be tracked."""
    t0_rows = [
        ["1", "single nucleotide variant", "Benign",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
    ]
    t1_rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "201", "RCV000000201", "germline", "BRCA1", "111", "2026-08-01"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", t0_rows)
    t1 = _write_gz(tmp_path / "t1.txt.gz", t1_rows)
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.n_total == 1
    assert cohort.changed == 1
    assert cohort.stable == 0
    assert cohort.variants[0].outcome == CalibrationOutcome.CHANGED_TO_PATHOGENIC


def test_calibration_changed_to_vus(tmp_path: Path):
    """A definitive variant that becomes VUS at t1."""
    t0_rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
    ]
    t1_rows = [
        ["1", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "201", "RCV000000201", "germline", "BRCA1", "111", "2026-08-01"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", t0_rows)
    t1 = _write_gz(tmp_path / "t1.txt.gz", t1_rows)
    cohort = build_calibration_cohort(t0, t1)
    assert cohort.variants[0].outcome == CalibrationOutcome.CHANGED_TO_VUS
    assert cohort.changed == 1


def test_gene_group_splits_basic(tmp_path: Path):
    """Test gene group split computation."""

    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Benign",
         "reviewed by expert panel", "GRCh38", "7", "200", "200", "C", "G",
         "102", "RCV000000002", "germline", "BRCA1", "222", "2024-03-20"],
        ["3", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "17", "300", "300", "G", "A",
         "103", "RCV000000003", "germline", "BRCA2", "333", "2024-06-10"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    result = gene_group_splits(t0)
    assert result["n_genes"] == 2
    assert "BRCA1" in result["genes"]
    assert "BRCA2" in result["genes"]
    assert result["genes"]["BRCA1"]["total_variants"] == 2
    assert result["genes"]["BRCA1"]["pathogenic"] == 1
    assert result["genes"]["BRCA1"]["benign"] == 1


def test_gene_group_splits_empty(tmp_path: Path):

    t0 = _write_gz(tmp_path / "t0.txt.gz", [])
    result = gene_group_splits(t0)
    assert result["n_genes"] == 0
    assert result["total_definitive_variants"] == 0


def test_gene_group_splits_excludes_low_star(tmp_path: Path):

    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "no assertion criteria provided", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    result = gene_group_splits(t0)
    assert result["n_genes"] == 0


def test_load_definitive_snapshot_filters_vus(tmp_path: Path):
    """Only definitive (not VUS) records should be in the snapshot."""
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "200", "200", "C", "G",
         "102", "RCV000000002", "germline", "BRCA1", "222", "2024-03-20"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    data, counts = _load_definitive_snapshot(t0)
    assert len(data) == 1
    assert counts["total"] == 2
    assert counts["germline_snv"] == 2

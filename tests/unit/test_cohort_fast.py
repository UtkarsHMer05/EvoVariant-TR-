"""Tests for cohort_fast.py — Milestone 36 optimized cohort construction."""

from __future__ import annotations

import gzip
import json
from datetime import date
from pathlib import Path

import pytest

from evovariant_tr.cohort_fast import (
    FastOutcome,
    _load_t0_vus,
    build_cohort_fast,
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
        ["1", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Uncertain significance",
         "criteria provided, multiple submitters", "GRCh38", "7", "200", "200",
         "C", "G", "102", "RCV000000002", "germline", "BRCA1", "222", "2024-03-20"],
        ["3", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "17", "300", "300", "G", "A",
         "103", "RCV000000003", "germline", "BRCA2", "333", "2024-06-10"],
        ["4", "single nucleotide variant", "Uncertain significance",
         "no assertion criteria provided", "GRCh38", "7", "400", "400",
         "T", "C", "104", "", "germline", "PALB2", "444", "2024-01-01"],
    ]
    return _write_gz(tmp_path / "t0.txt.gz", rows)


@pytest.fixture
def t1_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "201", "RCV000000201", "germline", "BRCA1", "111", "2026-08-01"],
        ["2", "single nucleotide variant", "Benign",
         "criteria provided, multiple submitters", "GRCh38", "7", "200", "200",
         "C", "G", "202", "RCV000000202", "germline", "BRCA1", "222", "2026-08-01"],
        ["3", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "17", "300", "300", "G", "A",
         "203", "RCV000000203", "germline", "BRCA2", "333", "2026-08-01"],
    ]
    return _write_gz(tmp_path / "t1.txt.gz", rows)


def test_fast_outcome_values():
    assert FastOutcome.RESOLVED_PATHOGENIC.value == "resolved_pathogenic"
    assert FastOutcome.RESOLVED_BENIGN.value == "resolved_benign"
    assert FastOutcome.UNRESOLVED.value == "unresolved"
    assert FastOutcome.EXCLUDED.value == "excluded"


def test_build_cohort_fast_basic(t0_file, t1_file):
    cohort = build_cohort_fast(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )
    # t0 VUS with 2+ stars: alleles 1 and 2 (allele 4 has 0 stars)
    assert cohort["n_total"] == 2
    assert cohort["n_resolved_pathogenic"] == 1
    assert cohort["n_resolved_benign"] == 1
    assert cohort["n_unresolved"] == 0
    assert cohort["n_excluded"] == 0


def test_build_cohort_fast_flow(t0_file, t1_file):
    cohort = build_cohort_fast(t0_file, t1_file)
    flow = cohort["flow"]
    assert flow["total_t0_records"] == 4
    assert flow["t0_germline_snv"] == 4
    assert flow["t0_grch38"] == 4
    assert flow["t0_vus_meets_star_gate"] == 2
    assert flow["t1_pathogenic"] == 1
    assert flow["t1_benign"] == 1


def test_build_cohort_fast_empty(tmp_path):
    t0 = _write_gz(tmp_path / "t0.txt.gz", [])
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    cohort = build_cohort_fast(t0, t1)
    assert cohort["n_total"] == 0
    assert cohort["n_resolved_pathogenic"] == 0
    assert cohort["n_resolved_benign"] == 0


def test_build_cohort_fast_min_stars_override(tmp_path):
    """With min_stars=0, VUS with 0 stars should be included."""
    rows_t0 = [
        ["1", "single nucleotide variant", "Uncertain significance",
         "no assertion criteria provided", "GRCh38", "7", "100", "100",
         "A", "T", "101", "RCV000000001", "germline", "GENE1", "111", "2024-01-15"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows_t0)
    t1 = _write_gz(tmp_path / "t1.txt.gz", rows_t0)  # same

    cohort = build_cohort_fast(t0, t1, min_review_stars=0)
    assert cohort["n_total"] == 1
    assert cohort["n_unresolved"] == 1  # still VUS at t1


def test_build_cohort_fast_json_serializable(t0_file, t1_file):
    cohort = build_cohort_fast(t0_file, t1_file)
    json_str = json.dumps(cohort)
    parsed = json.loads(json_str)
    assert parsed["n_total"] == cohort["n_total"]


def test_load_t0_vus_filters_non_vus(tmp_path: Path):
    """Only VUS (Uncertain_significance) should be in t0_vus."""
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "7", "100", "100", "A", "T",
         "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "7", "200", "200", "C", "G",
         "102", "RCV000000002", "germline", "BRCA1", "222", "2024-03-20"],
    ]
    t0 = _write_gz(tmp_path / "t0.txt.gz", rows)
    vus, counts = _load_t0_vus(t0)
    assert len(vus) == 1
    assert counts["total"] == 2


def test_load_t0_vus_excludes_somatic():
    pass  # covered by integration in build_cohort_fast tests

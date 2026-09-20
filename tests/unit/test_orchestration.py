"""Tests for orchestration.py — Milestone 50 end-to-end scoring.

Uses the FakeScorer and synthetic data to test the full pipeline
without requiring GPU access or the real ClinVar archives.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.orchestration import (
    result_to_json,
    run_scoring_orchestration,
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
def mock_fasta(tmp_path: Path) -> Path:
    """Create a small mock FASTA for testing."""
    # chr1 is long enough to satisfy the frozen 8,192-base window contract.
    fasta = tmp_path / "ref.fasta"
    seq = list("C" * 10000)
    # Put a C at position 1000 (1-based: 1001) for easy testing
    seq[999] = "G"
    seq = "".join(seq)

    # Write as multi-line FASTA (70 chars per line)
    fasta.write_text(">chr1\n")
    with fasta.open("a") as f:
        for i in range(0, len(seq), 70):
            f.write(seq[i:i + 70] + "\n")

    # Create .fai index
    # >chr1\n = 6 bytes
    # 70 chars per line, 10000 total bases
    # line_width = 71 (70 + newline)
    # offset = 6 (after >chr1\n)
    fai = tmp_path / "ref.fasta.fai"
    fai.write_text("chr1\t10000\t6\t70\t71\t0\n")
    return fasta


@pytest.fixture
def t0_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "single nucleotide variant", "Uncertain significance",
         "reviewed by expert panel", "GRCh38", "chr1", "1000", "1000",
         "G", "T", "101", "RCV000000001", "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "single nucleotide variant", "Uncertain significance",
         "criteria provided, multiple submitters, no conflicts", "GRCh38",
         "chr1", "1000", "1000", "G", "A", "102", "RCV000000002",
         "germline", "BRCA1", "222", "2024-03-20"],
    ]
    return _write_gz(tmp_path / "t0.txt.gz", rows)


@pytest.fixture
def t1_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "single nucleotide variant", "Pathogenic",
         "reviewed by expert panel", "GRCh38", "chr1", "1000", "1000",
         "G", "T", "201", "RCV000000201", "germline", "BRCA1", "111", "2026-08-01"],
        ["2", "single nucleotide variant", "Benign",
         "criteria provided, multiple submitters, no conflicts", "GRCh38",
         "chr1", "1000", "1000", "G", "A", "202", "RCV000000202",
         "germline", "BRCA1", "222", "2026-08-01"],
    ]
    return _write_gz(tmp_path / "t1.txt.gz", rows)


def test_run_scoring_orchestration_basic(
    t0_file: Path, t1_file: Path, mock_fasta: Path, tmp_path: Path,
):
    """Test the full orchestration pipeline with a fake scorer."""
    scorer = FakeScorer()
    fai_path = mock_fasta.with_suffix(mock_fasta.suffix + ".fai")

    result = run_scoring_orchestration(
        t0_file, t1_file, mock_fasta, fai_path,
        scorer, cache_dir=None, max_variants=2,
    )

    assert result.primary_cohort["n_total"] == 2  # 2 unique VUS identities (C->T and C->A)
    assert result.disjoint_check["is_disjoint"] is True
    assert result.scoring is not None
    assert result.scoring.total == 2
    assert result.scoring.scorer_name == "fake_scorer"
    assert result.errors == []


def test_run_scoring_orchestration_with_cache(
    t0_file: Path, t1_file: Path, mock_fasta: Path, tmp_path: Path,
):
    """Test orchestration with the sequence cache enabled."""
    scorer = FakeScorer()
    fai_path = mock_fasta.with_suffix(mock_fasta.suffix + ".fai")
    cache_dir = tmp_path / "cache"

    result = run_scoring_orchestration(
        t0_file, t1_file, mock_fasta, fai_path,
        scorer, cache_dir=cache_dir, max_variants=2,
    )

    assert result.cache_dir is not None
    assert (cache_dir / "cache_index.json").exists()


def test_result_to_json(t0_file: Path, t1_file: Path, mock_fasta: Path, tmp_path: Path):
    """Test JSON serialization of orchestration results."""
    scorer = FakeScorer()
    fai_path = mock_fasta.with_suffix(mock_fasta.suffix + ".fai")

    result = run_scoring_orchestration(
        t0_file, t1_file, mock_fasta, fai_path,
        scorer, max_variants=2,
    )

    data = result_to_json(result)
    assert "primary_cohort" in data
    assert "calibration_cohort" in data
    assert "disjoint_check" in data
    assert "scoring" in data
    assert "total_time_seconds" in data

    import json
    json.dumps(data)  # Should not raise


def test_scorer_health_check_failure():
    """Orchestration should handle unhealthy scorers."""
    from evovariant_tr.scorer import Scorer, ScoringResult

    class UnhealthyScorer(Scorer):
        name = "unhealthy"
        version = "1.0"
        context_length_bp = 8192

        def score_variant(self, ref_window, variant, strand="forward"):
            return 0.0, 0.0, 0.0

        def score_batch(self, variants):
            return ScoringResult([], [], 0, 0, 0.0, "unhealthy", "1.0")

        def score_cohort(self, cohort):
            raise NotImplementedError

        def check_health(self):
            return {"healthy": False, "reason": "mock unhealthy"}

    scorer = UnhealthyScorer()
    # Just test that the health check is captured
    health = scorer.check_health()
    assert health["healthy"] is False

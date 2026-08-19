"""Scientific validation tests — gated, slow.

Run with: pytest --run-scientific

These tests validate the scientific pipeline end-to-end using deterministic
fake scorers and synthetic fixtures, avoiding any GPU/paid compute requirements.
"""

from __future__ import annotations

import pytest

from evovariant_tr.abstention import compute_abstention_analysis, compute_risk_coverage_curve
from evovariant_tr.error_analysis import compute_error_analysis, perform_bias_audit
from evovariant_tr.metrics import compute_full_metrics
from evovariant_tr.scoring_record import ScoringRecord


def _make_scoring_records(
    n_positive: int = 50,
    n_negative: int = 50,
    score_base: float = 10.0,
) -> list[ScoringRecord]:
    records = []
    for i in range(n_positive):
        records.append(ScoringRecord(
            chrom="chr1", start=100 + i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=score_base + (i % 5),
            gene_symbol="GENE1",
            outcome="resolved_pathogenic",
        ))
    for i in range(n_negative):
        records.append(ScoringRecord(
            chrom="chr1", start=200 + i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=-score_base - (i % 5),
            gene_symbol="GENE1",
            outcome="resolved_benign",
        ))
    return records


@pytest.mark.scientific
def test_full_metrics_pipeline():
    """M79: Full metrics pipeline produces valid results."""
    records = _make_scoring_records(50, 50)
    metrics = compute_full_metrics(records, n_bootstrap=20)
    assert metrics.binary.auc_roc > 0.9
    assert metrics.binary.auc_pr > 0.9
    assert 0 <= metrics.binary.precision <= 1.0
    assert 0 <= metrics.binary.recall <= 1.0
    assert 0 <= metrics.binary.f1 <= 1.0
    assert metrics.binary.n_positive == 50
    assert metrics.binary.n_negative == 50
    assert metrics.calibration.brier_score >= 0.0
    assert metrics.calibration.ece >= 0.0
    assert metrics.n_bootstrap == 20
    assert metrics.bootstrap_auc_ci[0] <= metrics.bootstrap_auc_mean <= metrics.bootstrap_auc_ci[1]


@pytest.mark.scientific
def test_risk_coverage_curve():
    """M88: Risk-coverage curve produces valid selective-prediction analysis."""
    records = _make_scoring_records(30, 30, score_base=5.0)
    scores = [r.score_delta for r in records]
    labels = [1 if r.outcome == "resolved_pathogenic" else 0 for r in records]

    rc = compute_risk_coverage_curve(scores, labels, n_bins=10)
    assert len(rc.points) > 0
    assert rc.auc_rc >= 0.0
    assert rc.optimal_coverage > 0.0
    assert rc.optimal_coverage <= 1.0
    assert 0.0 <= rc.optimal_risk <= 1.0


@pytest.mark.scientific
def test_abstention_analysis():
    """M88: Abstention analysis at various coverage levels."""
    records = _make_scoring_records(40, 40, score_base=8.0)
    scores = [r.score_delta for r in records]
    labels = [1 if r.outcome == "resolved_pathogenic" else 0 for r in records]

    result = compute_abstention_analysis(scores, labels)
    assert len(result.results) > 0
    assert result.abstention_auc >= 0.0
    for r in result.results:
        assert 0.0 <= r.coverage <= 1.0
        assert r.abstained_count >= 0
        assert 0.0 <= r.accuracy_at_coverage <= 1.0


@pytest.mark.scientific
def test_structured_error_analysis():
    """M89: Structured error analysis with gene stratification."""
    records = _make_scoring_records(25, 25, score_base=4.0)
    analysis = compute_error_analysis(records, score_threshold=0.0)

    assert analysis.n_total == 50
    assert analysis.n_errors >= 0
    assert 0 <= analysis.false_positive_rate <= 1.0
    assert 0 <= analysis.false_negative_rate <= 1.0
    assert len(analysis.segments) > 0


@pytest.mark.scientific
def test_bias_audit():
    """M90: Bias, validity, and limitation audit."""
    records = _make_scoring_records(40, 60)
    audit = perform_bias_audit(records)

    assert audit.n_total == 100
    assert audit.n_positive == 40
    assert audit.n_negative == 60
    assert isinstance(audit.issues, list)
    assert isinstance(audit.ancestry_breakdown, dict)
    assert isinstance(audit.gene_coverage, dict)


@pytest.mark.scientific
def test_auroc_separation_quality():
    """Scientific check: well-separated scores yield high AUROC."""
    records = []
    for i in range(30):
        records.append(ScoringRecord(
            chrom="chr1", start=i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=15.0 + i * 0.1,
            gene_symbol="TEST",
            outcome="resolved_pathogenic",
        ))
    for i in range(30):
        records.append(ScoringRecord(
            chrom="chr2", start=i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=-15.0 - i * 0.1,
            gene_symbol="TEST",
            outcome="resolved_benign",
        ))

    metrics = compute_full_metrics(records, n_bootstrap=10)
    assert metrics.binary.auc_roc > 0.98


@pytest.mark.scientific
def test_gene_clustered_metrics():
    """M79: Gene-clustered metrics are computed per gene."""
    records = []
    for i in range(20):
        records.append(ScoringRecord(
            chrom="chr1", start=i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=5.0 + i,
            gene_symbol="BRCA1",
            outcome="resolved_pathogenic",
        ))
    for i in range(20):
        records.append(ScoringRecord(
            chrom="chr1", start=100 + i, ref="A", alt="T",
            scorer_name="fake", scorer_version="0.1.0",
            score_delta=-5.0 - i,
            gene_symbol="BRCA1",
            outcome="resolved_benign",
        ))

    metrics = compute_full_metrics(records, n_bootstrap=10)
    assert len(metrics.gene_clusters) == 1
    cluster = metrics.gene_clusters[0]
    assert cluster.gene == "BRCA1"
    assert cluster.n_variants == 40
    assert cluster.n_pathogenic == 20
    assert cluster.n_benign == 20

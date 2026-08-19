"""Tests for metrics.py — Milestone 79."""

from __future__ import annotations

import pytest

from evovariant_tr.metrics import (
    GeneClusteredMetrics,
    bootstrap_auc_ci,
    compute_auc_pr,
    compute_auc_roc,
    compute_brier_score,
    compute_ece,
    compute_full_metrics,
    compute_precision_recall,
)
from evovariant_tr.scoring_record import ScoreStatus, ScoringRecord


def _make_record(score: float, label: str, gene: str = "BRCA1") -> ScoringRecord:
    outcome = "resolved_pathogenic" if label == "positive" else "resolved_benign"
    return ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="test", scorer_version="1.0",
        score_delta=score, gene_symbol=gene, outcome=outcome,
    )


def test_compute_auc_roc_perfect():
    scores = [0.0, 0.0, 1.0, 1.0]
    labels = [0, 0, 1, 1]
    auc = compute_auc_roc(scores, labels)
    assert auc == pytest.approx(1.0)


def test_compute_auc_roc_no_signal():
    scores = [0.5, 0.5, 0.5, 0.5]
    labels = [0, 0, 1, 1]
    auc = compute_auc_roc(scores, labels)
    assert auc == pytest.approx(0.5, abs=0.01)


def test_compute_auc_roc_inverted():
    scores = [1.0, 1.0, 0.0, 0.0]
    labels = [0, 0, 1, 1]
    auc = compute_auc_roc(scores, labels)
    assert auc == pytest.approx(0.0)


def test_compute_auc_roc_single_class():
    scores = [0.1, 0.2, 0.3]
    labels = [1, 1, 1]
    auc = compute_auc_roc(scores, labels)
    assert auc == 0.5


def test_compute_auc_pr_perfect():
    scores = [0.0, 0.0, 1.0, 1.0]
    labels = [0, 0, 1, 1]
    auc = compute_auc_pr(scores, labels)
    assert auc == pytest.approx(1.0)


def test_compute_precision_recall():
    scores = [0.9, 0.8, 0.3, 0.2]
    labels = [1, 1, 0, 0]
    precision, recall, f1 = compute_precision_recall(scores, labels, threshold=0.5)
    assert precision == 1.0
    assert recall == 1.0
    assert f1 == 1.0


def test_compute_precision_recall_at_threshold():
    scores = [0.9, 0.6, 0.4, 0.1]
    labels = [1, 0, 1, 0]
    precision, recall, f1 = compute_precision_recall(scores, labels, threshold=0.5)
    assert precision == pytest.approx(0.5)
    assert recall == pytest.approx(0.5)


def test_compute_brier_score():
    scores = [0.9, 0.1, 0.8, 0.2]
    labels = [1, 0, 1, 0]
    brier = compute_brier_score(scores, labels)
    assert brier >= 0.0


def test_compute_brier_score_perfect():
    scores = [1.0, 0.0, 1.0, 0.0]
    labels = [1, 0, 1, 0]
    brier = compute_brier_score(scores, labels)
    assert brier == pytest.approx(0.0)


def test_compute_ece():
    scores = [0.9, 0.1, 0.8, 0.2]
    labels = [1, 0, 1, 0]
    ece, max_gap = compute_ece(scores, labels, n_bins=5)
    assert ece >= 0.0
    assert max_gap >= 0.0


def test_bootstrap_auc_ci():
    scores = [float(i % 2) for i in range(100)]
    labels = [i % 2 for i in range(100)]
    mean_auc, std_auc, (ci_low, ci_high) = bootstrap_auc_ci(
        scores, labels, n_bootstrap=100,
    )
    assert 0.0 <= mean_auc <= 1.0
    assert std_auc >= 0.0
    assert ci_low <= mean_auc <= ci_high


def test_bootstrap_auc_ci_single_class():
    scores = [1.0, 2.0, 3.0]
    labels = [1, 1, 1]
    mean_auc, std_auc, (ci_low, ci_high) = bootstrap_auc_ci(
        scores, labels, n_bootstrap=10,
    )
    assert mean_auc == 0.5


def test_compute_full_metrics_basic():
    records = [
        _make_record(10.0, "positive", "BRCA1"),
        _make_record(8.0, "positive", "BRCA1"),
        _make_record(-5.0, "negative", "BRCA1"),
        _make_record(-3.0, "negative", "BRCA1"),
        _make_record(12.0, "positive", "TP53"),
        _make_record(-8.0, "negative", "TP53"),
    ]
    metrics = compute_full_metrics(records, n_bootstrap=10)

    assert metrics.binary.n_positive == 3
    assert metrics.binary.n_negative == 3
    assert metrics.binary.auc_roc >= 0.0
    assert metrics.binary.auc_pr >= 0.0
    assert 0.0 <= metrics.binary.precision <= 1.0
    assert 0.0 <= metrics.binary.recall <= 1.0
    assert len(metrics.gene_clusters) == 2


def test_compute_full_metrics_failed_records_excluded():
    records = [
        _make_record(10.0, "positive"),
        ScoringRecord(
            chrom="chr1", start=100, ref="A", alt="T",
            scorer_name="test", scorer_version="1.0",
            score_delta=5.0, outcome="resolved_pathogenic",
            status=ScoreStatus.FAILED, error="OOM",
        ),
    ]
    metrics = compute_full_metrics(records, n_bootstrap=10)
    assert metrics.binary.n_positive == 1
    assert metrics.binary.n_negative == 0


def test_compute_full_metrics_empty():
    with pytest.raises(ValueError, match="No valid scoring records"):
        compute_full_metrics([], n_bootstrap=10)


def test_metrics_to_dict():
    records = [
        _make_record(10.0, "positive", "BRCA1"),
        _make_record(-5.0, "negative", "BRCA1"),
    ]
    metrics = compute_full_metrics(records, n_bootstrap=10)
    d = metrics.to_dict()

    assert "binary" in d
    assert "calibration" in d
    assert "gene_clusters" in d
    assert "bootstrap_auc_mean" in d
    assert "bootstrap_auc_ci" in d
    assert isinstance(d["bootstrap_auc_ci"], list)
    assert len(d["bootstrap_auc_ci"]) == 2

    assert "auc_roc" in d["binary"]
    assert "ece" in d["calibration"]


def test_gene_clustered_metrics_to_dict():
    gc = GeneClusteredMetrics(
        gene="BRCA1", n_variants=100, n_pathogenic=50, n_benign=50,
        auc_roc=0.85, ece=0.1, score_mean=2.5, score_std=1.2,
        ci_lower=0.8, ci_upper=0.9,
    )
    d = gc.to_dict()
    assert d["gene"] == "BRCA1"
    assert d["auc_roc"] == 0.85
    assert d["ci_lower"] == 0.8
    assert d["ci_upper"] == 0.9


def test_compute_full_metrics_with_gene_groups():
    """Test that genes are properly grouped."""
    records = []
    for i in range(50):
        score = float(i - 25)
        label = "positive" if i > 25 else "negative"
        gene = "BRCA1" if i % 2 == 0 else "TP53"
        records.append(_make_record(score, label, gene))

    metrics = compute_full_metrics(records, n_bootstrap=10)
    gene_names = [g.gene for g in metrics.gene_clusters]
    assert "BRCA1" in gene_names
    assert "TP53" in gene_names

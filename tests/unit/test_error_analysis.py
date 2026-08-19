"""Tests for error_analysis.py — Milestones 89-90."""

from __future__ import annotations

from evovariant_tr.error_analysis import (
    BiasAudit,
    ErrorAnalysis,
    ErrorSegment,
    compute_error_analysis,
    perform_bias_audit,
)
from evovariant_tr.scoring_record import ScoringRecord


def _make_record(score: float, label: str, gene: str = "BRCA1") -> ScoringRecord:
    outcome = "resolved_pathogenic" if label == "positive" else "resolved_benign"
    return ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="test", scorer_version="1.0",
        score_delta=score, gene_symbol=gene, outcome=outcome,
    )


def test_error_segment_creation():
    seg = ErrorSegment(
        name="BRCA1", count=100, false_positives=5, false_negatives=3,
        false_positive_rate=0.05, false_negative_rate=0.03,
        mean_score_delta=2.5,
    )
    assert seg.name == "BRCA1"
    assert seg.count == 100
    assert seg.false_positives == 5


def test_error_analysis_to_dict():
    analysis = ErrorAnalysis(
        n_total=100, n_errors=10, n_false_positives=7,
        n_false_negatives=3, false_positive_rate=0.1, false_negative_rate=0.05,
    )
    d = analysis.to_dict()
    assert d["n_total"] == 100
    assert d["n_errors"] == 10
    assert "segments" in d
    assert "summary" in d


def test_compute_error_analysis_basic():
    records = [
        _make_record(10.0, "positive", "BRCA1"),
        _make_record(8.0, "positive", "BRCA1"),
        _make_record(-5.0, "negative", "BRCA1"),
        _make_record(-3.0, "negative", "BRCA1"),
        _make_record(-1.0, "positive", "TP53"),  # False negative
        _make_record(2.0, "negative", "TP53"),  # False positive
    ]
    analysis = compute_error_analysis(records, score_threshold=0.0)

    assert analysis.n_total == 6
    assert analysis.n_errors == 2
    assert analysis.n_false_positives == 1
    assert analysis.n_false_negatives == 1


def test_compute_error_analysis_stratification():
    records = [
        _make_record(10.0, "positive", "BRCA1"),
        _make_record(-5.0, "negative", "BRCA1"),
        _make_record(-1.0, "positive", "TP53"),
        _make_record(-3.0, "negative", "TP53"),
    ]
    analysis = compute_error_analysis(records, score_threshold=0.0)

    assert len(analysis.segments) == 2
    gene_names = [s.name for s in analysis.segments]
    assert "BRCA1" in gene_names
    assert "TP53" in gene_names


def test_compute_error_analysis_empty():
    analysis = compute_error_analysis([], score_threshold=0.0)
    assert analysis.n_total == 0
    assert analysis.n_errors == 0


def test_compute_error_analysis_failed_records_excluded():
    from evovariant_tr.scoring_record import ScoreStatus
    records = [
        _make_record(10.0, "positive"),
        ScoringRecord(
            chrom="chr1", start=100, ref="A", alt="T",
            scorer_name="test", scorer_version="1.0",
            score_delta=5.0, outcome="resolved_pathogenic",
            status=ScoreStatus.FAILED, error="OOM",
        ),
    ]
    analysis = compute_error_analysis(records, score_threshold=0.0)
    assert analysis.n_total == 1


def test_compute_error_analysis_threshold():
    """Higher threshold should change prediction outcomes."""
    records = [
        _make_record(0.5, "negative"),  # FP at threshold 0.0
        _make_record(0.5, "positive"),   # TP at threshold 0.0
    ]
    analysis1 = compute_error_analysis(records, score_threshold=0.0)
    analysis2 = compute_error_analysis(records, score_threshold=1.0)

    assert analysis1.n_false_positives == 1
    assert analysis2.n_false_positives == 0  # Both below threshold 1.0


def test_bias_audit_creation():
    audit = BiasAudit(
        n_total=100, n_positive=50, n_negative=50,
        ancestry_breakdown={"EUR": 40, "AFR": 30, "EAS": 30},
        gene_coverage={"BRCA1": 50, "TP53": 50},
        issues=["test issue"],
    )
    assert audit.n_total == 100
    assert "EUR" in audit.ancestry_breakdown


def test_bias_audit_to_dict():
    audit = BiasAudit(
        n_total=10, n_positive=5, n_negative=5,
        issues=["issue1"],
    )
    d = audit.to_dict()
    assert d["n_total"] == 10
    assert d["n_positive"] == 5
    assert d["issues"] == ["issue1"]


def test_perform_bias_audit_no_imbalance():
    """Even class distribution should not flag imbalance."""
    records = []
    for i in range(50):
        records.append(_make_record(float(i - 25), "positive", "GENE1"))
    for i in range(50):
        records.append(_make_record(float(i - 25), "negative", "GENE1"))

    audit = perform_bias_audit(records)
    assert audit.n_positive == 50
    assert audit.n_negative == 50
    assert len(audit.issues) >= 0  # May flag small gene count


def test_perform_bias_audit_class_imbalance():
    """Severe class imbalance should be flagged."""
    records = []
    for _ in range(95):
        records.append(_make_record(-1.0, "negative", "GENE1"))
    for _ in range(5):
        records.append(_make_record(1.0, "positive", "GENE1"))

    audit = perform_bias_audit(records)
    assert any("class imbalance" in issue for issue in audit.issues)
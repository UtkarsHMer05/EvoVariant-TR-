"""Tests for abstention.py — Milestone 88."""

from __future__ import annotations

from evovariant_tr.abstention import (
    AbstentionAnalysis,
    AbstentionResult,
    CoveragePoint,
    RiskCoverageCurve,
    compute_abstention_analysis,
    compute_risk_coverage_curve,
)


def test_coverage_point_defaults():
    p = CoveragePoint(
        coverage=1.0, risk=0.5, n_examples=100,
        mean_score=0.0, score_std=0.0, threshold=float("inf"),
    )
    assert p.coverage == 1.0
    assert p.n_examples == 100


def test_abstention_result_defaults():
    r = AbstentionResult(
        coverage=0.8, abstained_count=20,
        accuracy_at_coverage=0.9,
        expected_calibration_error=0.05,
        mean_confidence=0.85,
    )
    assert r.coverage == 0.8
    assert r.abstained_count == 20


def test_risk_coverage_curve_to_dict():
    curve = RiskCoverageCurve(
        points=[
            CoveragePoint(1.0, 0.1, 100, 0.5, 0.2, float("inf")),
            CoveragePoint(0.5, 0.05, 50, 0.5, 0.2, 0.8),
        ],
        auc_rc=0.15,
        optimal_coverage=0.5,
        optimal_risk=0.05,
    )
    d = curve.to_dict()
    assert d["auc_rc"] == 0.15
    assert len(d["points"]) == 2
    assert d["points"][0]["coverage"] == 1.0


def test_abstention_analysis_to_dict():
    analysis = AbstentionAnalysis(
        results=[
            AbstentionResult(0.8, 20, 0.9, 0.05, 0.85),
        ],
        coverage_threshold=0.8,
        abstention_auc=0.72,
    )
    d = analysis.to_dict()
    assert d["coverage_threshold"] == 0.8
    assert d["abstention_auc"] == 0.72
    assert len(d["results"]) == 1


def test_compute_risk_coverage_curve_perfect():
    # Perfect scores: all positives have high scores, all negatives low
    scores = [10.0, 8.0, -5.0, -3.0]
    labels = [1, 1, 0, 0]
    curve = compute_risk_coverage_curve(scores, labels)

    assert len(curve.points) > 0
    assert curve.optimal_risk <= 0.5  # At least at some coverage, should be good
    assert isinstance(curve.auc_rc, float)


def test_compute_risk_coverage_curve_all_wrong():
    scores = [10.0, 10.0, 10.0, 10.0]
    labels = [0, 0, 0, 0]
    curve = compute_risk_coverage_curve(scores, labels)
    # All wrong → risk is always 1.0, AUC can be any value
    assert curve.optimal_risk == 1.0


def test_compute_abstention_analysis_default_levels():
    scores = [5.0, 3.0, -1.0, -3.0, 2.0, -5.0]
    labels = [1, 1, 0, 0, 1, 0]
    analysis = compute_abstention_analysis(scores, labels)

    assert len(analysis.results) == 6  # Default 6 coverage levels
    assert all(r.coverage > 0 for r in analysis.results)
    assert analysis.results[0].coverage == 0.5  # First = 50%
    assert analysis.results[-1].coverage == 1.0  # Last = 100%


def test_compute_abstention_analysis_custom_levels():
    scores = [1.0, -1.0, 2.0, -2.0]
    labels = [1, 0, 1, 0]
    analysis = compute_abstention_analysis(
        scores, labels, coverage_levels=[0.5, 1.0],
    )
    assert len(analysis.results) == 2
    assert analysis.results[0].coverage == 0.5
    assert analysis.results[1].coverage == 1.0


def test_compute_abstention_analysis_abstained_count():
    scores = [10.0, 8.0, -5.0, -3.0, 10.0, 8.0, -5.0, -3.0]
    labels = [1, 1, 0, 0, 1, 1, 0, 0]
    analysis = compute_abstention_analysis(
        scores, labels, coverage_levels=[0.5, 1.0],
    )
    # At 50% coverage with 8 examples, abstain on 4
    result_50 = next(r for r in analysis.results if r.coverage == 0.5)
    assert result_50.abstained_count == 4
    result_100 = next(r for r in analysis.results if r.coverage == 1.0)
    assert result_100.abstained_count == 0


def test_abstention_analysis_perfection():
    scores = [10.0, 10.0, 10.0, 10.0]
    labels = [1, 1, 1, 1]
    analysis = compute_abstention_analysis(
        scores, labels, coverage_levels=[1.0],
    )
    result = analysis.results[0]
    assert result.accuracy_at_coverage == 1.0
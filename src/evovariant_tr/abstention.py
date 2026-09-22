"""Risk-coverage and abstention analysis for EvoVariant-TR (Milestone 88).

This module provides:
- Risk-coverage curves (selective prediction analysis)
- Abstention analysis (at what coverage level the model should abstain)
- Expected calibration under abstention
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CoveragePoint:
    """A single point on a risk-coverage curve."""

    coverage: float
    risk: float
    n_examples: int
    mean_score: float
    score_std: float
    threshold: float


@dataclass
class AbstentionResult:
    """Results from abstention analysis."""

    coverage: float
    abstained_count: int
    accuracy_at_coverage: float | None
    expected_calibration_error: float | None
    mean_confidence: float


@dataclass
class RiskCoverageCurve:
    """Full risk-coverage curve."""

    points: list[CoveragePoint]
    auc_rc: float  # Area under the risk-coverage curve
    optimal_coverage: float
    optimal_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "auc_rc": self.auc_rc,
            "optimal_coverage": self.optimal_coverage,
            "optimal_risk": self.optimal_risk,
            "points": [
                {
                    "coverage": p.coverage,
                    "risk": p.risk,
                    "n_examples": p.n_examples,
                    "mean_score": p.mean_score,
                    "score_std": p.score_std,
                    "threshold": p.threshold,
                }
                for p in self.points
            ],
        }


@dataclass
class AbstentionAnalysis:
    """Full abstention analysis results."""

    results: list[AbstentionResult]
    coverage_threshold: float
    abstention_auc: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage_threshold": self.coverage_threshold,
            "abstention_auc": self.abstention_auc,
            "results": [
                {
                    "coverage": r.coverage,
                    "abstained_count": r.abstained_count,
                    "accuracy_at_coverage": r.accuracy_at_coverage,
                    "expected_calibration_error": r.expected_calibration_error,
                    "mean_confidence": r.mean_confidence,
                }
                for r in self.results
            ],
        }


def _count_errors(scores: list[float], labels: list[int]) -> int:
    """Count prediction errors (threshold at 0)."""
    return sum(
        1 for s, lab in zip(scores, labels, strict=True)
        if (1 if s > 0 else 0) != lab
    )


def _confidences_from_scores(scores: list[float]) -> list[float]:
    """Convert scores to confidence values in [0, 1].

    Assumes scores are log-likelihood ratios. Higher absolute value
    indicates higher confidence in the prediction.
    """
    # Signed log-likelihood scores map to probability-like confidence through
    # tanh; absolute value is required because a very negative score is also
    # highly confident, just in the negative class.
    import math
    return [0.5 + 0.5 * abs(math.tanh(s / 10.0)) for s in scores]


def compute_risk_coverage_curve(
    scores: list[float],
    labels: list[int],
    n_bins: int = 20,
) -> RiskCoverageCurve:
    """Compute the risk-coverage curve.

    The risk-coverage curve shows the error rate (risk) as a function
    of coverage (fraction of examples where the model makes a prediction).

    A selective prediction strategy abstains on the lowest-confidence
    predictions and only predicts on the highest-confidence ones.

    Args:
        scores: Model scores (higher = more confident in positive class).
        labels: Ground truth labels (0 or 1).
        n_bins: Number of coverage levels to evaluate.

    Returns:
        A RiskCoverageCurve with coverage and risk at each level.
    """
    confidences = _confidences_from_scores(scores)
    n = len(scores)

    # Sort by confidence (descending = highest confidence first)
    indexed = sorted(range(n), key=lambda i: -confidences[i])
    sorted_labels = [labels[i] for i in indexed]
    sorted_conf = [confidences[i] for i in indexed]
    sorted_scores = [scores[i] for i in indexed]

    points = []

    # Full coverage (no abstention)
    full_errors = _count_errors(sorted_scores, sorted_labels)
    points.append(CoveragePoint(
        coverage=1.0,
        risk=full_errors / n,
        n_examples=n,
        mean_score=sum(scores) / n,
        score_std=0.0,
        threshold=float("inf"),
    ))

    # Evaluate at decreasing coverage levels
    for frac in range(n_bins - 1, 0, -1):
        n_keep = max(1, int(n * frac / n_bins))
        kept_scores = sorted_scores[:n_keep]
        kept_labels = sorted_labels[:n_keep]
        errors = _count_errors(kept_scores, kept_labels)

        points.append(CoveragePoint(
            coverage=n_keep / n,
            risk=errors / n_keep if n_keep > 0 else 0.0,
            n_examples=n_keep,
            mean_score=sum(kept_scores) / n_keep,
            score_std=0.0,
            threshold=sorted_conf[n_keep - 1] if n_keep > 0 else float("inf"),
        ))

    # The points are generated from full to low coverage.  Integrate after
    # sorting by ascending coverage so the area is non-negative.
    points_for_auc = sorted(points, key=lambda point: point.coverage)
    auc_rc = 0.0
    for i in range(1, len(points_for_auc)):
        auc_rc += (points_for_auc[i].coverage - points_for_auc[i - 1].coverage) * (
            points_for_auc[i].risk + points_for_auc[i - 1].risk
        ) / 2

    # Find optimal (lowest risk) point
    best = min(points, key=lambda p: p.risk)

    return RiskCoverageCurve(
        points=points,
        auc_rc=auc_rc,
        optimal_coverage=best.coverage,
        optimal_risk=best.risk,
    )


def compute_abstention_analysis(
    scores: list[float],
    labels: list[int],
    coverage_levels: list[float] | None = None,
) -> AbstentionAnalysis:
    """Analyze abstention behavior at different coverage levels.

    Args:
        scores: Model scores.
        labels: Ground truth labels.
        coverage_levels: List of coverage fractions to evaluate.
            Defaults to [0.5, 0.6, 0.7, 0.8, 0.9, 1.0].

    Returns:
        An AbstentionAnalysis with results at each coverage level.
    """
    if coverage_levels is None:
        coverage_levels = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    confidences = _confidences_from_scores(scores)
    n = len(scores)

    indexed = sorted(range(n), key=lambda i: -confidences[i])
    sorted_labels = [labels[i] for i in indexed]
    sorted_scores = [scores[i] for i in indexed]
    sorted_conf = [confidences[i] for i in indexed]

    results = []
    for cov in coverage_levels:
        n_keep = max(1, int(n * cov))
        kept_scores = sorted_scores[:n_keep]
        kept_labels = sorted_labels[:n_keep]
        kept_conf = sorted_conf[:n_keep]

        # Accuracy
        errors = _count_errors(kept_scores, kept_labels)
        accuracy = 1.0 - (errors / n_keep if n_keep > 0 else 0.0)

        # Calibration error
        norm_scores = []
        s_min, s_max = min(kept_scores), max(kept_scores)
        if s_max > s_min:
            norm_scores = [(s - s_min) / (s_max - s_min) for s in kept_scores]
        else:
            norm_scores = [0.5] * len(kept_scores)

        from evovariant_tr.metrics import compute_ece
        ece, _ = compute_ece(norm_scores, kept_labels, n_bins=10)

        results.append(AbstentionResult(
            coverage=cov,
            abstained_count=n - n_keep,
            accuracy_at_coverage=accuracy,
            expected_calibration_error=ece,
            mean_confidence=sum(kept_conf) / n_keep if n_keep > 0 else 0.0,
        ))

    # AUC under abstention curve (higher = better)
    auc = 0.0
    for i in range(1, len(results)):
        acc_i = results[i].accuracy_at_coverage or 0.0
        acc_prev = results[i - 1].accuracy_at_coverage or 0.0
        auc += (results[i].coverage - results[i - 1].coverage) * (
            acc_i + acc_prev
        ) / 2

    return AbstentionAnalysis(
        results=results,
        coverage_threshold=results[0].coverage if results else 0.5,
        abstention_auc=auc,
    )

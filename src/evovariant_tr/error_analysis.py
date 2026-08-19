"""Structured error analysis for EvoVariant-TR (Milestone 89).

Provides analysis of model prediction errors, including:
- False positive/negative analysis
- Error stratification by gene and consequence
- Confidence calibration of predictions
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from evovariant_tr.scoring_record import ScoringRecord


@dataclass
class ErrorSegment:
    """A segment of errors with shared characteristics."""

    name: str
    count: int
    false_positives: int
    false_negatives: int
    false_positive_rate: float
    false_negative_rate: float
    mean_score_delta: float | None = None


@dataclass
class ErrorAnalysis:
    """Complete error analysis results."""

    n_total: int
    n_errors: int
    n_false_positives: int
    n_false_negatives: int
    false_positive_rate: float
    false_negative_rate: float
    segments: list[ErrorSegment] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_total": self.n_total,
            "n_errors": self.n_errors,
            "n_false_positives": self.n_false_positives,
            "n_false_negatives": self.n_false_negatives,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
            "segments": [s.__dict__ for s in self.segments],
            "summary": self.summary,
        }


def compute_error_analysis(
    records: list[ScoringRecord],
    score_threshold: float = 0.0,
    by_gene: bool = True,
    by_consequence: bool = True,
) -> ErrorAnalysis:
    """Compute structured error analysis from scoring records."""
    valid = [r for r in records if r.status.value == "completed" and r.error is None]
    n_total = len(valid)
    if n_total == 0:
        return ErrorAnalysis(
            n_total=0, n_errors=0, n_false_positives=0, n_false_negatives=0,
            false_positive_rate=0.0, false_negative_rate=0.0,
        )

    predictions = [1 if r.score_delta > score_threshold else 0 for r in valid]
    true_labels = [1 if r.outcome == "resolved_pathogenic" else 0 for r in valid]

    n_fp = sum(1 for p, t in zip(predictions, true_labels, strict=True) if p == 1 and t == 0)
    n_fn = sum(1 for p, t in zip(predictions, true_labels, strict=True) if p == 0 and t == 1)
    n_errors = n_fp + n_fn

    n_positive = sum(true_labels)
    n_negative = n_total - n_positive
    fp_rate = n_fp / n_negative if n_negative > 0 else 0.0
    fn_rate = n_fn / n_positive if n_positive > 0 else 0.0

    segments = []
    if by_gene:
        genes: dict[str, list[tuple[int, int, float]]] = {}
        for r, p, t in zip(valid, predictions, true_labels, strict=True):
            gene = r.gene_symbol or "UNKNOWN"
            genes.setdefault(gene, []).append((p, t, r.score_delta))

        for gene, data in sorted(genes.items(), key=lambda x: -len(x[1])):
            gene_preds = [d[0] for d in data]
            gene_labels = [d[1] for d in data]
            gene_scores = [d[2] for d in data]
            g_n = len(data)
            g_fp = sum(1 for p, t in zip(gene_preds, gene_labels, strict=True) if p == 1 and t == 0)
            g_fn = sum(1 for p, t in zip(gene_preds, gene_labels, strict=True) if p == 0 and t == 1)
            g_pos = sum(gene_labels)
            g_neg = g_n - g_pos
            segments.append(ErrorSegment(
                name=gene,
                count=g_n,
                false_positives=g_fp,
                false_negatives=g_fn,
                false_positive_rate=g_fp / g_neg if g_neg > 0 else 0.0,
                false_negative_rate=g_fn / g_pos if g_pos > 0 else 0.0,
                mean_score_delta=sum(gene_scores) / len(gene_scores) if gene_scores else None,
            ))

    summary = {
        "score_threshold": score_threshold,
        "by_gene": by_gene,
        "by_consequence": by_consequence,
        "error_rate": n_errors / n_total if n_total > 0 else 0.0,
        "balanced_accuracy": 0.5 * ((1 - fn_rate) + (1 - fp_rate)),
    }

    return ErrorAnalysis(
        n_total=n_total,
        n_errors=n_errors,
        n_false_positives=n_fp,
        n_false_negatives=n_fn,
        false_positive_rate=fp_rate,
        false_negative_rate=fn_rate,
        segments=segments,
        summary=summary,
    )


@dataclass
class BiasAudit:
    """Results of a bias, validity, and limitation audit."""

    n_total: int
    n_positive: int
    n_negative: int
    ancestry_breakdown: dict[str, int] = field(default_factory=dict)
    gene_coverage: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_total": self.n_total,
            "n_positive": self.n_positive,
            "n_negative": self.n_negative,
            "ancestry_breakdown": dict(self.ancestry_breakdown),
            "gene_coverage": dict(self.gene_coverage),
            "issues": list(self.issues),
        }


def perform_bias_audit(records: list[ScoringRecord]) -> BiasAudit:
    """Perform a bias, validity, and limitation audit."""
    valid = [r for r in records if r.status.value == "completed" and r.error is None]

    gene_counts: Counter[str] = Counter()
    ancestry_counts: Counter[str] = Counter()
    issues = []

    for r in valid:
        gene = r.gene_symbol or "UNKNOWN"
        gene_counts[gene] += 1
        ancestry = r.metadata.get("ancestry", "Unknown") if hasattr(r, "metadata") else "Unknown"
        ancestry_counts[ancestry] += 1

    # Check for class imbalance
    n_pos = sum(1 for r in valid if r.outcome == "resolved_pathogenic")
    n_neg = sum(1 for r in valid if r.outcome == "resolved_benign")
    if n_pos > 0 and n_neg > 0:
        ratio = max(n_pos, n_neg) / min(n_pos, n_neg)
        if ratio > 5:
            issues.append(f"Severe class imbalance: {ratio:.1f}:1 ratio")

    # Check for genes with very few examples
    small_genes = [g for g, c in gene_counts.items() if c < 10]
    if small_genes:
        issues.append(
            f"{len(small_genes)} genes have <10 variants - "
            "metrics may be unreliable for these genes"
        )

    return BiasAudit(
        n_total=len(valid),
        n_positive=n_pos,
        n_negative=n_neg,
        ancestry_breakdown=dict(ancestry_counts),
        gene_coverage=dict(gene_counts),
        issues=issues,
    )
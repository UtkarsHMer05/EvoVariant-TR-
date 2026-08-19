"""Full metrics and gene-clustered uncertainty engine for EvoVariant-TR (M79).

Provides binary classification metrics, calibration metrics,
uncertainty quantification via bootstrap, and gene-clustered analysis.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Any

from evovariant_tr.scoring_record import ScoringRecord

SQRT_2PI = 2.5066282746310002


@dataclass
class BinaryMetrics:
    """Binary classification metrics."""

    auc_roc: float
    auc_pr: float
    precision: float
    recall: float
    f1: float
    n_positive: int
    n_negative: int
    threshold: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "auc_roc": self.auc_roc,
            "auc_pr": self.auc_pr,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "n_positive": self.n_positive,
            "n_negative": self.n_negative,
            "threshold": self.threshold,
        }


@dataclass
class CalibrationMetrics:
    """Calibration metrics."""

    ece: float
    brier_score: float
    max_calibration_gap: float
    n_bins: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ece": self.ece,
            "brier_score": self.brier_score,
            "max_calibration_gap": self.max_calibration_gap,
            "n_bins": self.n_bins,
        }


@dataclass
class GeneClusteredMetrics:
    """Metrics for a single gene cluster."""

    gene: str
    n_variants: int
    n_pathogenic: int
    n_benign: int
    auc_roc: float | None
    ece: float | None
    score_mean: float
    score_std: float
    ci_lower: float | None = None
    ci_upper: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "gene": self.gene,
            "n_variants": self.n_variants,
            "n_pathogenic": self.n_pathogenic,
            "n_benign": self.n_benign,
            "auc_roc": self.auc_roc,
            "ece": self.ece,
            "score_mean": self.score_mean,
            "score_std": self.score_std,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
        }


@dataclass
class FullMetrics:
    """Complete metrics with uncertainty."""

    binary: BinaryMetrics
    calibration: CalibrationMetrics
    gene_clusters: list[GeneClusteredMetrics]
    bootstrap_auc_mean: float
    bootstrap_auc_std: float
    bootstrap_auc_ci: tuple[float, float]
    n_bootstrap: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "binary": self.binary.to_dict(),
            "calibration": self.calibration.to_dict(),
            "gene_clusters": [g.to_dict() for g in self.gene_clusters],
            "bootstrap_auc_mean": self.bootstrap_auc_mean,
            "bootstrap_auc_std": self.bootstrap_auc_std,
            "bootstrap_auc_ci": list(self.bootstrap_auc_ci),
            "n_bootstrap": self.n_bootstrap,
        }


def compute_auc_roc(
    scores: list[float], labels: list[int]
) -> float:
    """Compute AUC-ROC using the rank-based method (Mann-Whitney U)."""
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Sort by score, assign ranks (handling ties via average rank)
    indexed = sorted(enumerate(scores), key=lambda x: x[1])
    ranks = [0.0] * len(scores)

    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        # Average rank for tied positions (1-indexed)
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j

    sum_ranks_pos = sum(ranks[k] for k in range(len(labels)) if labels[k] == 1)
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(auc)


def compute_auc_pr(
    scores: list[float], labels: list[int]
) -> float:
    """Compute AUC-PR (area under precision-recall curve)."""
    n_pos = sum(labels)
    if n_pos == 0:
        return 0.0

    # Sort by score descending
    indexed = sorted(enumerate(scores), key=lambda x: -x[1])
    sorted_labels = [labels[i] for i, _ in indexed]

    tp = 0
    fp = 0
    precisions = [1.0]
    recalls = [0.0]

    for label in sorted_labels:
        if label == 1:
            tp += 1
        else:
            fp += 1
        if tp + fp > 0:
            precisions.append(tp / (tp + fp))
            recalls.append(tp / n_pos)

    auc = 0.0
    for i in range(1, len(recalls)):
        auc += (recalls[i] - recalls[i - 1]) * precisions[i]
    return float(auc)


def compute_precision_recall(
    scores: list[float],
    labels: list[int],
    threshold: float = 0.5,
) -> tuple[float, float, float]:
    """Compute precision, recall, and F1 at a given threshold."""
    tp = sum(1 for s, lab in zip(scores, labels, strict=True) if s >= threshold and lab == 1)
    fp = sum(1 for s, lab in zip(scores, labels, strict=True) if s >= threshold and lab == 0)
    fn = sum(1 for s, lab in zip(scores, labels, strict=True) if s < threshold and lab == 1)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    denom = precision + recall
    f1 = 2 * precision * recall / denom if denom > 0 else 0.0

    return float(precision), float(recall), float(f1)


def compute_brier_score(
    scores: list[float], labels: list[int]
) -> float:
    """Compute the Brier score (mean squared error of probabilities)."""
    return sum((s - lab) ** 2 for s, lab in zip(scores, labels, strict=True)) / len(scores)


def compute_ece(
    scores: list[float],
    labels: list[int],
    n_bins: int = 10,
) -> tuple[float, float]:
    """Compute Expected Calibration Error.

    Returns (ece, max_calibration_gap).
    """
    n = len(scores)
    ece = 0.0
    max_gap = 0.0

    for bin_idx in range(n_bins):
        lower = bin_idx / n_bins
        upper = (bin_idx + 1) / n_bins

        # For the last bin, include upper boundary
        if bin_idx == n_bins - 1:
            in_bin = [i for i, s in enumerate(scores) if lower <= s <= upper]
        else:
            in_bin = [i for i, s in enumerate(scores) if lower <= s < upper]

        if not in_bin:
            continue

        bin_acc = sum(labels[i] for i in in_bin) / len(in_bin)
        bin_conf = sum(scores[i] for i in in_bin) / len(in_bin)
        gap = abs(bin_acc - bin_conf)
        ece += (len(in_bin) / n) * gap
        max_gap = max(max_gap, gap)

    return float(ece), float(max_gap)


def _percentile(sorted_data: list[float], p: float) -> float:
    """Compute the p-th percentile from a sorted list."""
    if not sorted_data:
        return 0.0
    if len(sorted_data) == 1:
        return sorted_data[0]
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    if f == c:
        return sorted_data[f]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def bootstrap_auc_ci(
    scores: list[float],
    labels: list[int],
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, tuple[float, float]]:
    """Compute bootstrap confidence interval for AUC-ROC."""
    rng = random.Random(seed)
    n = len(scores)
    aucs: list[float] = []

    for _ in range(n_bootstrap):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        boot_scores = [scores[i] for i in indices]
        boot_labels = [labels[i] for i in indices]
        if sum(boot_labels) == 0 or n - sum(boot_labels) == 0:
            continue
        auc = compute_auc_roc(boot_scores, boot_labels)
        aucs.append(auc)

    if not aucs:
        return 0.5, 0.0, (0.0, 1.0)

    mean_auc = mean(aucs)
    std_auc = stdev(aucs) if len(aucs) > 1 else 0.0
    alpha = 1 - ci
    sorted_aucs = sorted(aucs)
    ci_lower = _percentile(sorted_aucs, alpha / 2 * 100)
    ci_upper = _percentile(sorted_aucs, (1 - alpha / 2) * 100)

    return float(mean_auc), float(std_auc), (float(ci_lower), float(ci_upper))


def compute_full_metrics(
    records: list[ScoringRecord],
    n_bootstrap: int = 1000,
    n_bins: int = 10,
    score_key: str = "score_delta",
) -> FullMetrics:
    """Compute full metrics from scoring records."""
    valid_records = [
        r for r in records
        if r.status.value == "completed" and r.error is None
    ]
    if not valid_records:
        raise ValueError("No valid scoring records to compute metrics")

    scores = [getattr(r, score_key) for r in valid_records]
    labels = [
        1 if r.outcome == "resolved_pathogenic" else 0
        for r in valid_records
    ]

    s_min, s_max = min(scores), max(scores)
    if s_max > s_min:
        norm_scores = [(s - s_min) / (s_max - s_min) for s in scores]
    else:
        norm_scores = [0.5] * len(scores)

    auc_roc = compute_auc_roc(scores, labels)
    auc_pr = compute_auc_pr(scores, labels)
    precision, recall, f1 = compute_precision_recall(scores, labels)

    binary = BinaryMetrics(
        auc_roc=auc_roc,
        auc_pr=auc_pr,
        precision=precision,
        recall=recall,
        f1=f1,
        n_positive=sum(labels),
        n_negative=len(labels) - sum(labels),
    )

    ece, max_gap = compute_ece(norm_scores, labels, n_bins)
    brier = compute_brier_score(norm_scores, labels)
    calibration = CalibrationMetrics(
        ece=ece,
        brier_score=brier,
        max_calibration_gap=max_gap,
        n_bins=n_bins,
    )

    boot_mean, boot_std, boot_ci = bootstrap_auc_ci(
        scores, labels, n_bootstrap=n_bootstrap,
    )

    # Gene-clustered metrics
    genes: dict[str, list[tuple[float, int]]] = {}
    for r in valid_records:
        gene = r.gene_symbol or "UNKNOWN"
        score_val = getattr(r, score_key)
        label_val = 1 if r.outcome == "resolved_pathogenic" else 0
        genes.setdefault(gene, []).append((float(score_val), label_val))

    gene_clusters = []
    for gene, gene_data in sorted(genes.items()):
        gene_scores = [d[0] for d in gene_data]
        gene_labels = [d[1] for d in gene_data]
        n_pos = sum(gene_labels)
        n_neg = len(gene_labels) - n_pos

        gene_auc = None
        gene_ece = None
        if n_pos > 0 and n_neg > 0:
            gene_auc = compute_auc_roc(gene_scores, gene_labels)
            gs_min, gs_max = min(gene_scores), max(gene_scores)
            if gs_max > gs_min:
                norm_gs = [(s - gs_min) / (gs_max - gs_min) for s in gene_scores]
            else:
                norm_gs = [0.5] * len(gene_scores)
            gene_ece, _ = compute_ece(norm_gs, gene_labels, n_bins)

        ci_lower = None
        ci_upper = None
        if n_pos > 0 and n_neg > 0 and len(gene_data) >= 10:
            _, _, ci = bootstrap_auc_ci(
                gene_scores, gene_labels,
                n_bootstrap=min(n_bootstrap, 100),
            )
            ci_lower, ci_upper = ci

        score_mean = mean(gene_scores) if gene_scores else 0.0
        score_std = stdev(gene_scores) if len(gene_scores) > 1 else 0.0

        gene_clusters.append(GeneClusteredMetrics(
            gene=gene,
            n_variants=len(gene_data),
            n_pathogenic=n_pos,
            n_benign=n_neg,
            auc_roc=gene_auc,
            ece=gene_ece,
            score_mean=score_mean,
            score_std=score_std,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
        ))

    return FullMetrics(
        binary=binary,
        calibration=calibration,
        gene_clusters=gene_clusters,
        bootstrap_auc_mean=boot_mean,
        bootstrap_auc_std=boot_std,
        bootstrap_auc_ci=boot_ci,
        n_bootstrap=n_bootstrap,
    )
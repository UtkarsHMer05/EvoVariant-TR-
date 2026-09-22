"""Gene-clustered bootstrap and Holm correction for locked reports."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence

from .metrics import _rank_auc, binary_metrics

CORE_METRICS = ("auroc", "auprc", "mcc", "balanced_accuracy", "brier")


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _sample_indices(
    grouped: dict[str, list[int]], names: list[str], rng: random.Random
) -> list[int]:
    return [index for _ in names for index in grouped[names[rng.randrange(len(names))]]]


def gene_bootstrap_auc(
    labels: Sequence[int],
    scores: Sequence[float],
    genes: Sequence[str],
    *,
    replicates: int = 2000,
    seed: int = 2026,
) -> dict[str, float | int]:
    if not (len(labels) == len(scores) == len(genes)):
        raise ValueError("labels, scores, and genes must have equal length")
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, gene in enumerate(genes):
        grouped[str(gene)].append(index)
    names = sorted(grouped)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(replicates):
        sampled = [names[rng.randrange(len(names))] for _ in names]
        indices = [index for name in sampled for index in grouped[name]]
        auc = _rank_auc([labels[index] for index in indices], [scores[index] for index in indices])
        if auc is not None:
            values.append(auc)
    if not values:
        raise ValueError("bootstrap produced no two-class samples")
    values.sort()
    lower = values[int(0.025 * (len(values) - 1))]
    upper = values[int(0.975 * (len(values) - 1))]
    return {
        "replicates": len(values),
        "mean_auc": sum(values) / len(values),
        "ci_lower": lower,
        "ci_upper": upper,
    }


def gene_bootstrap_metrics(
    labels: Sequence[int],
    scores: Sequence[float],
    genes: Sequence[str],
    *,
    replicates: int = 2000,
    seed: int = 2026,
) -> dict[str, dict[str, float | int]]:
    """Gene-cluster bootstrap CIs for the predeclared adaptation metrics."""
    if not replicates or not (len(labels) == len(scores) == len(genes)):
        raise ValueError("inputs must align and replicates must be positive")
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, gene in enumerate(genes):
        grouped[str(gene)].append(index)
    names = sorted(grouped)
    if not names:
        raise ValueError("at least one gene is required")
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {name: [] for name in CORE_METRICS}
    for _ in range(replicates):
        indices = _sample_indices(grouped, names, rng)
        metrics = binary_metrics(
            [labels[index] for index in indices], [scores[index] for index in indices]
        )
        for name in CORE_METRICS:
            value = metrics[name]
            if value is not None:
                samples[name].append(float(value))
    return {
        name: {
            "replicates": len(values),
            "mean": sum(values) / len(values),
            "ci_lower": _percentile(values, 0.025),
            "ci_upper": _percentile(values, 0.975),
        }
        for name, values in samples.items()
        if values
    }


def paired_gene_bootstrap(
    labels: Sequence[int],
    left_scores: Sequence[float],
    right_scores: Sequence[float],
    genes: Sequence[str],
    *,
    replicates: int = 2000,
    seed: int = 2026,
) -> dict[str, dict[str, float | int]]:
    """Paired gene bootstrap for right-minus-left metric differences."""
    if not replicates or not (len(labels) == len(left_scores) == len(right_scores) == len(genes)):
        raise ValueError("paired inputs must align and replicates must be positive")
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, gene in enumerate(genes):
        grouped[str(gene)].append(index)
    names = sorted(grouped)
    if not names:
        raise ValueError("at least one gene is required")
    rng = random.Random(seed)
    differences: dict[str, list[float]] = {name: [] for name in CORE_METRICS}
    for _ in range(replicates):
        sampled_names = [names[rng.randrange(len(names))] for _ in names]
        indices = [index for name in sampled_names for index in grouped[name]]
        sample_labels = [labels[index] for index in indices]
        left = binary_metrics(sample_labels, [left_scores[index] for index in indices])
        right = binary_metrics(sample_labels, [right_scores[index] for index in indices])
        for name in CORE_METRICS:
            if left[name] is not None and right[name] is not None:
                differences[name].append(float(right[name]) - float(left[name]))
    report = {}
    for name, values in differences.items():
        if not values:
            continue
        tail = min(sum(value <= 0 for value in values) + 1, sum(value >= 0 for value in values) + 1)
        report[name] = {
            "replicates": len(values),
            "mean_difference_right_minus_left": sum(values) / len(values),
            "ci_lower": _percentile(values, 0.025),
            "ci_upper": _percentile(values, 0.975),
            "two_sided_p": min(1.0, 2 * tail / (len(values) + 1)),
        }
    return report


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values in original comparison order."""
    if any(not 0 <= p_value <= 1 for p_value in p_values):
        raise ValueError("p-values must be in [0, 1]")
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, (index, p_value) in enumerate(indexed):
        running = max(running, min(1.0, (len(p_values) - rank) * p_value))
        adjusted[index] = running
    return adjusted

"""Gene-clustered bootstrap and Holm correction for locked reports."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Sequence

from .metrics import _rank_auc


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


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values in original comparison order."""
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, (index, p_value) in enumerate(indexed):
        running = max(running, min(1.0, (len(p_values) - rank) * p_value))
        adjusted[index] = running
    return adjusted


# Evidence snapshot from the incomplete adaptation branch.
# Source: research/posthoc-foundation-adaptation
# Snapshot commit: 196393636b069dfeaa8dbd43f41b543d0b20d91a
# Purpose: experimental fine-tuning evidence; not part of frozen baseline inference

"""TRAIN-only gene-grouped cross-validation splits."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def make_grouped_folds(
    rows: Sequence[Any],
    n_splits: int = 3,
    seed: int = 42,
) -> list[tuple[list[int], list[int]]]:
    """Return deterministic StratifiedGroupKFold indices over TRAIN rows only."""
    if n_splits != 3:
        raise ValueError("the frozen protocol requires exactly three folds")
    try:
        from sklearn.model_selection import StratifiedGroupKFold
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for grouped folds") from exc
    labels = [int(row.label) for row in rows]
    groups = [str(row.gene_symbol) for row in rows]
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return [
        (train.tolist(), validation.tolist())
        for train, validation in splitter.split(list(range(len(rows))), labels, groups)
    ]

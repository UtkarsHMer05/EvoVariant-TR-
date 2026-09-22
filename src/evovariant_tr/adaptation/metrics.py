"""Small dependency-light binary and calibration metrics for adaptation."""

from __future__ import annotations

from collections.abc import Sequence
from math import log
from typing import Any


def _rank_auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = sum(int(label) for label in labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(zip(scores, labels, strict=True), key=lambda item: item[0])
    rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2
        rank_sum += average_rank * sum(label for _, label in ordered[index:end])
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def _pr_auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = sum(int(label) for label in labels)
    if not positives or positives == len(labels):
        return None
    pairs = sorted(zip(scores, labels, strict=True), key=lambda item: item[0], reverse=True)
    tp = fp = 0
    previous_recall = 0.0
    area = 0.0
    for _, label in pairs:
        if label:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def _ece(labels: Sequence[int], scores: Sequence[float], bins: int = 10) -> float:
    if not labels:
        return 0.0
    total = len(labels)
    error = 0.0
    for bin_index in range(bins):
        lower = bin_index / bins
        upper = (bin_index + 1) / bins
        members = [
            (label, score)
            for label, score in zip(labels, scores, strict=True)
            if lower <= score < upper or (bin_index == bins - 1 and score == upper)
        ]
        if members:
            confidence = sum(score for _, score in members) / len(members)
            accuracy = sum(label for label, _ in members) / len(members)
            error += len(members) / total * abs(accuracy - confidence)
    return error


def binary_metrics(
    labels: Sequence[int],
    scores: Sequence[float],
    threshold: float = 0.5,
    bins: int = 10,
) -> dict[str, Any]:
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must be non-empty and equal length")
    predicted = [int(score >= threshold) for score in scores]
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predicted, strict=True))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predicted, strict=True))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predicted, strict=True))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels)
    balanced_accuracy = (recall + specificity) / 2
    brier = sum(
        (float(score) - int(label)) ** 2 for label, score in zip(labels, scores, strict=True)
    ) / len(labels)
    clipped = [min(1 - 1e-7, max(1e-7, float(score))) for score in scores]
    logloss = -sum(
        int(label) * log(score) + (1 - int(label)) * log(1 - score)
        for label, score in zip(labels, clipped, strict=True)
    ) / len(labels)
    return {
        "auroc": _rank_auc(labels, scores),
        "auprc": _pr_auc(labels, scores),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "mcc": (
            (tp * tn - fp * fn) / ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
            if (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
            else 0.0
        ),
        "brier": brier,
        "log_loss": logloss,
        "ece": _ece(labels, scores, bins),
        "threshold": threshold,
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "n": len(labels),
        "positives": sum(labels),
        "negatives": len(labels) - sum(labels),
    }

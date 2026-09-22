"""TRAIN-OOF-only calibration and abstention helpers."""

from __future__ import annotations

from math import exp, log
from typing import Sequence


def _nll(labels: Sequence[int], logits: Sequence[float], temperature: float) -> float:
    total = 0.0
    for label, logit in zip(labels, logits):
        scaled = logit / temperature
        probability = 1.0 / (1.0 + exp(-max(-60.0, min(60.0, scaled))))
        probability = min(1 - 1e-7, max(1e-7, probability))
        total -= int(label) * log(probability) + (1 - int(label)) * log(1 - probability)
    return total / len(labels)


def fit_temperature(
    labels: Sequence[int],
    logits: Sequence[float],
    *,
    minimum: float = 0.25,
    maximum: float = 4.0,
    step: float = 0.05,
) -> float:
    """Select temperature by TRAIN OOF NLL only."""
    if len(labels) != len(logits) or not labels:
        raise ValueError("labels and logits must be non-empty and equal length")
    candidates = []
    current = minimum
    while current <= maximum + 1e-9:
        candidates.append(round(current, 6))
        current += step
    return min(candidates, key=lambda value: _nll(labels, logits, value))


def apply_temperature(logits: Sequence[float], temperature: float) -> list[float]:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    return [1.0 / (1.0 + exp(-max(-60.0, min(60.0, logit / temperature)))) for logit in logits]


def _mcc(labels: Sequence[int], predictions: Sequence[int]) -> float:
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions))
    denominator = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
    return (tp * tn - fp * fn) / denominator if denominator else 0.0


def select_abstention_threshold(
    labels: Sequence[int],
    probabilities: Sequence[float],
) -> dict[str, float]:
    """Choose one MCC threshold from TRAIN OOF probabilities."""
    candidates = sorted({0.0, 0.5, 1.0, *map(float, probabilities)})
    best = max(
        candidates,
        key=lambda threshold: _mcc(
            labels, [int(probability >= threshold) for probability in probabilities]
        ),
    )
    return {
        "threshold": best,
        "mcc": _mcc(labels, [int(probability >= best) for probability in probabilities]),
    }


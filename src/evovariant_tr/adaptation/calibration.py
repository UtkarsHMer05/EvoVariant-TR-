"""TRAIN-OOF-only calibration and abstention helpers."""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence
from math import ceil, exp, log


def _nll(labels: Sequence[int], logits: Sequence[float], temperature: float) -> float:
    total = 0.0
    for label, logit in zip(labels, logits, strict=True):
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


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-max(-60.0, min(60.0, value))))


def fit_platt(labels: Sequence[int], logits: Sequence[float]) -> dict[str, float]:
    """Fit a two-parameter logistic calibration with damped Newton steps."""
    if len(labels) != len(logits) or not labels or len(set(labels)) != 2:
        raise ValueError("Platt scaling needs equal, non-empty inputs with both classes")
    slope, intercept = 1.0, 0.0
    for _ in range(100):
        grad_slope = grad_intercept = h_ss = h_si = h_ii = 0.0
        for label, logit in zip(labels, logits, strict=True):
            x = max(-60.0, min(60.0, float(logit)))
            probability = _sigmoid(slope * x + intercept)
            variance = probability * (1.0 - probability)
            residual = probability - int(label)
            grad_slope += residual * x
            grad_intercept += residual
            h_ss += variance * x * x
            h_si += variance * x
            h_ii += variance
        # ponytail: tiny ridge keeps the 2x2 Newton solve finite on separable OOF scores.
        ridge = 1e-8
        grad_slope += ridge * slope
        grad_intercept += ridge * intercept
        h_ss += ridge
        h_ii += ridge
        determinant = h_ss * h_ii - h_si * h_si
        if determinant <= 1e-20:
            break
        delta_slope = (h_ii * grad_slope - h_si * grad_intercept) / determinant
        delta_intercept = (h_ss * grad_intercept - h_si * grad_slope) / determinant
        slope -= delta_slope
        intercept -= delta_intercept
        if max(abs(delta_slope), abs(delta_intercept)) < 1e-7:
            break
    return {"slope": slope, "intercept": intercept}


def _fit_isotonic(labels: Sequence[int], logits: Sequence[float]) -> dict[str, list[float]]:
    """Fit monotone stepwise PAVA calibration, merging tied scores first."""
    if len(labels) != len(logits) or not labels or len(set(labels)) != 2:
        raise ValueError("isotonic calibration needs equal, non-empty inputs with both classes")
    grouped: list[list[float]] = []
    for score, label in sorted(zip(logits, labels, strict=True)):
        score = float(score)
        if grouped and grouped[-1][0] == score:
            grouped[-1][1] += int(label)
            grouped[-1][2] += 1
        else:
            grouped.append([score, int(label), 1])
    blocks: list[list[float]] = []
    for score, positives, count in grouped:
        blocks.append([score, score, positives, count])
        while len(blocks) > 1:
            left, right = blocks[-2], blocks[-1]
            if left[2] / left[3] <= right[2] / right[3]:
                break
            blocks[-2:] = [[left[0], right[1], left[2] + right[2], left[3] + right[3]]]
    return {
        "upper_bounds": [block[1] for block in blocks],
        "values": [block[2] / block[3] for block in blocks],
    }


def _apply_isotonic(logits: Sequence[float], model: dict[str, list[float]]) -> list[float]:
    bounds, values = model["upper_bounds"], model["values"]
    if not bounds or len(bounds) != len(values):
        raise ValueError("invalid isotonic model")
    return [values[min(bisect_left(bounds, float(logit)), len(values) - 1)] for logit in logits]


def fit_calibrators(labels: Sequence[int], logits: Sequence[float]) -> dict[str, object]:
    """Compare uncalibrated, temperature, Platt, and isotonic using TRAIN OOF only."""
    if len(labels) != len(logits) or not labels or len(set(labels)) != 2:
        raise ValueError("calibration needs equal, non-empty inputs with both classes")
    from .metrics import binary_metrics

    platt = fit_platt(labels, logits)
    isotonic = _fit_isotonic(labels, logits)
    temperature = fit_temperature(labels, logits)
    candidates = {
        "uncalibrated": [
            _sigmoid(max(-60.0, min(60.0, float(logit)))) for logit in logits
        ],
        "temperature": apply_temperature(logits, temperature),
        "platt": [_sigmoid(platt["slope"] * float(logit) + platt["intercept"]) for logit in logits],
        "isotonic": _apply_isotonic(logits, isotonic),
    }
    scores = {
        name: {
            key: binary_metrics(labels, probabilities)[key]
            for key in ("log_loss", "brier", "ece")
        }
        for name, probabilities in candidates.items()
    }
    selected = min(
        scores,
        key=lambda name: (
            scores[name]["log_loss"],
            scores[name]["brier"],
            scores[name]["ece"],
        ),
    )
    return {
        "fit_scope": "TRAIN_OOF_ONLY",
        "temperature": temperature,
        "platt": platt,
        "isotonic": isotonic,
        "scores": scores,
        "selected_method": selected,
    }


def apply_calibrator(logits: Sequence[float], model: dict[str, object]) -> list[float]:
    method = model.get("selected_method")
    if method == "uncalibrated":
        return [_sigmoid(max(-60.0, min(60.0, float(logit)))) for logit in logits]
    if method == "temperature":
        temperature = model.get("temperature")
        if not isinstance(temperature, (int, float)):
            raise ValueError("invalid temperature model")
        return apply_temperature(logits, float(temperature))
    if method == "platt":
        parameters = model["platt"]
        if not isinstance(parameters, dict):
            raise ValueError("invalid Platt parameters")
        return [
            _sigmoid(float(parameters["slope"]) * float(logit) + float(parameters["intercept"]))
            for logit in logits
        ]
    if method == "isotonic":
        parameters = model["isotonic"]
        if not isinstance(parameters, dict):
            raise ValueError("invalid isotonic parameters")
        return _apply_isotonic(logits, parameters)
    raise ValueError(f"unknown calibration method: {method}")


def _mcc(labels: Sequence[int], predictions: Sequence[int]) -> float:
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions, strict=True))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions, strict=True))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions, strict=True))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions, strict=True))
    denominator = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
    return (tp * tn - fp * fn) / denominator if denominator else 0.0


def select_abstention_threshold(
    labels: Sequence[int],
    probabilities: Sequence[float],
) -> dict[str, float]:
    """Choose one MCC threshold from TRAIN OOF probabilities."""
    if len(labels) != len(probabilities) or not labels:
        raise ValueError("labels and probabilities must be non-empty and equal length")
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


def selective_metrics(
    labels: Sequence[int],
    probabilities: Sequence[float],
    coverage_targets: Sequence[float] = (0.5, 0.75, 0.9, 1.0),
) -> list[dict[str, float | int]]:
    """Report risk and accuracy after retaining the highest-confidence rows."""
    if len(labels) != len(probabilities) or not labels:
        raise ValueError("labels and probabilities must be non-empty and equal length")
    confidence = [
        max(float(probability), 1.0 - float(probability)) for probability in probabilities
    ]
    ordered = sorted(confidence, reverse=True)
    results = []
    for target in coverage_targets:
        if not 0 < target <= 1:
            raise ValueError("coverage targets must be in (0, 1]")
        cutoff = ordered[max(0, ceil(len(ordered) * target) - 1)]
        selected = [
            (int(label), int(probability >= 0.5))
            for label, probability, score in zip(labels, probabilities, confidence, strict=True)
            if score >= cutoff
        ]
        correct = sum(label == prediction for label, prediction in selected)
        count = len(selected)
        error_rate = (count - correct) / count
        results.append(
            {
                "target_coverage": float(target),
                "confidence_threshold": cutoff,
                "n_selected": count,
                "coverage": count / len(labels),
                "accuracy": correct / count,
                "risk": error_rate,
                "error_rate": error_rate,
                "abstention_rate": 1 - count / len(labels),
            }
        )
    return results


def selective_metrics_at_thresholds(
    labels: Sequence[int],
    probabilities: Sequence[float],
    thresholds: Sequence[dict[str, float]],
) -> list[dict[str, float | int | None]]:
    """Apply confidence cutoffs frozen from TRAIN OOF predictions."""
    if len(labels) != len(probabilities) or not labels:
        raise ValueError("labels and probabilities must be non-empty and equal length")
    confidence = [max(float(p), 1.0 - float(p)) for p in probabilities]
    results = []
    for item in thresholds:
        cutoff = float(item["confidence_threshold"])
        if not 0.5 <= cutoff <= 1.0:
            raise ValueError("confidence thresholds must be in [0.5, 1]")
        selected = [
            (int(label), int(probability >= 0.5))
            for label, probability, score in zip(
                labels, probabilities, confidence, strict=True
            )
            if score >= cutoff
        ]
        count = len(selected)
        errors = sum(label != prediction for label, prediction in selected)
        results.append(
            {
                "target_coverage": float(item["target_coverage"]),
                "confidence_threshold": cutoff,
                "n_selected": count,
                "coverage": count / len(labels),
                "accuracy": 1.0 - errors / count if count else None,
                "risk": errors / count if count else None,
                "error_rate": errors / count if count else None,
                "abstention_rate": 1 - count / len(labels),
            }
        )
    return results

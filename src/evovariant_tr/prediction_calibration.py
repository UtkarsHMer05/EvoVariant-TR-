"""Leakage-safe probability calibration for development prediction rows.

The functions in this module fit calibration maps on one split and evaluate
them on a disjoint split.  They are intentionally small and dependency-free so
the local development continuation does not need a new scientific package.
They are not a locked-test evaluator and reject malformed probability inputs.
"""

from __future__ import annotations

import math
from typing import Any

from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc, compute_ece


class PredictionCalibrationError(ValueError):
    """Raised when calibration inputs cannot support a safe fit."""


def _validate_inputs(scores: list[float], labels: list[int]) -> None:
    if len(scores) != len(labels) or not scores:
        raise PredictionCalibrationError("scores and labels must be aligned and non-empty")
    if set(labels) != {0, 1}:
        raise PredictionCalibrationError("calibration requires both classes")
    if any(
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(float(score))
        or not 0.0 <= float(score) <= 1.0
        for score in scores
    ):
        raise PredictionCalibrationError(
            "calibration scores must be finite probabilities in [0, 1]"
        )
    if any(label not in {0, 1} for label in labels):
        raise PredictionCalibrationError("labels must be binary integers")


def _logit(score: float) -> float:
    clipped = min(max(score, 1e-8), 1.0 - 1e-8)
    return math.log(clipped / (1.0 - clipped))


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        inverse = math.exp(-value)
        return 1.0 / (1.0 + inverse)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def fit_platt(
    scores: list[float],
    labels: list[int],
    *,
    max_iterations: int = 100,
) -> dict[str, float | int]:
    """Fit a two-parameter logistic map on logit-transformed probabilities."""
    _validate_inputs(scores, labels)
    if max_iterations <= 0:
        raise PredictionCalibrationError("max_iterations must be positive")
    features = [_logit(float(score)) for score in scores]
    intercept = 0.0
    slope = 1.0
    regularization = 1e-8
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        probabilities = [_sigmoid(intercept + slope * feature) for feature in features]
        weights = [probability * (1.0 - probability) for probability in probabilities]
        gradient_intercept = sum(
            probability - label for probability, label in zip(probabilities, labels, strict=True)
        )
        gradient_slope = sum(
            (probability - label) * feature
            for probability, label, feature in zip(probabilities, labels, features, strict=True)
        )
        h00 = sum(weights) + regularization
        h01 = sum(weight * feature for weight, feature in zip(weights, features, strict=True))
        h11 = (
            sum(
                weight * feature * feature
                for weight, feature in zip(weights, features, strict=True)
            )
            + regularization
        )
        determinant = h00 * h11 - h01 * h01
        if determinant <= 0.0 or not math.isfinite(determinant):
            raise PredictionCalibrationError("Platt Hessian is singular or non-finite")
        step_intercept = (h11 * gradient_intercept - h01 * gradient_slope) / determinant
        step_slope = (-h01 * gradient_intercept + h00 * gradient_slope) / determinant
        intercept -= step_intercept
        slope -= step_slope
        if max(abs(step_intercept), abs(step_slope)) < 1e-9:
            break
    if not math.isfinite(intercept) or not math.isfinite(slope):
        raise PredictionCalibrationError("Platt fit produced non-finite parameters")
    return {
        "intercept": intercept,
        "slope": slope,
        "iterations": iterations,
        "fit_count": len(scores),
    }


def apply_platt(scores: list[float], parameters: dict[str, float | int]) -> list[float]:
    try:
        intercept = float(parameters["intercept"])
        slope = float(parameters["slope"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PredictionCalibrationError("invalid Platt parameters") from exc
    if not math.isfinite(intercept) or not math.isfinite(slope):
        raise PredictionCalibrationError("Platt parameters must be finite")
    return [_sigmoid(intercept + slope * _logit(float(score))) for score in scores]


def fit_isotonic(scores: list[float], labels: list[int]) -> dict[str, Any]:
    """Fit a deterministic weighted pool-adjacent-violators map."""
    _validate_inputs(scores, labels)
    grouped: list[dict[str, float | int]] = []
    for score in sorted(set(float(value) for value in scores)):
        members = [label for value, label in zip(scores, labels, strict=True) if value == score]
        grouped.append(
            {
                "x_high": score,
                "weight": len(members),
                "sum": sum(members),
            }
        )
    blocks: list[dict[str, float | int]] = []
    for block in grouped:
        blocks.append(block)
        while len(blocks) >= 2:
            previous = blocks[-2]
            current = blocks[-1]
            previous_mean = float(previous["sum"]) / int(previous["weight"])
            current_mean = float(current["sum"]) / int(current["weight"])
            if previous_mean <= current_mean:
                break
            previous["sum"] = float(previous["sum"]) + float(current["sum"])
            previous["weight"] = int(previous["weight"]) + int(current["weight"])
            previous["x_high"] = current["x_high"]
            blocks.pop()
    thresholds = [float(block["x_high"]) for block in blocks]
    values = [float(block["sum"]) / int(block["weight"]) for block in blocks]
    return {
        "thresholds": thresholds,
        "values": values,
        "fit_count": len(scores),
        "block_count": len(blocks),
    }


def apply_isotonic(scores: list[float], parameters: dict[str, Any]) -> list[float]:
    try:
        thresholds = [float(value) for value in parameters["thresholds"]]
        values = [float(value) for value in parameters["values"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise PredictionCalibrationError("invalid isotonic parameters") from exc
    if not thresholds or len(thresholds) != len(values):
        raise PredictionCalibrationError("isotonic thresholds and values must be aligned")
    if any(not math.isfinite(value) for value in thresholds + values):
        raise PredictionCalibrationError("isotonic parameters must be finite")
    if any(left > right for left, right in zip(thresholds, thresholds[1:], strict=False)):
        raise PredictionCalibrationError("isotonic thresholds must be ordered")
    result: list[float] = []
    for score in scores:
        index = next(
            (index for index, threshold in enumerate(thresholds) if score <= threshold),
            len(values) - 1,
        )
        result.append(min(max(values[index], 0.0), 1.0))
    return result


def probability_metrics(scores: list[float], labels: list[int]) -> dict[str, float | int]:
    """Return validation-only metrics for calibrated probabilities."""
    _validate_inputs(scores, labels)
    predictions = [int(score >= 0.5) for score in scores]
    correct = sum(
        prediction == label for prediction, label in zip(predictions, labels, strict=True)
    )
    brier = sum((score - label) ** 2 for score, label in zip(scores, labels, strict=True)) / len(
        scores
    )
    epsilon = 1e-15
    nll = -sum(
        label * math.log(max(score, epsilon)) + (1 - label) * math.log(max(1.0 - score, epsilon))
        for score, label in zip(scores, labels, strict=True)
    ) / len(scores)
    ece, max_gap = compute_ece(scores, labels)
    return {
        "auroc": compute_auc_roc(scores, labels),
        "auprc": compute_auc_pr(scores, labels),
        "accuracy": correct / len(scores),
        "brier": brier,
        "nll": nll,
        "ece": ece,
        "max_calibration_gap": max_gap,
        "n": len(scores),
    }

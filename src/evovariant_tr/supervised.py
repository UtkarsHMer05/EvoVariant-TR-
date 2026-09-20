"""Small deterministic downstream classifiers with split-leakage guards.

These CPU implementations are engineering primitives and synthetic-test targets.
They are not trained on the real Phase 3 data until model features and gates pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrainingRow:
    normalized_variant_id: str
    split: str
    label: int
    features: tuple[float, ...]
    gene_symbol: str | None = None


def validate_training_rows(
    train_rows: list[TrainingRow],
    validation_rows: list[TrainingRow],
    *,
    require_gene_grouping: bool = True,
) -> None:
    """Reject locked labels and identity/gene leakage before fitting."""
    for row in [*train_rows, *validation_rows]:
        if row.split == "LOCKED_TEST":
            raise ValueError("locked-test rows cannot enter downstream training")
        if row.label not in (0, 1):
            raise ValueError("training labels must be binary")
    train_ids = {row.normalized_variant_id for row in train_rows}
    validation_ids = {row.normalized_variant_id for row in validation_rows}
    if train_ids & validation_ids:
        raise ValueError("train/validation normalized IDs overlap")
    if require_gene_grouping:
        train_genes = {row.gene_symbol for row in train_rows if row.gene_symbol}
        validation_genes = {row.gene_symbol for row in validation_rows if row.gene_symbol}
        if train_genes & validation_genes:
            raise ValueError("train/validation gene groups overlap")


def _validate_matrix(rows: list[TrainingRow]) -> int:
    if not rows:
        raise ValueError("at least one training row is required")
    dimensions = {len(row.features) for row in rows}
    if len(dimensions) != 1 or not dimensions:
        raise ValueError("all rows must have the same non-empty feature dimension")
    return next(iter(dimensions))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


@dataclass(frozen=True)
class LogisticModel:
    weights: tuple[float, ...]
    bias: float
    seed: int
    steps: int

    def predict_proba(self, features: tuple[float, ...] | list[float]) -> float:
        if len(features) != len(self.weights):
            raise ValueError("feature dimension does not match fitted model")
        return _sigmoid(self.bias + sum(w * x for w, x in zip(self.weights, features, strict=True)))


def fit_logistic_regression(
    rows: list[TrainingRow],
    *,
    learning_rate: float = 0.1,
    steps: int = 200,
    l2: float = 0.0,
    seed: int = 42,
) -> LogisticModel:
    """Fit a tiny deterministic logistic model with batch gradient descent."""
    dimension = _validate_matrix(rows)
    if steps < 1 or learning_rate <= 0 or l2 < 0:
        raise ValueError("invalid logistic optimization parameters")
    if {row.label for row in rows} != {0, 1}:
        raise ValueError("logistic training requires both classes")
    weights = [0.0] * dimension
    bias = 0.0
    for _ in range(steps):
        grad_w = [0.0] * dimension
        grad_b = 0.0
        for row in rows:
            prediction = _sigmoid(
                bias + sum(w * x for w, x in zip(weights, row.features, strict=True))
            )
            error = prediction - row.label
            grad_b += error
            for index, value in enumerate(row.features):
                grad_w[index] += error * value
        scale = 1.0 / len(rows)
        bias -= learning_rate * grad_b * scale
        for index in range(dimension):
            weights[index] -= learning_rate * (grad_w[index] * scale + l2 * weights[index])
    return LogisticModel(tuple(weights), bias, seed, steps)


@dataclass(frozen=True)
class StumpModel:
    feature_index: int
    threshold: float
    positive_if_greater: bool

    def predict_proba(self, features: tuple[float, ...] | list[float]) -> float:
        value = features[self.feature_index]
        positive = value >= self.threshold if self.positive_if_greater else value < self.threshold
        return 1.0 if positive else 0.0


def fit_decision_stump(rows: list[TrainingRow]) -> StumpModel:
    """Fit a transparent one-feature tree baseline on training rows only."""
    dimension = _validate_matrix(rows)
    if {row.label for row in rows} != {0, 1}:
        raise ValueError("stump training requires both classes")
    best: tuple[int, int, float, int] | None = None
    for feature_index in range(dimension):
        thresholds = sorted({row.features[feature_index] for row in rows})
        for threshold in thresholds:
            for positive_if_greater in (True, False):
                errors = sum(
                    int(
                        (
                            1
                            if (
                                (row.features[feature_index] >= threshold)
                                if positive_if_greater
                                else (row.features[feature_index] < threshold)
                            )
                            else 0
                        )
                        != row.label
                    )
                    for row in rows
                )
                candidate = (errors, feature_index, threshold, int(positive_if_greater))
                if best is None or candidate < best:
                    best = candidate
    assert best is not None
    _, feature_index, threshold, positive_flag = best
    return StumpModel(feature_index, threshold, bool(positive_flag))


@dataclass(frozen=True)
class MLPModel:
    hidden_weights: tuple[tuple[float, ...], ...]
    hidden_bias: tuple[float, ...]
    output_weights: tuple[float, ...]
    output_bias: float

    def predict_proba(self, features: tuple[float, ...] | list[float]) -> float:
        hidden = [
            math.tanh(
                bias + sum(weight * value for weight, value in zip(weights, features, strict=True))
            )
            for weights, bias in zip(self.hidden_weights, self.hidden_bias, strict=True)
        ]
        return _sigmoid(
            self.output_bias + sum(w * h for w, h in zip(self.output_weights, hidden, strict=True))
        )


def fit_mlp(
    rows: list[TrainingRow],
    *,
    hidden_width: int = 4,
    learning_rate: float = 0.05,
    epochs: int = 100,
    seed: int = 42,
) -> MLPModel:
    """Fit a small one-hidden-layer MLP for CPU smoke tests and baselines."""
    dimension = _validate_matrix(rows)
    if hidden_width < 1 or learning_rate <= 0 or epochs < 1:
        raise ValueError("invalid MLP optimization parameters")
    if {row.label for row in rows} != {0, 1}:
        raise ValueError("MLP training requires both classes")
    hidden_weights = [
        [0.01 * ((seed + unit + index) % 7 - 3) for index in range(dimension)]
        for unit in range(hidden_width)
    ]
    hidden_bias = [0.0] * hidden_width
    output_weights = [0.0] * hidden_width
    output_bias = 0.0
    for _ in range(epochs):
        for row in rows:
            hidden = [
                math.tanh(
                    bias
                    + sum(
                        weight * value for weight, value in zip(weights, row.features, strict=True)
                    )
                )
                for weights, bias in zip(hidden_weights, hidden_bias, strict=True)
            ]
            prediction = _sigmoid(
                output_bias + sum(w * h for w, h in zip(output_weights, hidden, strict=True))
            )
            error = prediction - row.label
            old_output = output_weights.copy()
            for unit in range(hidden_width):
                output_weights[unit] -= learning_rate * error * hidden[unit]
                hidden_error = error * old_output[unit] * (1.0 - hidden[unit] ** 2)
                hidden_bias[unit] -= learning_rate * hidden_error
                for index, value in enumerate(row.features):
                    hidden_weights[unit][index] -= learning_rate * hidden_error * value
            output_bias -= learning_rate * error
    return MLPModel(
        tuple(tuple(row) for row in hidden_weights),
        tuple(hidden_bias),
        tuple(output_weights),
        output_bias,
    )


def fit_classifier(kind: str, rows: list[TrainingRow], **params: Any) -> Any:
    """Dispatch the required classical model families by explicit name."""
    if kind == "logistic_regression":
        return fit_logistic_regression(rows, **params)
    if kind == "decision_stump":
        return fit_decision_stump(rows)
    if kind == "mlp":
        return fit_mlp(rows, **params)
    raise ValueError(f"unknown classifier family: {kind}")

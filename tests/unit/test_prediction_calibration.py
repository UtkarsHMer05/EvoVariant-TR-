"""Tests for leakage-safe development prediction calibration."""

from __future__ import annotations

import math

import pytest

from evovariant_tr.prediction_calibration import (
    PredictionCalibrationError,
    apply_isotonic,
    apply_platt,
    fit_isotonic,
    fit_platt,
    probability_metrics,
)


def test_platt_fit_is_deterministic_and_finite() -> None:
    scores = [0.05, 0.2, 0.8, 0.95]
    labels = [0, 0, 1, 1]
    parameters = fit_platt(scores, labels)
    assert parameters["fit_count"] == 4
    assert all(value == value for value in apply_platt(scores, parameters))


def test_platt_rejects_invalid_inputs() -> None:
    with pytest.raises(PredictionCalibrationError, match="aligned"):
        fit_platt([], [])
    with pytest.raises(PredictionCalibrationError, match="both classes"):
        fit_platt([0.2, 0.3], [0, 0])
    with pytest.raises(PredictionCalibrationError, match="finite"):
        fit_platt([math.nan, 0.3], [0, 1])
    with pytest.raises(PredictionCalibrationError, match="max_iterations"):
        fit_platt([0.2, 0.8], [0, 1], max_iterations=0)


def test_platt_application_rejects_invalid_parameters() -> None:
    with pytest.raises(PredictionCalibrationError, match="invalid Platt"):
        apply_platt([0.2], {})
    with pytest.raises(PredictionCalibrationError, match="finite"):
        apply_platt([0.2], {"intercept": math.nan, "slope": 1.0})


def test_isotonic_is_monotone() -> None:
    parameters = fit_isotonic([0.1, 0.2, 0.3, 0.4], [1, 0, 1, 1])
    calibrated = apply_isotonic([0.1, 0.2, 0.3, 0.4], parameters)
    assert calibrated == sorted(calibrated)
    assert parameters["block_count"] < 4


def test_probability_metrics_requires_both_classes() -> None:
    with pytest.raises(PredictionCalibrationError, match="both classes"):
        probability_metrics([0.2, 0.3], [0, 0])


def test_invalid_isotonic_parameters_fail_closed() -> None:
    with pytest.raises(PredictionCalibrationError, match="aligned"):
        apply_isotonic([0.2], {"thresholds": [0.2], "values": []})
    with pytest.raises(PredictionCalibrationError, match="invalid isotonic"):
        apply_isotonic([0.2], {})
    with pytest.raises(PredictionCalibrationError, match="finite"):
        apply_isotonic([0.2], {"thresholds": [math.nan], "values": [0.5]})
    with pytest.raises(PredictionCalibrationError, match="ordered"):
        apply_isotonic([0.2], {"thresholds": [0.4, 0.2], "values": [0.0, 1.0]})


def test_probability_metrics_reports_validation_values() -> None:
    metrics = probability_metrics([0.1, 0.9], [0, 1])
    assert metrics["n"] == 2
    assert metrics["accuracy"] == 1.0
    assert metrics["auroc"] == 1.0


def test_isotonic_application_clips_and_extrapolates() -> None:
    parameters = {"thresholds": [0.2, 0.8], "values": [-1.0, 2.0]}
    assert apply_isotonic([0.1, 0.5, 0.9], parameters) == [0.0, 1.0, 1.0]

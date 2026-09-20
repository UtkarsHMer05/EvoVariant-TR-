"""Predeclared plans and freeze guards for later ML-extension phases."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrozenAnalysisConfig:
    config: dict[str, Any]
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {"config": self.config, "sha256": self.sha256}


def freeze_analysis_config(config: dict[str, Any]) -> FrozenAnalysisConfig:
    """Content-hash a configuration before any locked evaluation."""
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return FrozenAnalysisConfig(dict(config), hashlib.sha256(encoded).hexdigest())


def require_frozen_config(
    frozen: FrozenAnalysisConfig,
    *,
    expected_sha256: str,
) -> None:
    if frozen.sha256 != expected_sha256:
        raise ValueError("analysis configuration hash does not match the frozen evaluation input")


def build_ablation_matrix() -> list[dict[str, Any]]:
    """Return the predeclared one-component-at-a-time ablation matrix."""
    components = ("rc", "external_baseline", "embedding_features", "calibration")
    return [
        {"ablation_id": f"remove_{component}", "removed_component": component}
        for component in components
    ]


def build_robustness_matrix() -> list[dict[str, Any]]:
    """Return only scientifically meaningful, predeclared perturbations."""
    return [
        {"robustness_id": "center_shift_minus_1", "operation": "shift_center", "offset_bp": -1},
        {"robustness_id": "center_shift_plus_1", "operation": "shift_center", "offset_bp": 1},
        {"robustness_id": "orientation_forward", "operation": "orientation", "value": "forward"},
        {"robustness_id": "orientation_reverse", "operation": "orientation", "value": "reverse"},
    ]


def build_learning_curve_sizes(total: int) -> list[int]:
    """Return grouped learning-curve fractions without exceeding the source size."""
    if total < 1:
        raise ValueError("total must be positive")
    return sorted({max(1, round(total * fraction)) for fraction in (0.1, 0.2, 0.4, 0.6, 0.8, 1.0)})

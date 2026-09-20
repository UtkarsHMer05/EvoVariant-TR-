"""Bounded validation-only hyperparameter search primitives."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrialResult:
    trial_number: int
    config: dict[str, Any]
    validation_metric: float
    status: str = "COMPLETED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_number": self.trial_number,
            "config": self.config,
            "validation_metric": self.validation_metric,
            "status": self.status,
        }


@dataclass(frozen=True)
class ValidationOnlyStudy:
    study_name: str
    direction: str
    seed: int
    trials: tuple[TrialResult, ...]

    @property
    def best_trial(self) -> TrialResult:
        if not self.trials:
            raise ValueError("study has no completed trials")
        return (
            max(self.trials, key=lambda trial: trial.validation_metric)
            if self.direction == "maximize"
            else min(self.trials, key=lambda trial: trial.validation_metric)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_name": self.study_name,
            "direction": self.direction,
            "seed": self.seed,
            "selection_split": "VALIDATION",
            "trials": [trial.to_dict() for trial in self.trials],
            "best_trial": self.best_trial.to_dict(),
        }


def run_validation_only_study(
    *,
    study_name: str,
    configs: list[dict[str, Any]],
    objective: Callable[[dict[str, Any]], float],
    seed: int = 42,
    direction: str = "maximize",
    selection_split: str = "VALIDATION",
) -> ValidationOnlyStudy:
    """Evaluate a bounded config list without permitting locked-test selection."""
    if not configs:
        raise ValueError("at least one HPO configuration is required")
    if direction not in {"maximize", "minimize"}:
        raise ValueError("direction must be maximize or minimize")
    if selection_split != "VALIDATION":
        raise ValueError("HPO selection is validation-only")
    trials = tuple(
        TrialResult(index, dict(config), float(objective(config)))
        for index, config in enumerate(configs)
    )
    return ValidationOnlyStudy(study_name, direction, seed, trials)


def write_study(path: str | Path, study: ValidationOnlyStudy) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(study.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target

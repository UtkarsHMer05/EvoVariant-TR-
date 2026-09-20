"""Artifact-driven figure/table specifications without manual result values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    title: str
    source_artifacts: tuple[str, ...]
    required_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "source_artifacts": list(self.source_artifacts),
            "required_fields": list(self.required_fields),
        }


REQUIRED_FIGURES: tuple[FigureSpec, ...] = (
    FigureSpec(
        "model_auroc", "Model AUROC comparison", ("benchmark.json",), ("model_id", "auc_roc")
    ),
    FigureSpec(
        "model_auprc", "Model AUPRC comparison", ("benchmark.json",), ("model_id", "auc_pr")
    ),
    FigureSpec(
        "calibration",
        "Calibration and reliability",
        ("calibration.json",),
        ("confidence", "observed_frequency"),
    ),
    FigureSpec("risk_coverage", "Risk-coverage", ("abstention.json",), ("coverage", "risk")),
    FigureSpec("ensemble", "Ensemble comparison", ("ensemble.json",), ("model_id", "metric")),
    FigureSpec(
        "cost_latency", "Latency and cost", ("cost_ledger.jsonl",), ("run_id", "measured_seconds")
    ),
)


def build_figure_manifest(registered_artifacts: set[str]) -> list[dict[str, Any]]:
    """Return only figure specs whose sources are registered artifacts."""
    specs = []
    for figure in REQUIRED_FIGURES:
        if all(source in registered_artifacts for source in figure.source_artifacts):
            specs.append(figure.to_dict())
    return specs


def require_artifact_fields(artifact: dict[str, Any], fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if field not in artifact]
    if missing:
        raise ValueError(f"registered artifact is missing required fields: {missing}")

"""Artifact-driven figure/table specifications without manual result values.

The registry manifest produced here is deliberately metadata-only.  It is the
input contract for a later renderer, not a source of metrics itself.  In
particular, a missing or non-eligible run produces a deterministic ``BLOCKED``
manifest instead of a synthetic plot or a placeholder score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evovariant_tr.evidence import AGGREGATE_ALLOWED_STAGES
from evovariant_tr.registry import Registry, RegistryError, RunStatus, verify_output_hashes

FIGURE_MANIFEST_SCHEMA_VERSION = "1.0"


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


def build_registry_figure_manifest(
    registry: Registry,
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Build a deterministic figure-input manifest from verified registry outputs.

    Only completed PRELIMINARY or FINAL runs can supply current scientific
    figure inputs. Every eligible run is checked against its recorded output
    hashes before it is exposed. The returned structure intentionally carries
    no metrics, predictions, or inferred values; it only records the available
    source paths and their already-registered hashes.
    """
    source_records: dict[str, list[dict[str, str]]] = {}
    eligible_runs: list[dict[str, Any]] = []
    excluded_runs: list[dict[str, str]] = []
    blockers: list[str] = []
    all_runs = registry.list_runs()

    for record in all_runs:
        if record.status is not RunStatus.COMPLETED:
            continue
        if record.evidence_stage not in AGGREGATE_ALLOWED_STAGES:
            excluded_runs.append(
                {
                    "run_id": record.run_id,
                    "reason": f"evidence stage {record.evidence_stage.value} is not eligible",
                }
            )
            continue
        try:
            verify_output_hashes(record, repo_root)
        except RegistryError as exc:
            blockers.append(str(exc))
            continue

        eligible_runs.append(
            {
                "run_id": record.run_id,
                "evidence_stage": record.evidence_stage.value,
                "output_paths": list(record.output_paths),
                "output_hashes": dict(sorted(record.output_hashes.items())),
            }
        )
        for output_path in record.output_paths:
            normalized_path = Path(output_path).as_posix()
            source_name = Path(normalized_path).name
            source_records.setdefault(source_name, []).append(
                {
                    "run_id": record.run_id,
                    "path": normalized_path,
                    "sha256": record.output_hashes[normalized_path],
                }
            )

    for entries in source_records.values():
        entries.sort(key=lambda entry: (entry["run_id"], entry["path"]))

    required_figures: list[dict[str, Any]] = []
    available_figures: list[dict[str, Any]] = []
    missing_sources: set[str] = set()
    for figure in REQUIRED_FIGURES:
        sources = {
            source: list(source_records.get(source, []))
            for source in figure.source_artifacts
        }
        missing = sorted(source for source, entries in sources.items() if not entries)
        entry = figure.to_dict()
        entry["available"] = not missing
        entry["missing_sources"] = missing
        entry["source_records"] = sources
        required_figures.append(entry)
        if missing:
            missing_sources.update(missing)
        else:
            available_figures.append(entry)

    if not eligible_runs:
        blockers.append("no completed PRELIMINARY or FINAL run outputs are registered")
    if missing_sources:
        blockers.append(
            "missing registered source artifact(s): " + ", ".join(sorted(missing_sources))
        )

    blockers = sorted(set(blockers))
    status = (
        "READY"
        if not blockers and len(available_figures) == len(REQUIRED_FIGURES)
        else "BLOCKED"
    )
    return {
        "schema_version": FIGURE_MANIFEST_SCHEMA_VERSION,
        "status": status,
        "registered_run_count": len(all_runs),
        "eligible_completed_run_count": len(eligible_runs),
        "eligible_runs": eligible_runs,
        "excluded_completed_runs": sorted(excluded_runs, key=lambda entry: entry["run_id"]),
        "required_figures": required_figures,
        "available_figures": available_figures,
        "blockers": blockers,
    }


def write_figure_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    """Write a stable, atomically replaced registry figure manifest."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target

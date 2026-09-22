"""Registry-driven Phase 17 figure, table, and report artifacts.

The renderer is intentionally boring and deterministic. It consumes only
hash-verified outputs from completed registry runs and never supplies a metric
or prediction of its own. When any required input is absent or malformed it
writes a blocked bundle manifest and no scientific output files.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from evovariant_tr.evidence import AGGREGATE_ALLOWED_STAGES, EvidenceStage
from evovariant_tr.registry import (
    Registry,
    RegistryError,
    RunStatus,
    hash_file,
    verify_output_hashes,
)

FIGURE_MANIFEST_SCHEMA_VERSION = "1.2"
BUNDLE_SCHEMA_VERSION = "1.0"

# Conditional families are disabled only by an explicit, status-checked project
# decision artifact. They are never silently removed from the study contract.
CONDITIONAL_SOURCE_POLICIES: dict[str, dict[str, str]] = {
    "finetuning.json": {
        "phase": "10",
        "status": "DEFERRED_BY_COMPUTE",
        "reason": (
            "Phase 10 fine-tuning was not executed due to the documented compute budget deferral."
        ),
        "decision_artifact": "artifacts/modal/phase10_adaptation_deferral_20260921.json",
    },
    "hpo_importance.json": {
        "phase": "9",
        "status": "NOT_APPLICABLE_WITH_DOCUMENTED_REASON",
        "reason": (
            "The bounded validation-only HPO evidence has four trials per study and no "
            "predeclared parameter-importance estimator; an importance figure would overstate "
            "the available evidence."
        ),
        "decision_artifact": "artifacts/phase9/hpo_parameter_importance_deferral_20260922.json",
    },
    "loss.json": {
        "phase": "10",
        "status": "DEFERRED_BY_COMPUTE",
        "reason": (
            "Phase 10 adaptation was deferred before training; no scientifically valid train/"
            "validation loss series exists and no loss values may be inferred from downstream "
            "metrics."
        ),
        "decision_artifact": "artifacts/modal/phase10_adaptation_deferral_20260921.json",
    },
    "context_length.json": {
        "phase": "13",
        "status": "NOT_APPLICABLE_WITH_DOCUMENTED_REASON",
        "reason": (
            "The predeclared context-length cell was conditional on additional foundation-model "
            "extraction. Phase 13 records it as not run under the paid authorization, and the "
            "cached 8192-bp features do not contain alternate context windows."
        ),
        "decision_artifact": "artifacts/phase13/context_length_deferral_20260922.json",
    },
}


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    title: str
    source_artifacts: tuple[str, ...]
    required_fields: tuple[str, ...]
    x_field: str
    y_field: str
    error_low_field: str | None = None
    error_high_field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "figure_id": self.figure_id,
            "title": self.title,
            "source_artifacts": list(self.source_artifacts),
            "required_fields": list(self.required_fields),
            "x_field": self.x_field,
            "y_field": self.y_field,
        }
        if self.error_low_field is not None and self.error_high_field is not None:
            result["error_low_field"] = self.error_low_field
            result["error_high_field"] = self.error_high_field
        return result


@dataclass(frozen=True)
class TableSpec:
    table_id: str
    title: str
    source_artifacts: tuple[str, ...]
    required_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "title": self.title,
            "source_artifacts": list(self.source_artifacts),
            "required_fields": list(self.required_fields),
        }


# Source names and fields form the result-artifact contract. A future
# scientific runner may emit these files, but it may not bypass the registry or
# silently change the field contract.
REQUIRED_FIGURES: tuple[FigureSpec, ...] = (
    FigureSpec(
        "model_auroc",
        "Model AUROC comparison",
        ("benchmark.json",),
        ("model_id", "auc_roc"),
        "model_id",
        "auc_roc",
        "auc_roc_ci_low",
        "auc_roc_ci_high",
    ),
    FigureSpec(
        "model_auprc",
        "Model AUPRC comparison",
        ("benchmark.json",),
        ("model_id", "auc_pr"),
        "model_id",
        "auc_pr",
        "auc_pr_ci_low",
        "auc_pr_ci_high",
    ),
    FigureSpec(
        "roc_curves",
        "ROC curves",
        ("roc.json",),
        ("model_id", "fpr", "tpr"),
        "fpr",
        "tpr",
    ),
    FigureSpec(
        "pr_curves",
        "Precision-recall curves",
        ("pr.json",),
        ("model_id", "recall", "precision"),
        "recall",
        "precision",
    ),
    FigureSpec(
        "confusion_matrices",
        "Confusion matrices",
        ("confusion_matrix.json",),
        ("model_id", "tn", "fp", "fn", "tp"),
        "model_id",
        "tp",
    ),
    FigureSpec(
        "calibration",
        "Calibration and reliability",
        ("calibration.json",),
        ("confidence", "observed_frequency"),
        "confidence",
        "observed_frequency",
    ),
    FigureSpec(
        "risk_coverage",
        "Risk-coverage",
        ("abstention.json",),
        ("coverage", "risk"),
        "coverage",
        "risk",
    ),
    FigureSpec(
        "context_length_metric",
        "Context length versus metric",
        ("context_length.json",),
        ("context_length", "metric"),
        "context_length",
        "metric",
    ),
    FigureSpec(
        "embedding_layer_metric",
        "Embedding layer versus metric",
        ("embedding_layer.json",),
        ("layer", "metric"),
        "layer",
        "metric",
    ),
    FigureSpec(
        "hpo_trial_history",
        "HPO trial history",
        ("hpo.json",),
        ("trial_id", "objective"),
        "trial_id",
        "objective",
    ),
    FigureSpec(
        "hpo_parameter_importance",
        "HPO parameter importance",
        ("hpo_importance.json",),
        ("parameter", "importance"),
        "parameter",
        "importance",
    ),
    FigureSpec(
        "train_validation_loss",
        "Train and validation loss",
        ("loss.json",),
        ("epoch", "train_loss", "validation_loss"),
        "epoch",
        "train_loss",
    ),
    FigureSpec(
        "learning_curve",
        "Learning curve",
        ("learning_curve.json",),
        ("train_size", "metric"),
        "train_size",
        "metric",
    ),
    FigureSpec(
        "error_correlation",
        "Error correlation and disagreement",
        ("error_correlation.json",),
        ("model_id", "error_correlation"),
        "model_id",
        "error_correlation",
    ),
    FigureSpec(
        "ensemble",
        "Ensemble comparison",
        ("ensemble.json",),
        ("model_id", "metric"),
        "model_id",
        "metric",
    ),
    FigureSpec(
        "ablation",
        "Ablation study",
        ("ablation.json",),
        ("component", "metric"),
        "component",
        "metric",
    ),
    FigureSpec(
        "subgroup",
        "Subgroup or per-gene performance",
        ("subgroup.json",),
        ("subgroup", "metric", "sample_count"),
        "subgroup",
        "metric",
    ),
    FigureSpec(
        "cost_latency",
        "Latency and cost",
        ("cost_ledger.jsonl",),
        ("run_id", "measured_seconds"),
        "run_id",
        "measured_seconds",
    ),
    FigureSpec(
        "temporal_cohort_flow",
        "Temporal cohort flow",
        ("temporal_cohort.json",),
        ("stage", "count"),
        "stage",
        "count",
    ),
)

REQUIRED_TABLES: tuple[TableSpec, ...] = (
    TableSpec("dataset_flow", "Dataset flow", ("dataset_flow.json",), ("stage", "count")),
    TableSpec(
        "split_composition", "Split composition", ("split_composition.json",), ("split", "count")
    ),
    TableSpec("model_registry", "Model registry", ("model_registry.json",), ("model_id", "status")),
    TableSpec(
        "zero_shot_benchmark",
        "Zero-shot benchmark",
        ("benchmark.json",),
        ("model_id", "auc_roc", "auc_pr"),
    ),
    TableSpec("trained_models", "Trained models", ("trained_models.json",), ("model_id", "metric")),
    TableSpec(
        "hpo_best_configs", "HPO best configurations", ("hpo.json",), ("trial_id", "objective")
    ),
    TableSpec(
        "fine_tuning_summary", "Fine-tuning summary", ("finetuning.json",), ("model_id", "metric")
    ),
    TableSpec("ensemble_summary", "Ensemble summary", ("ensemble.json",), ("model_id", "metric")),
    TableSpec(
        "calibration_summary",
        "Calibration summary",
        ("calibration.json",),
        ("confidence", "observed_frequency"),
    ),
    TableSpec("ablation_results", "Ablation results", ("ablation.json",), ("component", "metric")),
    TableSpec(
        "subgroup_results",
        "Subgroup results",
        ("subgroup.json",),
        ("subgroup", "metric", "sample_count"),
    ),
    TableSpec(
        "limitations_failures",
        "Limitations and failures",
        ("failures.json",),
        ("component", "reason"),
    ),
)

_TEXT_FIELDS = frozenset(
    {
        "model_id",
        "run_id",
        "trial_id",
        "parameter",
        "component",
        "subgroup",
        "stage",
        "split",
        "status",
        "reason",
    }
)


def build_figure_manifest(registered_artifacts: set[str]) -> list[dict[str, Any]]:
    """Return figure specs whose sources are registered artifact names."""
    return [
        figure.to_dict()
        for figure in REQUIRED_FIGURES
        if all(source in registered_artifacts for source in figure.source_artifacts)
    ]


def require_artifact_fields(artifact: dict[str, Any], fields: tuple[str, ...]) -> None:
    """Require named fields in one already-decoded artifact object."""
    missing = [field for field in fields if field not in artifact]
    if missing:
        raise ValueError(f"registered artifact is missing required fields: {missing}")


def _stable_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def _load_rows(path: Path) -> list[dict[str, Any]]:
    """Load a JSON/JSONL artifact as a list of row objects."""
    try:
        if path.suffix == ".jsonl":
            rows: list[Any] = []
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_number} is not valid JSON: {exc.msg}") from exc
        else:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                rows = raw
            elif isinstance(raw, dict):
                nested = next(
                    (raw[key] for key in ("rows", "records", "data") if key in raw),
                    None,
                )
                rows = nested if isinstance(nested, list) else [raw]
            else:
                raise ValueError("top-level artifact must be an object or array")
    except OSError as exc:
        raise ValueError(f"cannot read artifact: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"artifact is not valid JSON: {exc.msg}") from exc

    if not rows:
        raise ValueError("artifact contains no rows")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("every artifact row must be an object")
    return [row for row in rows if isinstance(row, dict)]


def _validate_rows(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for row_index, row in enumerate(rows):
        missing = [field for field in fields if field not in row]
        if missing:
            errors.append(f"row {row_index}: missing required fields {missing}")
            continue
        for field in fields:
            value = row[field]
            if field in _TEXT_FIELDS:
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"row {row_index}: {field} must be a non-empty string")
            elif isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"row {row_index}: {field} must be a finite number")
            elif not math.isfinite(float(value)):
                errors.append(f"row {row_index}: {field} must be a finite number")
    return errors


def _inspect_artifact(path: Path, fields: tuple[str, ...]) -> list[str]:
    try:
        return _validate_rows(_load_rows(path), fields)
    except ValueError as exc:
        return [str(exc)]


def _safe_repo_relative(repo_root: Path, recorded_path: str) -> str:
    path = Path(recorded_path)
    if path.is_absolute():
        raise RegistryError(
            f"registered output path must be relative to repository root: {recorded_path}"
        )
    root = repo_root.resolve()
    target = (root / path).resolve()
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise RegistryError(
            f"registered output path escapes repository root: {recorded_path}"
        ) from exc
    return relative.as_posix()


def _source_records_for_spec(
    source_records: dict[str, list[dict[str, str]]],
    spec: FigureSpec | TableSpec,
    repo_root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    invalid: list[str] = []
    for source in spec.source_artifacts:
        entries: list[dict[str, Any]] = []
        for base_entry in source_records.get(source, []):
            entry: dict[str, Any] = dict(base_entry)
            try:
                path = repo_root / str(base_entry["path"])
                errors = _inspect_artifact(path, spec.required_fields)
            except (KeyError, RegistryError, ValueError) as exc:
                errors = [str(exc)]
            entry["validation_errors"] = errors
            entries.append(entry)
            if errors:
                invalid.append(
                    f"{source} ({base_entry.get('run_id', 'unknown')}): " + "; ".join(errors)
                )
        selected[source] = entries
    return selected, sorted(invalid)


def _eligible_run_metadata(record: Any) -> dict[str, Any]:
    """Return provenance/cost metadata, deliberately excluding scientific metrics."""
    return {
        "run_id": record.run_id,
        "evidence_stage": record.evidence_stage.value,
        "experiment_family": record.experiment_family,
        "model_name": record.model_name,
        "model_identity": record.model_identity,
        "model_revision": record.model_revision,
        "model_source": record.model_source,
        "checkpoint": record.checkpoint,
        "license_record": record.license_record,
        "hardware": record.hardware,
        "GPU": record.GPU,
        "runtime_seconds": record.runtime_seconds,
        "estimated_cost_usd": record.estimated_cost_usd,
        "measured_cost_usd": record.measured_cost_usd,
    }


def _conditional_source_policies(repo_root: Path) -> dict[str, dict[str, str]]:
    """Return conditional policies only when their decision artifact agrees."""
    active: dict[str, dict[str, str]] = {}
    for source, policy in CONDITIONAL_SOURCE_POLICIES.items():
        decision_path = repo_root / policy["decision_artifact"]
        if not decision_path.is_file():
            continue
        try:
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(decision, dict) and decision.get("status") == policy["status"]:
            active[source] = dict(policy)
    return active


def build_registry_figure_manifest(
    registry: Registry,
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Build a deterministic, hash-verified Phase 17 input manifest.

    Only completed PRELIMINARY or FINAL runs can supply current inputs. The
    manifest includes source metadata and field-validation errors, never row
    values or metrics. A renderer may proceed only when all required figures
    and tables have valid registered sources *and* at least one completed
    FINAL run contributes the registered source surface. Preliminary runs can
    populate the review bundle, but cannot promote it to the final bundle.
    """
    root = Path(repo_root).resolve()
    conditional_policies = _conditional_source_policies(root)
    source_records: dict[str, list[dict[str, str]]] = {}
    eligible_runs: list[dict[str, Any]] = []
    eligible_final_run_count = 0
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
            normalized_paths = [_safe_repo_relative(root, path) for path in record.output_paths]
            verify_output_hashes(record, root)
        except RegistryError as exc:
            blockers.append(str(exc))
            continue

        eligible_runs.append(
            {
                **_eligible_run_metadata(record),
                "output_paths": normalized_paths,
                "output_hashes": dict(sorted(record.output_hashes.items())),
            }
        )
        if record.evidence_stage is EvidenceStage.FINAL:
            eligible_final_run_count += 1
        for output_path in normalized_paths:
            source_name = Path(output_path).name
            source_records.setdefault(source_name, []).append(
                {
                    "run_id": record.run_id,
                    "path": output_path,
                    "sha256": record.output_hashes[output_path],
                }
            )

    for entries in source_records.values():
        entries.sort(key=lambda entry: (entry["run_id"], entry["path"]))

    required_figures: list[dict[str, Any]] = []
    available_figures: list[dict[str, Any]] = []
    required_tables: list[dict[str, Any]] = []
    available_tables: list[dict[str, Any]] = []
    not_applicable_figures: list[dict[str, str]] = []
    not_applicable_tables: list[dict[str, str]] = []
    missing_sources: set[str] = set()
    invalid_sources: set[str] = set()

    for figure in REQUIRED_FIGURES:
        sources, invalid = _source_records_for_spec(source_records, figure, root)
        missing = sorted(source for source, entries in sources.items() if not entries)
        entry = figure.to_dict()
        policy = next(
            (
                conditional_policies[source]
                for source in figure.source_artifacts
                if source in conditional_policies
            ),
            None,
        )
        if policy is not None:
            entry["applicability"] = "NOT_APPLICABLE_WITH_DOCUMENTED_REASON"
            entry["applicability_reason"] = policy["reason"]
            entry["decision_artifact"] = policy["decision_artifact"]
            entry["available"] = False
            entry["missing_sources"] = []
            entry["source_records"] = sources
            not_applicable_figures.append(
                {
                    "figure_id": figure.figure_id,
                    "source_artifact": figure.source_artifacts[0],
                    "phase": policy["phase"],
                    "status": policy["status"],
                    "reason": policy["reason"],
                    "decision_artifact": policy["decision_artifact"],
                }
            )
            required_figures.append(entry)
            continue
        entry["applicability"] = "REQUIRED"
        entry["available"] = not missing and not invalid
        entry["missing_sources"] = missing
        entry["source_records"] = sources
        required_figures.append(entry)
        if missing:
            missing_sources.update(missing)
        if invalid:
            invalid_sources.update(invalid)
        if entry["available"]:
            available_figures.append(entry)

    for table in REQUIRED_TABLES:
        sources, invalid = _source_records_for_spec(source_records, table, root)
        missing = sorted(source for source, entries in sources.items() if not entries)
        entry = table.to_dict()
        policy = next(
            (
                conditional_policies[source]
                for source in table.source_artifacts
                if source in conditional_policies
            ),
            None,
        )
        if policy is not None:
            entry["applicability"] = "NOT_APPLICABLE_WITH_DOCUMENTED_REASON"
            entry["applicability_reason"] = policy["reason"]
            entry["decision_artifact"] = policy["decision_artifact"]
            entry["available"] = False
            entry["missing_sources"] = []
            entry["source_records"] = sources
            not_applicable_tables.append(
                {
                    "table_id": table.table_id,
                    "source_artifact": table.source_artifacts[0],
                    "phase": policy["phase"],
                    "status": policy["status"],
                    "reason": policy["reason"],
                    "decision_artifact": policy["decision_artifact"],
                }
            )
            required_tables.append(entry)
            continue
        entry["applicability"] = "REQUIRED"
        entry["available"] = not missing and not invalid
        entry["missing_sources"] = missing
        entry["source_records"] = sources
        required_tables.append(entry)
        if missing:
            missing_sources.update(missing)
        if invalid:
            invalid_sources.update(invalid)
        if entry["available"]:
            available_tables.append(entry)

    if not eligible_runs:
        blockers.append("no completed PRELIMINARY or FINAL run outputs are registered")
    if eligible_final_run_count == 0:
        blockers.append(
            "no completed FINAL run outputs are registered; preliminary sources "
            "cannot produce the final bundle"
        )
    if missing_sources:
        blockers.append(
            "missing registered source artifact(s): " + ", ".join(sorted(missing_sources))
        )
    if invalid_sources:
        blockers.append(
            "invalid registered source artifact(s): " + "; ".join(sorted(invalid_sources))
        )

    blockers = sorted(set(blockers))
    status = (
        "READY"
        if not blockers
        and len(available_figures) == len(REQUIRED_FIGURES) - len(not_applicable_figures)
        and len(available_tables) == len(REQUIRED_TABLES) - len(not_applicable_tables)
        else "BLOCKED"
    )
    return {
        "schema_version": FIGURE_MANIFEST_SCHEMA_VERSION,
        "status": status,
        "registered_run_count": len(all_runs),
        "eligible_completed_run_count": len(eligible_runs),
        "eligible_final_run_count": eligible_final_run_count,
        "applicable_required_figure_count": len(REQUIRED_FIGURES) - len(not_applicable_figures),
        "applicable_required_table_count": len(REQUIRED_TABLES) - len(not_applicable_tables),
        "not_applicable_figure_families": sorted(
            not_applicable_figures, key=lambda entry: entry["figure_id"]
        ),
        "not_applicable_table_families": sorted(
            not_applicable_tables, key=lambda entry: entry["table_id"]
        ),
        "eligible_runs": eligible_runs,
        "excluded_completed_runs": sorted(excluded_runs, key=lambda entry: entry["run_id"]),
        "required_figures": required_figures,
        "available_figures": available_figures,
        "required_tables": required_tables,
        "available_tables": available_tables,
        "blockers": blockers,
    }


def write_figure_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    """Write a stable, atomically replaced registry figure manifest."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(_stable_json_bytes(manifest))
    temporary.replace(target)
    return target


def _verified_rows_for_entry(
    entry: dict[str, Any], repo_root: Path, required_fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_records = entry.get("source_records", {})
    if not isinstance(source_records, dict):
        raise RegistryError(
            f"{entry.get('figure_id', entry.get('table_id', 'artifact'))}: source_records invalid"
        )
    for source in entry.get("source_artifacts", []):
        records = source_records.get(source, [])
        if not isinstance(records, list) or not records:
            raise RegistryError(f"missing source records for {source}")
        for record in records:
            if not isinstance(record, dict):
                raise RegistryError(f"source record for {source} is not an object")
            relative = _safe_repo_relative(repo_root, str(record["path"]))
            target = repo_root / relative
            if not target.is_file():
                raise RegistryError(f"registered source artifact is missing: {relative}")
            actual_hash = hash_file(target)
            if actual_hash != record.get("sha256"):
                raise RegistryError(f"registered source artifact is not reproducible: {relative}")
            artifact_rows = _load_rows(target)
            errors = _validate_rows(artifact_rows, required_fields)
            if errors:
                raise RegistryError(f"{relative}: " + "; ".join(errors))
            rows.extend(artifact_rows)
    rows.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    return rows


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RegistryError(f"expected finite numeric value, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise RegistryError(f"expected finite numeric value, got {value!r}")
    return result


def _format_number(value: float) -> str:
    return format(value, ".6g")


def _render_svg(spec: FigureSpec, rows: list[dict[str, Any]]) -> bytes:
    """Render a small deterministic SVG from source rows, without plotting deps."""
    width, height = 800, 480
    left, top, right, bottom = 78, 58, 28, 82
    plot_width, plot_height = width - left - right, height - top - bottom
    ordered = list(rows)
    numeric_x = all(
        not isinstance(row.get(spec.x_field), bool)
        and isinstance(row.get(spec.x_field), (int, float))
        for row in ordered
    )
    if numeric_x:
        ordered.sort(key=lambda row: _number(row[spec.x_field]))
    else:
        ordered.sort(key=lambda row: str(row[spec.x_field]))
    y_values = [_number(row[spec.y_field]) for row in ordered]
    y_min, y_max = min(y_values), max(y_values)
    if y_min == y_max:
        padding = max(abs(y_min) * 0.05, 1.0)
        y_min -= padding
        y_max += padding
    else:
        padding = (y_max - y_min) * 0.05
        y_min -= padding
        y_max += padding

    def x_position(index: int, row: dict[str, Any]) -> float:
        if numeric_x:
            values = [_number(item[spec.x_field]) for item in ordered]
            x_value = _number(row[spec.x_field])
            x_low, x_high = min(values), max(values)
            if x_low == x_high:
                return left + plot_width / 2
            return left + (x_value - x_low) / (x_high - x_low) * plot_width
        return left + (index + 0.5) / len(ordered) * plot_width

    def y_position(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" '
        f'font-family="sans-serif" font-size="18">{escape(spec.title)}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" '
        f'y2="{top + plot_height}" stroke="#333"/>',
        f'<text x="{left + plot_width / 2:.1f}" y="{height - 18}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="12">{escape(spec.x_field)}</text>',
        f'<text x="16" y="{top + plot_height / 2:.1f}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="12" transform="rotate(-90 16 '
        f'{top + plot_height / 2:.1f})">{escape(spec.y_field)}</text>',
        f'<text x="{left - 8}" y="{top + 4}" text-anchor="end" '
        f'font-family="sans-serif" font-size="10">{_format_number(y_max)}</text>',
        f'<text x="{left - 8}" y="{top + plot_height}" text-anchor="end" '
        f'font-family="sans-serif" font-size="10">{_format_number(y_min)}</text>',
    ]
    points: list[str] = []
    for index, row in enumerate(ordered):
        x = x_position(index, row)
        y = y_position(_number(row[spec.y_field]))
        points.append(f"{x:.3f},{y:.3f}")
        if numeric_x:
            elements.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3" fill="#2563eb"/>')
        else:
            bar_width = plot_width / max(len(ordered) * 1.5, 1)
            elements.append(
                f'<rect x="{x - bar_width / 2:.3f}" y="{y:.3f}" width="{bar_width:.3f}" '
                f'height="{top + plot_height - y:.3f}" fill="#2563eb"/>'
            )
        if spec.error_low_field and spec.error_high_field:
            low = row.get(spec.error_low_field)
            high = row.get(spec.error_high_field)
            if low is not None and high is not None:
                low_y, high_y = y_position(_number(low)), y_position(_number(high))
                elements.append(
                    f'<line x1="{x:.3f}" y1="{low_y:.3f}" x2="{x:.3f}" y2="{high_y:.3f}" '
                    'stroke="#111"/>'
                )
        if not numeric_x:
            label = escape(str(row[spec.x_field]))
            elements.append(
                f'<text x="{x:.3f}" y="{top + plot_height + 18}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="10">{label}</text>'
            )
    if numeric_x:
        elements.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="#2563eb" stroke-width="2"/>'
        )
    elements.append(
        '<text x="790" y="468" text-anchor="end" font-family="sans-serif" font-size="10">'
        "source-derived</text>"
    )
    elements.append("</svg>")
    return ("\n".join(elements) + "\n").encode("utf-8")


def _output_path(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise RegistryError(f"generated output path escapes bundle directory: {relative}") from exc
    return target


def _prior_output_paths(root: Path, manifest_name: str = "bundle_manifest.json") -> list[str]:
    manifest_path = root / manifest_name
    if not manifest_path.is_file():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot safely replace malformed bundle manifest: {exc}") from exc
    outputs = payload.get("outputs", [])
    if not isinstance(outputs, list):
        raise RegistryError("cannot safely replace bundle manifest with invalid outputs")
    paths: list[str] = []
    for output in outputs:
        if isinstance(output, dict) and isinstance(output.get("path"), str):
            _output_path(root, output["path"])
            paths.append(output["path"])
    return paths


def _remove_previous_outputs(root: Path, paths: list[str]) -> None:
    for relative in paths:
        target = _output_path(root, relative)
        if target.is_file() or target.is_symlink():
            target.unlink()


def _output_record(root: Path, relative: str, kind: str, identifier: str) -> dict[str, str]:
    target = _output_path(root, relative)
    return {
        "id": identifier,
        "kind": kind,
        "path": Path(relative).as_posix(),
        "sha256": hash_file(target),
    }


def _cost_summary(eligible_runs: list[dict[str, Any]]) -> dict[str, Any]:
    def total(field: str) -> float | None:
        values = [run[field] for run in eligible_runs if isinstance(run.get(field), (int, float))]
        return sum(float(value) for value in values) if values else None

    return {
        "runs": [
            {
                "run_id": run["run_id"],
                "evidence_stage": run["evidence_stage"],
                "GPU": run.get("GPU"),
                "runtime_seconds": run.get("runtime_seconds"),
                "estimated_cost_usd": run.get("estimated_cost_usd"),
                "measured_cost_usd": run.get("measured_cost_usd"),
            }
            for run in eligible_runs
        ],
        "totals": {
            "runtime_seconds": total("runtime_seconds"),
            "estimated_cost_usd": total("estimated_cost_usd"),
            "measured_cost_usd": total("measured_cost_usd"),
        },
    }


def _blocked_bundle(
    manifest: dict[str, Any], manifest_hash: str, blockers: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "status": "BLOCKED",
        "source_manifest_sha256": manifest_hash,
        "required_figure_count": manifest.get(
            "applicable_required_figure_count", len(manifest.get("required_figures", []))
        ),
        "required_table_count": manifest.get(
            "applicable_required_table_count", len(manifest.get("required_tables", []))
        ),
        "not_applicable_figure_families": manifest.get("not_applicable_figure_families", []),
        "not_applicable_table_families": manifest.get("not_applicable_table_families", []),
        "outputs": [],
        "blockers": sorted(set(blockers)),
        "scientific_outputs_included": False,
    }


def render_figure_bundle(
    manifest: dict[str, Any],
    *,
    repo_root: str | Path,
    output_dir: str | Path,
) -> Path:
    """Render a deterministic Phase 17 export bundle from a manifest.

    A blocked input manifest produces only ``bundle_manifest.json``. Existing
    outputs listed by the previous bundle manifest are removed narrowly by
    their recorded relative paths, so a rerun cannot leave stale figures.
    """
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    previous_paths = _prior_output_paths(root)
    manifest_hash = hashlib.sha256(_stable_json_bytes(manifest)).hexdigest()
    blockers = [str(blocker) for blocker in manifest.get("blockers", [])]

    if manifest.get("status") != "READY":
        _remove_previous_outputs(root, previous_paths)
        bundle = _blocked_bundle(manifest, manifest_hash, blockers)
        target = root / "bundle_manifest.json"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(_stable_json_bytes(bundle))
        temporary.replace(target)
        return target

    repo = Path(repo_root).resolve()
    generated: list[tuple[str, bytes, str, str]] = []
    try:
        for entry in manifest.get("available_figures", []):
            spec = next(
                figure for figure in REQUIRED_FIGURES if figure.figure_id == entry["figure_id"]
            )
            rows = _verified_rows_for_entry(entry, repo, spec.required_fields)
            generated.append(
                (
                    f"bundle/figures/{spec.figure_id}.svg",
                    _render_svg(spec, rows),
                    "figure",
                    spec.figure_id,
                )
            )
        for entry in manifest.get("available_tables", []):
            table_spec = next(
                table for table in REQUIRED_TABLES if table.table_id == entry["table_id"]
            )
            rows = _verified_rows_for_entry(entry, repo, table_spec.required_fields)
            generated.append(
                (
                    f"bundle/tables/{table_spec.table_id}.json",
                    _stable_json_bytes(
                        {
                            "table_id": table_spec.table_id,
                            "title": table_spec.title,
                            "rows": rows,
                        }
                    ),
                    "table",
                    table_spec.table_id,
                )
            )
        eligible_runs = list(manifest.get("eligible_runs", []))
        applicable_figure_count = manifest.get(
            "applicable_required_figure_count", len(REQUIRED_FIGURES)
        )
        applicable_table_count = manifest.get(
            "applicable_required_table_count", len(REQUIRED_TABLES)
        )
        not_applicable_figure_count = len(manifest.get("not_applicable_figure_families", []))
        not_applicable_table_count = len(manifest.get("not_applicable_table_families", []))
        methods = (
            "# Methods\n\n"
            "This bundle was generated from hash-verified outputs of completed "
            "PRELIMINARY or FINAL registry runs. Figures and tables are derived "
            "from source artifact rows; no values are entered by the renderer.\n\n"
            f"- Source manifest SHA-256: `{manifest_hash}`\n"
            f"- Eligible completed runs: `{len(eligible_runs)}`\n"
            f"- Applicable required figure families: `{applicable_figure_count}`\n"
            f"- Applicable required tables: `{applicable_table_count}`\n"
            f"- Not-applicable figure families: `{not_applicable_figure_count}`\n"
            f"- Not-applicable table families: `{not_applicable_table_count}`\n"
        ).encode()
        limitations = (
            b"# Limitations\n\n"
            b"- Registry provenance does not establish clinical validity or external validity.\n"
            b"- The export does not change the frozen protocol, selection rules, or locked-test "
            b"gate.\n"
            b"- Uncertainty is shown only when the registered artifact supplies the required "
            b"bounds.\n"
            b"- Missing, malformed, or tampered artifacts block the bundle rather than being "
            b"inferred.\n"
        )
        generated.extend(
            [
                ("bundle/methods.md", methods, "report", "methods"),
                ("bundle/limitations.md", limitations, "report", "limitations"),
                (
                    "bundle/compute_cost.json",
                    _stable_json_bytes(_cost_summary(eligible_runs)),
                    "report",
                    "compute_cost",
                ),
                (
                    "bundle/model_provenance.json",
                    _stable_json_bytes(
                        {"runs": eligible_runs, "scientific_metrics_included": False}
                    ),
                    "report",
                    "model_provenance",
                ),
            ]
        )
    except (KeyError, RegistryError, StopIteration, TypeError, ValueError) as exc:
        _remove_previous_outputs(root, previous_paths)
        bundle = _blocked_bundle(
            manifest,
            manifest_hash,
            blockers + [f"renderer refused source manifest: {exc}"],
        )
        target = root / "bundle_manifest.json"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(_stable_json_bytes(bundle))
        temporary.replace(target)
        return target

    _remove_previous_outputs(root, previous_paths)
    output_records: list[dict[str, str]] = []
    for relative, content, kind, identifier in generated:
        target = _output_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        output_records.append(_output_record(root, relative, kind, identifier))
    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "status": "READY",
        "source_manifest_sha256": manifest_hash,
        "required_figure_count": manifest.get(
            "applicable_required_figure_count", len(REQUIRED_FIGURES)
        ),
        "required_table_count": manifest.get(
            "applicable_required_table_count", len(REQUIRED_TABLES)
        ),
        "not_applicable_figure_families": manifest.get("not_applicable_figure_families", []),
        "not_applicable_table_families": manifest.get("not_applicable_table_families", []),
        "outputs": output_records,
        "blockers": [],
        "scientific_outputs_included": True,
    }
    target = root / "bundle_manifest.json"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(_stable_json_bytes(bundle))
    temporary.replace(target)
    return target


def render_preliminary_figure_bundle(
    manifest: dict[str, Any],
    *,
    repo_root: str | Path,
    output_dir: str | Path,
) -> Path:
    """Render only available registry sources as an explicitly preliminary bundle.

    The complete Phase 17 renderer remains fail-closed. This companion export
    is useful for reviewing real development-subset artifacts while making it
    impossible to confuse them with a complete or citable final bundle.
    """
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest_name = "preliminary_bundle_manifest.json"
    previous_paths = _prior_output_paths(root, manifest_name)
    manifest_hash = hashlib.sha256(_stable_json_bytes(manifest)).hexdigest()
    available_figures = list(manifest.get("available_figures", []))
    available_tables = list(manifest.get("available_tables", []))
    blockers = [str(blocker) for blocker in manifest.get("blockers", [])]
    if not available_figures and not available_tables:
        _remove_previous_outputs(root, previous_paths)
        bundle: dict[str, Any] = {
            "schema_version": "1.0-preliminary",
            "status": "BLOCKED",
            "evidence_stage": "PRELIMINARY",
            "promotable": False,
            "source_manifest_sha256": manifest_hash,
            "available_figure_count": 0,
            "available_table_count": 0,
            "outputs": [],
            "blockers": sorted(set(blockers or ["no valid preliminary sources available"])),
            "scientific_outputs_included": False,
        }
        target = root / manifest_name
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(_stable_json_bytes(bundle))
        temporary.replace(target)
        return target

    repo = Path(repo_root).resolve()
    generated: list[tuple[str, bytes, str, str]] = []
    try:
        for entry in available_figures:
            figure_spec = next(
                figure for figure in REQUIRED_FIGURES if figure.figure_id == entry["figure_id"]
            )
            generated.append(
                (
                    f"bundle/figures/{figure_spec.figure_id}.svg",
                    _render_svg(
                        figure_spec,
                        _verified_rows_for_entry(entry, repo, figure_spec.required_fields),
                    ),
                    "figure",
                    figure_spec.figure_id,
                )
            )
        for entry in available_tables:
            table_spec = next(
                table for table in REQUIRED_TABLES if table.table_id == entry["table_id"]
            )
            generated.append(
                (
                    f"bundle/tables/{table_spec.table_id}.json",
                    _stable_json_bytes(
                        {
                            "table_id": table_spec.table_id,
                            "title": table_spec.title,
                            "rows": _verified_rows_for_entry(
                                entry, repo, table_spec.required_fields
                            ),
                        }
                    ),
                    "table",
                    table_spec.table_id,
                )
            )
    except (KeyError, RegistryError, StopIteration, TypeError, ValueError) as exc:
        _remove_previous_outputs(root, previous_paths)
        blockers.append(f"preliminary renderer refused source manifest: {exc}")
        generated = []

    if not generated:
        bundle = {
            "schema_version": "1.0-preliminary",
            "status": "BLOCKED",
            "evidence_stage": "PRELIMINARY",
            "promotable": False,
            "source_manifest_sha256": manifest_hash,
            "available_figure_count": len(available_figures),
            "available_table_count": len(available_tables),
            "outputs": [],
            "blockers": sorted(set(blockers)),
            "scientific_outputs_included": False,
        }
        target = root / manifest_name
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(_stable_json_bytes(bundle))
        temporary.replace(target)
        return target

    _remove_previous_outputs(root, previous_paths)
    output_records: list[dict[str, str]] = []
    for relative, content, kind, identifier in generated:
        target = _output_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        output_records.append(_output_record(root, relative, kind, identifier))
    bundle = {
        "schema_version": "1.0-preliminary",
        "status": "PARTIAL",
        "evidence_stage": "PRELIMINARY",
        "promotable": False,
        "source_manifest_sha256": manifest_hash,
        "available_figure_count": len(available_figures),
        "available_table_count": len(available_tables),
        "outputs": output_records,
        "blockers": sorted(set(blockers)),
        "scientific_outputs_included": True,
    }
    target = root / manifest_name
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(_stable_json_bytes(bundle))
    temporary.replace(target)
    return target

"""Evidence-stage types and claim guards for EvoVariant-TR.

Every run and result carries exactly one :class:`EvidenceStage`. The stage
controls where an output may be written, how it may be labeled, and whether it
may be cited. Promotion is a deliberate, logged act — never automatic.

Guards implemented here (Milestone 13):
- synthetic scorer outputs cannot be written to final-results directories;
- legacy BRCA1 metrics cannot enter EvoVariant-TR aggregate tables;
- forbidden stage promotions raise loudly;
- the stage label survives JSON/CSV/Parquet serialization.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class EvidenceStageError(RuntimeError):
    """Base error for evidence-stage policy violations."""


class ForbiddenPromotionError(EvidenceStageError):
    """Raised when a stage promotion is not allowed."""


class FinalPathWriteError(EvidenceStageError):
    """Raised when a non-final output targets a final-results path."""


class EvidenceStage(str, Enum):
    """Evidence maturity of a run or result.

    Serialization label is the enum value itself (e.g. ``"SYNTHETIC_TEST"``).
    """

    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    LEGACY_BASELINE = "LEGACY_BASELINE"
    ENGINEERING_PILOT = "ENGINEERING_PILOT"
    PRELIMINARY = "PRELIMINARY"
    FINAL = "FINAL"

    @property
    def ui_description(self) -> str:
        return _UI_DESCRIPTIONS[self]

    @property
    def citable(self) -> bool:
        """Only FINAL outputs may be cited as EvoVariant-TR science."""
        return self is EvidenceStage.FINAL


_UI_DESCRIPTIONS: dict[EvidenceStage, str] = {
    EvidenceStage.SYNTHETIC_TEST: (
        "Synthetic test output: exercises software only. Not scientific evidence."
    ),
    EvidenceStage.LEGACY_BASELINE: (
        "Legacy baseline from the old project (different estimand, assembly, and "
        "threshold). Not EvoVariant-TR evidence."
    ),
    EvidenceStage.ENGINEERING_PILOT: (
        "Engineering pilot: validates infrastructure, not performance. "
        "Not performance evidence."
    ),
    EvidenceStage.PRELIMINARY: (
        "Preliminary result from a registered real run before final approval. "
        "Not a final claim."
    ),
    EvidenceStage.FINAL: (
        "Final frozen result from the approved primary run and frozen analysis "
        "plan. Citable with stated limitations."
    ),
}

# Path segments that mark final-results locations.
FINAL_PATH_SEGMENTS = frozenset({"final", "final_results"})

# Stages allowed into EvoVariant-TR aggregate tables.
AGGREGATE_ALLOWED_STAGES = frozenset({EvidenceStage.PRELIMINARY, EvidenceStage.FINAL})

# Source markers that identify legacy-project outputs (old BRCA1 evaluation).
LEGACY_SOURCE_MARKERS = ("legacy", "brca1", "evaluation/results")

# Scorer kinds and the only stage their outputs may carry.
SCORER_REQUIRED_STAGE = {
    "fake": EvidenceStage.SYNTHETIC_TEST,
    "legacy": EvidenceStage.LEGACY_BASELINE,
}

# The only promotions that may ever be granted (each still requires a reason).
_ALLOWED_PROMOTIONS: dict[EvidenceStage, frozenset[EvidenceStage]] = {
    EvidenceStage.PRELIMINARY: frozenset({EvidenceStage.FINAL}),
}


def stage_from_label(label: str) -> EvidenceStage:
    """Parse a serialized stage label; fails loudly on unknown labels."""
    try:
        return EvidenceStage(label)
    except ValueError as exc:
        valid = ", ".join(stage.value for stage in EvidenceStage)
        raise EvidenceStageError(
            f"unknown evidence stage label {label!r}; valid labels: {valid}"
        ) from exc


def is_final_path(path: str | Path) -> bool:
    """True when any path segment marks a final-results location."""
    parts = {part.lower() for part in Path(path).parts}
    return bool(parts & FINAL_PATH_SEGMENTS)


def validate_stage_for_scorer(scorer_kind: str, stage: EvidenceStage) -> None:
    """Fake and legacy scorer outputs can never masquerade as real evidence."""
    required = SCORER_REQUIRED_STAGE.get(scorer_kind)
    if required is not None and stage is not required:
        raise ForbiddenPromotionError(
            f"scorer kind {scorer_kind!r} may only produce {required.value} "
            f"outputs, got {stage.value}"
        )


class ResultRecord(BaseModel):
    """A single metric/result artifact carrying its evidence stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_name: str
    value: float
    evidence_stage: EvidenceStage
    run_id: str | None = None
    source: str | None = None

    @field_validator("metric_name")
    @classmethod
    def _non_empty_metric(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("metric_name must be non-empty")
        return value


class PromotionEvent(BaseModel):
    """Immutable log entry for a deliberate stage promotion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_name: str
    from_stage: EvidenceStage
    to_stage: EvidenceStage
    reason: str
    promoted_at: str


def check_write_allowed(path: str | Path, stage: EvidenceStage) -> None:
    """Guard result writes: non-final outputs must not target final paths."""
    if is_final_path(path) and stage is not EvidenceStage.FINAL:
        raise FinalPathWriteError(
            f"evidence stage {stage.value} cannot be written to final-results "
            f"path {str(path)!r}; only FINAL outputs may live there"
        )


def write_result_record(record: ResultRecord, path: str | Path) -> Path:
    """Write a result record as JSON after enforcing the stage/path guard."""
    target = Path(path)
    check_write_allowed(target, record.evidence_stage)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def read_result_record(path: str | Path) -> ResultRecord:
    """Read and validate a JSON result record."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ResultRecord.model_validate(raw)


class AggregateTable:
    """EvoVariant-TR aggregate metric table.

    Rejects legacy BRCA1 metrics and any non-PRELIMINARY/FINAL stage so old or
    synthetic numbers can never enter project aggregate results.
    """

    def __init__(self) -> None:
        self._records: list[ResultRecord] = []

    def add(self, record: ResultRecord) -> None:
        if record.evidence_stage not in AGGREGATE_ALLOWED_STAGES:
            raise EvidenceStageError(
                f"evidence stage {record.evidence_stage.value} cannot enter an "
                f"EvoVariant-TR aggregate table; allowed: "
                f"{sorted(stage.value for stage in AGGREGATE_ALLOWED_STAGES)}"
            )
        source = (record.source or "").lower()
        for marker in LEGACY_SOURCE_MARKERS:
            if marker in source:
                raise EvidenceStageError(
                    f"legacy-project output (source contains {marker!r}) cannot "
                    f"enter an EvoVariant-TR aggregate table"
                )
        self._records.append(record)

    @property
    def records(self) -> tuple[ResultRecord, ...]:
        return tuple(self._records)

    def to_records_for_serialization(self) -> list[dict[str, Any]]:
        return [record.model_dump(mode="json") for record in self._records]


def promote(
    record: ResultRecord,
    target: EvidenceStage,
    *,
    reason: str,
    log: list[PromotionEvent] | None = None,
) -> ResultRecord:
    """Deliberately promote a record to a higher stage.

    Returns a NEW record; the input record is immutable and unchanged. Only
    PRELIMINARY -> FINAL is ever grantable, and only with a non-empty reason.
    """
    if not reason.strip():
        raise ForbiddenPromotionError("promotion requires a non-empty reason")
    allowed = _ALLOWED_PROMOTIONS.get(record.evidence_stage, frozenset())
    if target not in allowed:
        raise ForbiddenPromotionError(
            f"promotion {record.evidence_stage.value} -> {target.value} is "
            f"forbidden; only PRELIMINARY -> FINAL may ever be granted, and only "
            f"with a logged reason"
        )
    event = PromotionEvent(
        metric_name=record.metric_name,
        from_stage=record.evidence_stage,
        to_stage=target,
        reason=reason.strip(),
        promoted_at=datetime.now(timezone.utc).isoformat(),
    )
    if log is not None:
        log.append(event)
    return record.model_copy(update={"evidence_stage": target})


# ---------------------------------------------------------------------------
# Serialization helpers: the stage label must survive JSON/CSV/Parquet.
# ---------------------------------------------------------------------------


def records_to_json(records: list[ResultRecord]) -> str:
    return json.dumps(
        [record.model_dump(mode="json") for record in records], indent=2
    )


def records_from_json(text: str) -> list[ResultRecord]:
    return [ResultRecord.model_validate(raw) for raw in json.loads(text)]


_CSV_FIELDS = ("metric_name", "value", "evidence_stage", "run_id", "source")


def records_to_csv(records: list[ResultRecord]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    for record in records:
        dumped = record.model_dump(mode="json")
        writer.writerow({field: dumped.get(field, "") for field in _CSV_FIELDS})
    return buffer.getvalue()


def records_from_csv(text: str) -> list[ResultRecord]:
    records: list[ResultRecord] = []
    for row in csv.DictReader(io.StringIO(text)):
        payload = {
            "metric_name": row["metric_name"],
            "value": float(row["value"]),
            "evidence_stage": row["evidence_stage"],
            "run_id": row["run_id"] or None,
            "source": row["source"] or None,
        }
        records.append(ResultRecord.model_validate(payload))
    return records


def records_to_parquet(records: list[ResultRecord], path: str | Path) -> Path:
    """Write records to Parquet (stage stored as its string label)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(
        [record.model_dump(mode="json") for record in records]
    )
    pq.write_table(table, target)
    return target


def records_from_parquet(path: str | Path) -> list[ResultRecord]:
    import pyarrow.parquet as pq

    table = pq.read_table(Path(path))
    return [ResultRecord.model_validate(row) for row in table.to_pylist()]

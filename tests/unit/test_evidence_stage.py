"""Evidence-stage and claim-guard tests (Milestone 13).

Acceptance validations:
- Validation 1: a synthetic result cannot pass the final-result writer.
- Validation 2: evidence stage survives JSON/CSV/Parquet serialization.
Plus the forbidden-promotion matrix from docs/terminology/EVIDENCE_STAGES.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from evovariant_tr.evidence import (
    AggregateTable,
    EvidenceStage,
    EvidenceStageError,
    FinalPathWriteError,
    ForbiddenPromotionError,
    ResultRecord,
    check_write_allowed,
    is_final_path,
    promote,
    read_result_record,
    records_from_csv,
    records_from_json,
    records_from_parquet,
    records_to_csv,
    records_to_json,
    records_to_parquet,
    stage_from_label,
    validate_stage_for_scorer,
    write_result_record,
)

ALL_STAGES = list(EvidenceStage)


def make_record(
    stage: EvidenceStage,
    *,
    metric: str = "auroc",
    value: float = 0.75,
    source: str | None = None,
) -> ResultRecord:
    return ResultRecord(
        metric_name=metric,
        value=value,
        evidence_stage=stage,
        run_id="run_test_0001",
        source=source,
    )


# ---------------------------------------------------------------------------
# Enum, labels, UI descriptions
# ---------------------------------------------------------------------------


def test_enum_has_exactly_the_five_required_stages() -> None:
    assert [stage.value for stage in EvidenceStage] == [
        "SYNTHETIC_TEST",
        "LEGACY_BASELINE",
        "ENGINEERING_PILOT",
        "PRELIMINARY",
        "FINAL",
    ]


def test_every_stage_has_a_ui_safe_description() -> None:
    for stage in ALL_STAGES:
        description = stage.ui_description
        assert isinstance(description, str) and len(description) > 10
        lowered = description.lower()
        assert stage.value in description or stage.value.replace("_", " ").lower() in lowered


def test_only_final_is_citable() -> None:
    for stage in ALL_STAGES:
        assert stage.citable is (stage is EvidenceStage.FINAL)


def test_stage_from_label_round_trips_and_rejects_unknown() -> None:
    for stage in ALL_STAGES:
        assert stage_from_label(stage.value) is stage
    with pytest.raises(EvidenceStageError, match="unknown evidence stage"):
        stage_from_label("KINDA_FINAL")


# ---------------------------------------------------------------------------
# Validation 1: synthetic results cannot pass the final-result writer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "artifacts/results/final/auroc.json",
        "artifacts/final_results/auroc.json",
        "artifacts/results/FINAL/auroc.json",
    ],
)
def test_synthetic_result_cannot_pass_final_writer(tmp_path: Path, path: str) -> None:
    record = make_record(EvidenceStage.SYNTHETIC_TEST)
    target = tmp_path / path
    with pytest.raises(FinalPathWriteError):
        write_result_record(record, target)
    assert not target.exists()


@pytest.mark.parametrize(
    "stage",
    [
        EvidenceStage.LEGACY_BASELINE,
        EvidenceStage.ENGINEERING_PILOT,
        EvidenceStage.PRELIMINARY,
    ],
)
def test_other_non_final_stages_also_blocked_from_final_paths(
    tmp_path: Path, stage: EvidenceStage
) -> None:
    record = make_record(stage)
    with pytest.raises(FinalPathWriteError):
        write_result_record(record, tmp_path / "artifacts" / "results" / "final" / "x.json")


def test_final_stage_can_write_final_path_and_round_trip(tmp_path: Path) -> None:
    record = make_record(EvidenceStage.FINAL)
    target = tmp_path / "artifacts" / "results" / "final" / "auroc.json"
    written = write_result_record(record, target)
    assert read_result_record(written) == record


def test_non_final_stages_can_write_non_final_paths(tmp_path: Path) -> None:
    for stage in ALL_STAGES:
        target = tmp_path / "artifacts" / "results" / "preliminary" / f"{stage.value}.json"
        write_result_record(make_record(stage), target)
        assert target.exists()


def test_is_final_path_detection() -> None:
    assert is_final_path("artifacts/results/final/x.json")
    assert is_final_path("artifacts/final_results/x.json")
    assert not is_final_path("artifacts/results/preliminary/x.json")
    assert not is_final_path("artifacts/results/pilot/x.json")


def test_check_write_allowed_raises_with_stage_and_path() -> None:
    with pytest.raises(FinalPathWriteError) as excinfo:
        check_write_allowed("artifacts/results/final/x.json", EvidenceStage.ENGINEERING_PILOT)
    message = str(excinfo.value)
    assert "ENGINEERING_PILOT" in message
    assert "final" in message


# ---------------------------------------------------------------------------
# Scorer-kind guards: fake/legacy outputs cannot wear real-evidence stages
# ---------------------------------------------------------------------------


def test_fake_scorer_output_must_be_synthetic_test() -> None:
    validate_stage_for_scorer("fake", EvidenceStage.SYNTHETIC_TEST)  # ok
    for stage in ALL_STAGES:
        if stage is not EvidenceStage.SYNTHETIC_TEST:
            with pytest.raises(ForbiddenPromotionError):
                validate_stage_for_scorer("fake", stage)


def test_legacy_scorer_output_must_be_legacy_baseline() -> None:
    validate_stage_for_scorer("legacy", EvidenceStage.LEGACY_BASELINE)  # ok
    with pytest.raises(ForbiddenPromotionError):
        validate_stage_for_scorer("legacy", EvidenceStage.PRELIMINARY)


# ---------------------------------------------------------------------------
# Aggregate table: legacy BRCA1 metrics cannot enter EvoVariant-TR tables
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stage",
    [
        EvidenceStage.SYNTHETIC_TEST,
        EvidenceStage.LEGACY_BASELINE,
        EvidenceStage.ENGINEERING_PILOT,
    ],
)
def test_aggregate_table_rejects_non_evidence_stages(stage: EvidenceStage) -> None:
    table = AggregateTable()
    with pytest.raises(EvidenceStageError):
        table.add(make_record(stage))
    assert table.records == ()


@pytest.mark.parametrize(
    "source",
    [
        "legacy/evaluation/results/final_100",
        "evaluation/results/final_100/metrics.json",
        "BRCA1 500-row legacy endpoint eval",
    ],
)
def test_aggregate_table_rejects_legacy_brca1_sources(source: str) -> None:
    table = AggregateTable()
    record = make_record(EvidenceStage.PRELIMINARY, source=source)
    with pytest.raises(EvidenceStageError, match="legacy"):
        table.add(record)


def test_aggregate_table_accepts_clean_preliminary_and_final() -> None:
    table = AggregateTable()
    table.add(make_record(EvidenceStage.PRELIMINARY, source="run_20260818_pilot"))
    table.add(make_record(EvidenceStage.FINAL, source="run_20260901_primary"))
    assert len(table.records) == 2


# ---------------------------------------------------------------------------
# Forbidden promotions (matrix from EVIDENCE_STAGES.md)
# ---------------------------------------------------------------------------


def test_promotion_matrix_only_preliminary_to_final_is_grantable() -> None:
    for source_stage in ALL_STAGES:
        for target_stage in ALL_STAGES:
            record = make_record(source_stage)
            if source_stage is EvidenceStage.PRELIMINARY and target_stage is EvidenceStage.FINAL:
                continue  # the single grantable case, tested below
            with pytest.raises(ForbiddenPromotionError):
                promote(record, target_stage, reason="attempted forbidden promotion")


def test_preliminary_to_final_promotion_is_logged_and_immutable() -> None:
    log: list = []
    record = make_record(EvidenceStage.PRELIMINARY)
    promoted = promote(record, EvidenceStage.FINAL, reason="approved full run 2026-09-01", log=log)
    assert promoted.evidence_stage is EvidenceStage.FINAL
    assert record.evidence_stage is EvidenceStage.PRELIMINARY  # original unchanged
    assert len(log) == 1
    event = log[0]
    assert event.from_stage is EvidenceStage.PRELIMINARY
    assert event.to_stage is EvidenceStage.FINAL
    assert event.reason == "approved full run 2026-09-01"
    assert event.promoted_at  # timestamp recorded


def test_promotion_requires_reason() -> None:
    record = make_record(EvidenceStage.PRELIMINARY)
    with pytest.raises(ForbiddenPromotionError, match="reason"):
        promote(record, EvidenceStage.FINAL, reason="   ")


def test_synthetic_cannot_be_registered_as_preliminary_or_final() -> None:
    record = make_record(EvidenceStage.SYNTHETIC_TEST)
    with pytest.raises(ForbiddenPromotionError):
        promote(record, EvidenceStage.PRELIMINARY, reason="no")
    with pytest.raises(ForbiddenPromotionError):
        promote(record, EvidenceStage.FINAL, reason="no")


def test_engineering_pilot_auroc_cannot_become_a_research_finding() -> None:
    record = make_record(EvidenceStage.ENGINEERING_PILOT, metric="auroc")
    with pytest.raises(ForbiddenPromotionError):
        promote(record, EvidenceStage.FINAL, reason="looks good")


# ---------------------------------------------------------------------------
# Validation 2: stage survives JSON/CSV/Parquet serialization
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_records() -> list[ResultRecord]:
    return [make_record(stage, metric=f"metric_{stage.value.lower()}") for stage in ALL_STAGES]


def test_stage_survives_json_round_trip(sample_records: list[ResultRecord]) -> None:
    restored = records_from_json(records_to_json(sample_records))
    assert restored == sample_records
    assert [record.evidence_stage for record in restored] == ALL_STAGES


def test_stage_survives_csv_round_trip(sample_records: list[ResultRecord]) -> None:
    restored = records_from_csv(records_to_csv(sample_records))
    assert restored == sample_records
    assert [record.evidence_stage for record in restored] == ALL_STAGES


def test_stage_survives_parquet_round_trip(
    tmp_path: Path, sample_records: list[ResultRecord]
) -> None:
    path = records_to_parquet(sample_records, tmp_path / "results.parquet")
    restored = records_from_parquet(path)
    assert restored == sample_records
    assert [record.evidence_stage for record in restored] == ALL_STAGES


def test_serialized_label_is_the_plain_stage_string(sample_records: list[ResultRecord]) -> None:
    text = records_to_json(sample_records)
    for stage in ALL_STAGES:
        assert f'"evidence_stage": "{stage.value}"' in text
    csv_text = records_to_csv(sample_records)
    for stage in ALL_STAGES:
        assert stage.value in csv_text


# ---------------------------------------------------------------------------
# Record model strictness
# ---------------------------------------------------------------------------


def test_result_record_rejects_unknown_fields() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ResultRecord(
            metric_name="auroc",
            value=0.7,
            evidence_stage=EvidenceStage.FINAL,
            surprise="x",  # type: ignore[call-arg]
        )


def test_result_record_is_immutable() -> None:
    from pydantic import ValidationError

    record = make_record(EvidenceStage.PRELIMINARY)
    with pytest.raises(ValidationError):
        record.evidence_stage = EvidenceStage.FINAL  # type: ignore[misc]


def test_result_record_rejects_empty_metric_name() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ResultRecord(metric_name="  ", value=0.1, evidence_stage=EvidenceStage.FINAL)

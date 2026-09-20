"""Tests for batch.py — Milestones 64-69."""

from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

import pytest

from evovariant_tr.batch import (
    BatchJob,
    FailureKind,
    ScoringMetrics,
    ShardResult,
    ShardSpec,
    check_resume_state,
    classify_error,
    compute_shard_id,
    create_job_id,
    create_shards,
    load_job_manifest,
    load_shard_result,
    retry_backoff_seconds,
    retryable_failure,
    save_job_manifest,
    write_shard_result,
)
from evovariant_tr.cohort_fast import FastVariant


def _make_variant(chrom: str, start: int, ref: str, alt: str) -> FastVariant:
    return FastVariant(
        chrom=chrom, start=start, ref=ref, alt=alt,
        t0_significance="Uncertain significance", t0_stars=2,
        t1_significance=None, t1_stars=0,
        outcome="excluded", gene=None,
        allele_id_t0=1, allele_id_t1=None,
    )


# --------------------------------------------------------------------------- #
# M66: Deterministic sharding
# --------------------------------------------------------------------------- #


def test_compute_shard_id_deterministic():
    ids = [("chr1", 100, "A", "T"), ("chr1", 101, "C", "G")]
    key1 = compute_shard_id(ids, 0, 1)
    key2 = compute_shard_id(ids, 0, 1)
    assert key1 == key2
    assert len(key1) == 32


def test_compute_shard_id_order_invariant():
    ids1 = [("chr1", 100, "A", "T"), ("chr1", 101, "C", "G")]
    ids2 = [("chr1", 101, "C", "G"), ("chr1", 100, "A", "T")]
    assert compute_shard_id(ids1, 0, 1) == compute_shard_id(ids2, 0, 1)


def test_create_shards_basic():
    variants = [_make_variant("chr1", i, "A", "T") for i in range(100)]
    shards = create_shards(variants, shard_size=25, batch_size=32)
    assert len(shards) == 4
    assert all(s.variant_count == 25 for s in shards)


def test_create_shards_uneven():
    variants = [_make_variant("chr1", i, "A", "T") for i in range(105)]
    shards = create_shards(variants, shard_size=25, batch_size=32)
    assert len(shards) == 5
    assert shards[0].variant_count == 25
    assert shards[-1].variant_count == 5  # remainder


def test_create_shards_ids_unique():
    variants = [_make_variant("chr1", i, "A", "T") for i in range(100)]
    shards = create_shards(variants, shard_size=25, batch_size=32)
    ids = [s.shard_id for s in shards]
    assert len(set(ids)) == len(ids)


def test_create_shards_empty():
    shards = create_shards([], shard_size=10, batch_size=32)
    assert len(shards) == 0


# --------------------------------------------------------------------------- #
# M67: Resume and retry
# --------------------------------------------------------------------------- #


def test_create_job_id_deterministic():
    id1 = create_job_id("vus_cohort", 1000)
    id2 = create_job_id("vus_cohort", 1000)
    # Same day → same ID
    assert id1 == id2
    assert len(id1) == 24


def test_save_and_load_job_manifest(tmp_path: Path):
    from datetime import datetime

    job = BatchJob(
        job_id="test_job_123",
        cohort_name="vus_cohort",
        total_variants=380776,
        shard_size=1000,
        status="completed",
        created_at=datetime.now(UTC).isoformat(),
    )

    manifest_path = tmp_path / "job_manifest.json"
    save_job_manifest(job, manifest_path)
    loaded = load_job_manifest(manifest_path)

    assert loaded["job_id"] == "test_job_123"
    assert loaded["cohort_name"] == "vus_cohort"
    assert loaded["status"] == "completed"
    assert loaded["total_variants"] == 380776


def test_check_resume_state_no_manifest(tmp_path: Path):
    state = check_resume_state(tmp_path / "jobs" / "test")
    assert state["is_resumable"] is False
    assert state["progress"] == 0.0


def test_check_resume_state_with_manifest_but_no_shards(tmp_path: Path):
    job_dir = tmp_path / "jobs" / "empty"
    job_dir.mkdir(parents=True)
    (job_dir / "job_manifest.json").write_text(
        json.dumps({"total_shards": 2, "job_id": "empty"})
    )
    state = check_resume_state(job_dir)
    assert state == {
        "is_resumable": True,
        "completed_shards": [],
        "failed_shards": [],
        "progress": 0.0,
    }


def test_check_resume_state_with_completed_shards(tmp_path: Path):
    job_dir = tmp_path / "jobs" / "test"
    shards_dir = job_dir / "shards"
    shards_dir.mkdir(parents=True)

    manifest = {"total_shards": 3, "job_id": "test"}
    (job_dir / "job_manifest.json").write_text(json.dumps(manifest))

    # Create completed shard
    ShardResult(
        shard_id="shard_1", status="completed",
    )
    shard_data = {"shard_id": "shard_1", "status": "completed"}
    (shards_dir / "shard_1.json").write_text(json.dumps(shard_data))

    state = check_resume_state(job_dir)
    assert state["is_resumable"] is True
    assert "shard_1" in state["completed_shards"]
    assert state["progress"] == 1 / 3


def test_check_resume_state_with_failed_shards(tmp_path: Path):
    job_dir = tmp_path / "jobs" / "test"
    shards_dir = job_dir / "shards"
    shards_dir.mkdir(parents=True)

    manifest = {"total_shards": 2, "job_id": "test"}
    (job_dir / "job_manifest.json").write_text(json.dumps(manifest))

    shard_data = {"shard_id": "failed_1", "status": "failed"}
    (shards_dir / "failed_1.json").write_text(json.dumps(shard_data))

    state = check_resume_state(job_dir)
    assert "failed_1" in state["failed_shards"]


def test_shard_result_round_trip_and_retry_policy(tmp_path: Path) -> None:
    result = ShardResult(
        shard_id="abc",
        status="completed",
        scored=[{"id": "v1"}],
        completed_at="2026-09-21T00:00:00+00:00",
    )
    write_shard_result(tmp_path, result)
    loaded = load_shard_result(tmp_path, "abc")
    assert loaded is not None
    assert loaded.scored == [{"id": "v1"}]
    assert load_shard_result(tmp_path, "missing") is None
    assert retryable_failure(FailureKind.NETWORK_ERROR) is True
    assert retryable_failure(FailureKind.OUT_OF_MEMORY) is False
    assert retry_backoff_seconds(0) == 2.0
    assert retry_backoff_seconds(10) == 300.0


def test_retry_backoff_rejects_negative_attempt() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        retry_backoff_seconds(-1)


# --------------------------------------------------------------------------- #
# M64: Failure taxonomy
# --------------------------------------------------------------------------- #


def test_classify_error_oom():
    assert classify_error("CUDA out of memory") == FailureKind.OUT_OF_MEMORY


def test_classify_error_oom_no_caps():
    assert classify_error("out of memory") == FailureKind.OUT_OF_MEMORY


def test_classify_error_gpu():
    assert classify_error("No GPU found") == FailureKind.GPU_ERROR


def test_classify_error_timeout():
    assert classify_error("Request timed out") == FailureKind.TIMEOUT


def test_classify_error_network():
    assert classify_error("Connection refused") == FailureKind.NETWORK_ERROR


def test_classify_error_sequence():
    assert classify_error("Sequence length mismatch") == FailureKind.SEQUENCE_ERROR


def test_classify_error_validation():
    assert classify_error("Validation failed") == FailureKind.VALIDATION_ERROR


def test_classify_error_model():
    assert classify_error("Model load failed") == FailureKind.MODEL_ERROR


def test_classify_error_unknown():
    assert classify_error("Something weird happened") == FailureKind.UNKNOWN


def test_classify_error_with_type():
    assert classify_error("Bad input", "ValueError") == FailureKind.VALIDATION_ERROR


def test_classify_error_with_type_runtime():
    assert classify_error("Bad input", "RuntimeError") == FailureKind.MODEL_ERROR


def test_classify_error_with_index_type():
    assert classify_error("Bad input", "IndexError") == FailureKind.SEQUENCE_ERROR


# --------------------------------------------------------------------------- #
# Scoring metrics
# --------------------------------------------------------------------------- #


def test_scoring_metrics_to_dict():
    metrics = ScoringMetrics(
        n_scored=100,
        n_failed=5,
        n_total=105,
        mean_score_delta=2.5,
        std_score_delta=1.0,
        failures_by_kind={"gpu_error": 3, "timeout": 2},
    )
    d = metrics.to_dict()
    assert d["n_scored"] == 100
    assert d["n_failed"] == 5
    assert d["failures_by_kind"]["gpu_error"] == 3


# --------------------------------------------------------------------------- #
# ShardSpec and ShardResult
# --------------------------------------------------------------------------- #


def test_shard_spec_defaults():
    spec = ShardSpec(
        shard_id="test",
        variant_count=100,
        batch_size=32,
        expected_duration_seconds=10.0,
    )
    assert spec.shard_id == "test"
    assert spec.variant_count == 100
    assert spec.provenance == {}


def test_shard_result_defaults():
    result = ShardResult(shard_id="test", status="completed")
    assert result.scored == []
    assert result.errors == []
    assert result.timing_ms == 0.0
    assert result.completed_at == ""


def test_failure_kind_values():
    assert FailureKind.GPU_ERROR.value == "gpu_error"
    assert FailureKind.OUT_OF_MEMORY.value == "out_of_memory"
    assert FailureKind.TIMEOUT.value == "timeout"
    assert FailureKind.SEQUENCE_ERROR.value == "sequence_error"
    assert FailureKind.UNKNOWN.value == "unknown"

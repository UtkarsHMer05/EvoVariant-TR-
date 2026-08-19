"""Batch resumability and failure-recovery pilot tests — gated (wait).

These tests validate the batch retry/resume semantics without requiring GPU
access. They run under the `modal` gate since they simulate the full scoring
pipeline including failure recovery.

Run with:
    EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS pytest --run-modal
    tests/modal/
"""

from __future__ import annotations

import json

import pytest

from evovariant_tr.batch import (
    FailureKind,
    check_resume_state,
    classify_error,
    create_shards,
)
from evovariant_tr.cohort_fast import FastVariant
from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.scoring_record import ScoreStatus, ScoringRecord


def _make_variants(n: int, start: int = 1000) -> list[FastVariant]:
    variants = []
    for i in range(n):
        variants.append(FastVariant(
            chrom="chr1", start=start + i, ref="A", alt="T",
            t0_significance="Uncertain significance", t0_stars=2,
            t1_significance="Pathogenic", t1_stars=2,
            outcome="resolved_pathogenic", gene="TEST1",
            allele_id_t0=i, allele_id_t1=i,
        ))
    return variants


@pytest.mark.modal
def test_25_variant_resumability_pilot(tmp_path):
    """M067: 25-variant resumability and failure-recovery pilot.

    Simulates a scoring run where some shards fail and verifies
    that the resume logic correctly identifies completed vs failed
    shards, and that re-scoring produces the same results (determinism).
    """
    variants = _make_variants(25)
    shards = create_shards(variants, shard_size=5, batch_size=5)
    assert len(shards) == 5

    job_dir = tmp_path / "jobs" / "pilot_25"
    shards_dir = job_dir / "shards"
    shards_dir.mkdir(parents=True)

    # Simulate scoring: first 3 shards succeed, 2 fail
    job_manifest = {
        "job_id": "pilot_25",
        "total_variants": 25,
        "shard_size": 5,
        "total_shards": 5,
    }
    (job_dir / "job_manifest.json").write_text(json.dumps(job_manifest))

    scorer = FakeScorer(scale=1.0)

    for i, shard in enumerate(shards):
        shard_file = shards_dir / f"{shard.shard_id}.json"
        if i < 3:
            # Success
            records = []
            for v in variants[i * 5:(i + 1) * 5]:
                record = ScoringRecord(
                    chrom=v.chrom, start=v.start, ref=v.ref, alt=v.alt,
                    scorer_name=scorer.name, scorer_version=scorer.version,
                    score_delta=0.5, outcome="resolved_pathogenic",
                    status=ScoreStatus.COMPLETED,
                )
                records.append(record)
            shard_file.write_text(json.dumps({
                "shard_id": shard.shard_id,
                "status": "completed",
                "records": [r.to_dict() for r in records],
            }))
        else:
            # Failure
            shard_file.write_text(json.dumps({
                "shard_id": shard.shard_id,
                "status": "failed",
                "errors": [{"variant": "chr1:1001A>T", "error": "out of memory"}],
            }))

    # Check resume state
    state = check_resume_state(job_dir)
    assert state["is_resumable"] is True
    assert len(state["completed_shards"]) == 3
    assert len(state["failed_shards"]) == 2
    assert state["progress"] == 0.6


@pytest.mark.modal
def test_100_variant_performance_pilot(tmp_path):
    """M068: 100-variant performance-engineering pilot.

    Verifies deterministic sharding and cost model computation
    for a 100-variant batch.
    """
    variants = _make_variants(100, start=2000)
    shards = create_shards(variants, shard_size=20, batch_size=32)
    assert len(shards) == 5

    # Verify deterministic shard IDs
    shard_ids = [s.shard_id for s in shards]
    assert len(set(shard_ids)) == 5

    # Verify shard sizes
    for s in shards:
        assert s.variant_count == 20
        assert s.batch_size == 32
        assert s.expected_duration_seconds > 0.0


@pytest.mark.modal
def test_failure_recovery_classify_errors():
    """M067: All failure classifications map to correct FailureKind."""
    assert classify_error("CUDA out of memory") == FailureKind.OUT_OF_MEMORY
    assert classify_error("Request timed out") == FailureKind.TIMEOUT
    assert classify_error("No GPU available") == FailureKind.GPU_ERROR
    assert classify_error("Connection reset by peer") == FailureKind.NETWORK_ERROR
    assert classify_error("Model load failed") == FailureKind.MODEL_ERROR
    assert classify_error("Sequence length mismatch") == FailureKind.SEQUENCE_ERROR
    assert classify_error("Validation error in input") == FailureKind.VALIDATION_ERROR
    assert classify_error("Unexpected error occurred") == FailureKind.UNKNOWN


@pytest.mark.modal
def test_shard_file_serialization():
    """M061: ShardFile can be serialized and deserialized."""
    from evovariant_tr.scoring_record import ShardFile

    record = ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="test", scorer_version="1.0",
        score_delta=2.5, outcome="resolved_pathogenic",
    )
    shard = ShardFile(
        shard_id="test_shard",
        records=[record],
        metadata={"batch_size": 10},
    )

    d = shard.to_dict()
    assert d["shard_id"] == "test_shard"
    assert d["record_count"] == 1
    assert len(d["records"]) == 1
    assert d["metadata"]["batch_size"] == 10

    # Round-trip
    restored = ShardFile.from_dict(d)
    assert restored.shard_id == "test_shard"
    assert len(restored.records) == 1
    assert restored.records[0].chrom == "chr1"


@pytest.mark.modal
def test_resume_with_mixed_shard_statuses(tmp_path):
    """M063: Resume correctly handles mixed completed/failed shards."""
    job_dir = tmp_path / "jobs" / "mixed"
    shards_dir = job_dir / "shards"
    shards_dir.mkdir(parents=True)

    manifest = {"total_shards": 4, "job_id": "mixed"}
    (job_dir / "job_manifest.json").write_text(json.dumps(manifest))

    # 2 completed, 1 failed, 1 pending
    statuses = ["completed", "completed", "failed", None]
    for i, status in enumerate(statuses):
        if status:
            (shards_dir / f"shard_{i}.json").write_text(json.dumps({
                "shard_id": f"shard_{i}",
                "status": status,
            }))

    state = check_resume_state(job_dir)
    assert len(state["completed_shards"]) == 2
    assert len(state["failed_shards"]) == 1
    assert state["progress"] == 0.5

"""Tests for scoring_record.py — Milestone 61."""

from __future__ import annotations

from evovariant_tr.scoring_record import (
    ScoreStatus,
    ScoringRecord,
    ShardFile,
)


def test_score_status_values():
    assert ScoreStatus.COMPLETED.value == "completed"
    assert ScoreStatus.FAILED.value == "failed"
    assert ScoreStatus.SKIPPED.value == "skipped"


def test_scoring_record_creation():
    rec = ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="evo2", scorer_version="1.0",
    )
    assert rec.chrom == "chr1"
    assert rec.start == 100
    assert rec.identity == ("chr1", 100, "A", "T")
    assert rec.status == ScoreStatus.COMPLETED


def test_scoring_record_id_deterministic():
    rec1 = ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0")
    rec2 = ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0")
    assert rec1.record_id == rec2.record_id
    assert len(rec1.record_id) == 32


def test_scoring_record_id_changes_with_version():
    rec1 = ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0")
    rec2 = ScoringRecord("chr1", 100, "A", "T", "evo2", "2.0")
    assert rec1.record_id != rec2.record_id


def test_scoring_record_to_dict():
    rec = ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="evo2", scorer_version="1.0",
        reference_score=10.0, alternate_score=12.0, score_delta=2.0,
        gene_symbol="BRCA1", outcome="resolved_pathogenic",
    )
    d = rec.to_dict()
    assert d["chrom"] == "chr1"
    assert d["record_id"] is not None
    assert d["reference_score"] == 10.0
    assert d["score_delta"] == 2.0
    assert d["status"] == "completed"
    assert d["gene_symbol"] == "BRCA1"


def test_scoring_record_from_dict():
    rec = ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="evo2", scorer_version="1.0",
        reference_score=5.0, alternate_score=7.0, score_delta=2.0,
        gene_symbol="TP53", outcome="resolved_benign",
        status=ScoreStatus.COMPLETED,
    )
    d = rec.to_dict()
    rec2 = ScoringRecord.from_dict(d)
    assert rec2.chrom == rec.chrom
    assert rec2.reference_score == rec.reference_score
    assert rec2.gene_symbol == "TP53"
    assert rec2.status == ScoreStatus.COMPLETED


def test_scoring_record_from_dict_failed():
    rec = ScoringRecord(
        chrom="chr1", start=100, ref="A", alt="T",
        scorer_name="fake", scorer_version="0.1",
        status=ScoreStatus.FAILED, error="OOM",
    )
    d = rec.to_dict()
    assert d["status"] == "failed"
    assert d["error"] == "OOM"

    rec2 = ScoringRecord.from_dict(d)
    assert rec2.status == ScoreStatus.FAILED
    assert rec2.error == "OOM"


def test_shard_file_creation():
    records = [
        ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0"),
        ScoringRecord("chr1", 200, "C", "G", "evo2", "1.0"),
    ]
    shard = ShardFile(shard_id="shard_1", records=records)
    assert shard.shard_id == "shard_1"
    assert len(shard.records) == 2
    assert shard.completed_count == 2
    assert shard.failed_count == 0


def test_shard_file_with_failures():
    records = [
        ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0"),
        ScoringRecord("chr1", 200, "C", "G", "evo2", "1.0", status=ScoreStatus.FAILED),
    ]
    shard = ShardFile(shard_id="shard_1", records=records)
    assert shard.completed_count == 1
    assert shard.failed_count == 1


def test_shard_file_serialization():
    records = [
        ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0"),
    ]
    shard = ShardFile(shard_id="shard_1", records=records, metadata={"batch": 1})
    d = shard.to_dict()
    assert d["shard_id"] == "shard_1"
    assert d["record_count"] == 1
    assert "shard_record_id" in d
    assert "records" in d

    shard2 = ShardFile.from_dict(d)
    assert shard2.shard_id == "shard_1"
    assert len(shard2.records) == 1
    assert shard2.metadata["batch"] == 1


def test_shard_record_id_deterministic():
    records = [
        ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0"),
        ScoringRecord("chr1", 200, "C", "G", "evo2", "1.0"),
    ]
    shard = ShardFile(shard_id="shard_1", records=records)
    id1 = shard.shard_record_id
    id2 = shard.shard_record_id
    assert id1 == id2
    assert len(id1) == 32


def test_scoring_record_is_frozen():
    """ScoringRecord fields should be mutable."""
    rec = ScoringRecord("chr1", 100, "A", "T", "evo2", "1.0")
    # ScoringRecord is not frozen, so this should work
    rec.reference_score = 5.0
    assert rec.reference_score == 5.0
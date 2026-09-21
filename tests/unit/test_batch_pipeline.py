"""CPU-only tests for the Phase 15 batch input and resume contract."""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

import pytest

from evovariant_tr.batch_pipeline import (
    BatchVariant,
    build_batch_plan,
    estimate_batch_cost_usd,
    execute_batch,
    export_batch_results,
    parse_variant_input,
    parse_variant_vcf,
    sha256_file,
    write_batch_plan,
)


def _csv(path: Path, rows: str) -> Path:
    path.write_text(
        "assembly,chromosome,position_1based,reference,alternate\n" + rows,
        encoding="utf-8",
    )
    return path


def _variants() -> list[BatchVariant]:
    return [
        BatchVariant("GRCh38", "chr1", 10, "A", "T", "GRCh38:chr1:10:A>T", 2),
        BatchVariant("GRCh38", "chr2", 20, "C", "G", "GRCh38:chr2:20:C>G", 3),
        BatchVariant("GRCh38", "chrX", 30, "G", "A", "GRCh38:chrX:30:G>A", 4),
    ]


def _plan(variants: list[BatchVariant], *, shard_size: int = 2):
    return build_batch_plan(
        variants,
        input_sha256="a" * 64,
        input_format="csv",
        shard_size=shard_size,
        batch_size=2,
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision="b" * 40,
        context_length_bp=8192,
        orientation="both",
        seconds_per_variant=2.0,
        gpu_usd_per_hour=3.95,
        fixed_seconds=10.0,
    )


def _scorer(rows: list[BatchVariant]):
    return [
        {
            "normalized_variant_id": row.normalized_variant_id,
            "delta_forward": float(index),
        }
        for index, row in enumerate(rows)
    ]


def test_csv_and_vcf_inputs_share_canonical_identity(tmp_path: Path) -> None:
    csv_path = _csv(tmp_path / "variants.csv", "GRCh38,1,10,A,T\n")
    parsed_csv = parse_variant_input(csv_path)
    assert parsed_csv[0].chromosome == "chr1"
    assert parsed_csv[0].normalized_variant_id == "GRCh38:chr1:10:A>T"
    assert parsed_csv[0].canonical().is_snv

    vcf_text = "##fileformat=VCFv4.3\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    vcf_path = tmp_path / "variants.vcf"
    vcf_path.write_text(vcf_text + "1\t10\t.\tA\tT\t.\tPASS\t.\n", encoding="utf-8")
    assert parse_variant_vcf(vcf_path)[0].canonical() == parsed_csv[0].canonical()

    gz_path = tmp_path / "variants.vcf.gz"
    with gzip.open(gz_path, "wt", encoding="utf-8") as handle:
        handle.write(vcf_text + "chr2\t20\t.\tC\tG\t.\tPASS\t.\n")
    assert parse_variant_input(gz_path)[0].normalized_variant_id == "GRCh38:chr2:20:C>G"


def test_input_parser_rejects_malformed_or_ambiguous_records(tmp_path: Path) -> None:
    bad_assembly = _csv(tmp_path / "bad-assembly.csv", "GRCh37,1,10,A,T\n")
    with pytest.raises(ValueError, match="GRCh38"):
        parse_variant_input(bad_assembly)

    empty_row = _csv(tmp_path / "empty.csv", ",,,,\n")
    with pytest.raises(ValueError, match="empty"):
        parse_variant_input(empty_row)

    no_header = tmp_path / "no-header.vcf"
    no_header.write_text("1\t10\t.\tA\tT\n", encoding="utf-8")
    with pytest.raises(ValueError, match="#CHROM"):
        parse_variant_vcf(no_header)

    multi = tmp_path / "multi.vcf"
    multi.write_text(
        "#CHROM\tPOS\tID\tREF\tALT\n1\t10\t.\tA\tT,G\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="multiallelic"):
        parse_variant_vcf(multi)

    with pytest.raises(ValueError, match="input_format"):
        parse_variant_input(no_header, input_format="bed")

    short_vcf = tmp_path / "short.vcf"
    short_vcf.write_text("#CHROM\tPOS\tID\tREF\tALT\n1\t10\t.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fewer than five"):
        parse_variant_vcf(short_vcf)

    header_only = tmp_path / "header-only.vcf"
    header_only.write_text("#CHROM\tPOS\tID\tREF\tALT\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no variant rows"):
        parse_variant_vcf(header_only)

    for filename, row, message in (
        ("missing-position.csv", "GRCh38,1,nope,A,T\n", "invalid position"),
        ("empty-chromosome.csv", "GRCh38,,10,A,T\n", "empty chromosome"),
        ("chr-only.csv", "GRCh38,chr,10,A,T\n", "invalid chromosome"),
        ("indel.csv", "GRCh38,1,10,AA,T\n", "biallelic SNV"),
        ("ambiguous.csv", "GRCh38,1,10,N,T\n", "non-ACGT"),
        ("same.csv", "GRCh38,1,10,A,A\n", "identical"),
    ):
        malformed = _csv(tmp_path / filename, row)
        with pytest.raises(ValueError, match=message):
            parse_variant_input(malformed)


def test_plan_cost_and_atomic_serialization(tmp_path: Path) -> None:
    variants = _variants()
    plan = _plan(variants)
    same = _plan(variants)
    assert plan.job_id == same.job_id
    assert plan.total_variants == 3
    assert plan.total_shards == 2
    assert plan.estimated_seconds == 16.0
    assert plan.estimated_cost_usd == pytest.approx(16.0 / 3600.0 * 3.95)

    plan_path = write_batch_plan(plan, tmp_path / "job" / "batch_plan.json")
    loaded = json.loads(plan_path.read_text(encoding="utf-8"))
    assert loaded["variant_ids"] == [variant.normalized_variant_id for variant in variants]
    assert not list(plan_path.parent.glob("*.tmp"))
    assert sha256_file(plan_path) == sha256_file(plan_path)
    assert estimate_batch_cost_usd(
        total_variants=0,
        seconds_per_variant=1.0,
        gpu_usd_per_hour=1.0,
    ) == 0.0

    with pytest.raises(ValueError, match="positive"):
        estimate_batch_cost_usd(
            total_variants=1,
            seconds_per_variant=1.0,
            gpu_usd_per_hour=0.0,
        )
    with pytest.raises(ValueError, match="non-negative"):
        estimate_batch_cost_usd(
            total_variants=-1,
            seconds_per_variant=1.0,
            gpu_usd_per_hour=1.0,
        )
    with pytest.raises(ValueError, match="finite"):
        estimate_batch_cost_usd(
            total_variants=1,
            seconds_per_variant=math.nan,
            gpu_usd_per_hour=1.0,
        )
    for kwargs, message in (
        ({"shard_size": 0}, "positive"),
        ({"context_length_bp": 0}, "positive"),
        ({"model_id": ""}, "non-empty"),
        ({"input_format": "bed"}, "csv or vcf"),
        ({"input_sha256": "0"}, "lowercase SHA"),
    ):
        values = {
            "input_sha256": "a" * 64,
            "input_format": "csv",
            "shard_size": 1,
            "batch_size": 1,
            "model_id": "evo2",
            "checkpoint": "evo2_7b",
            "model_revision": "b" * 40,
            "context_length_bp": 8192,
            "orientation": "both",
        }
        values.update(kwargs)
        with pytest.raises(ValueError, match=message):
            build_batch_plan(variants, **values)
    duplicate_plan_rows = variants + [variants[0]]
    with pytest.raises(ValueError, match="duplicate"):
        build_batch_plan(
            duplicate_plan_rows,
            input_sha256="a" * 64,
            input_format="csv",
            shard_size=1,
            batch_size=1,
            model_id="evo2",
            checkpoint="evo2_7b",
            model_revision="b" * 40,
            context_length_bp=8192,
            orientation="both",
        )
    with pytest.raises(ValueError, match="both"):
        build_batch_plan(
            variants,
            input_sha256="a" * 64,
            input_format="csv",
            shard_size=1,
            batch_size=1,
            model_id="evo2",
            checkpoint="evo2_7b",
            model_revision="b" * 40,
            context_length_bp=8192,
            orientation="both",
            seconds_per_variant=1.0,
        )


def test_execute_resume_and_export_preserve_order(tmp_path: Path) -> None:
    variants = _variants()
    plan = _plan(variants)
    calls: list[tuple[str, ...]] = []

    def scorer(rows: list[BatchVariant]):
        calls.append(tuple(row.normalized_variant_id for row in rows))
        return _scorer(rows)

    output_dir = tmp_path / "job"
    first = execute_batch(variants, plan=plan, output_dir=output_dir, scorer=scorer)
    assert first["status"] == "COMPLETED"
    assert first["completed_variants"] == 3
    assert first["reused_shards"] == 0
    assert len(calls) == 2

    second = execute_batch(variants, plan=plan, output_dir=output_dir, scorer=scorer)
    assert second["status"] == "COMPLETED"
    assert second["reused_shards"] == 2
    assert len(calls) == 2

    exported = export_batch_results(output_dir, tmp_path / "exports" / "results.jsonl")
    assert exported["status"] == "COMPLETED"
    assert exported["exported_rows"] == 3
    result_ids = [
        json.loads(line)["normalized_variant_id"]
        for line in (tmp_path / "exports" / "results.jsonl").read_text().splitlines()
    ]
    assert result_ids == list(plan.variant_ids)


def test_execute_persists_failure_then_retries_and_rejects_labels(tmp_path: Path) -> None:
    variants = _variants()
    plan = _plan(variants)
    output_dir = tmp_path / "recover"
    failed_once = {plan.variant_ids[2]}

    def flaky(rows: list[BatchVariant]):
        if any(row.normalized_variant_id in failed_once for row in rows):
            raise RuntimeError("network timeout")
        return _scorer(rows)

    partial = execute_batch(variants, plan=plan, output_dir=output_dir, scorer=flaky)
    assert partial["status"] == "PARTIAL"
    assert partial["failed_variants"] == 1
    still_partial = execute_batch(variants, plan=plan, output_dir=output_dir, scorer=flaky)
    assert still_partial["status"] == "PARTIAL"
    assert still_partial["failed_shards"] == 1
    partial_export = export_batch_results(output_dir, tmp_path / "partial.jsonl")
    assert partial_export["missing_rows"] == 1

    failed_once.clear()
    recovered = execute_batch(
        variants,
        plan=plan,
        output_dir=output_dir,
        scorer=flaky,
        retry_failed=True,
    )
    assert recovered["status"] == "COMPLETED"
    assert recovered["reused_shards"] == 1

    def returns_labels(rows: list[BatchVariant]):
        return [
            {"normalized_variant_id": row.normalized_variant_id, "outcome": "pathogenic"}
            for row in rows
        ]

    label_dir = tmp_path / "labels"
    label_result = execute_batch(
        variants,
        plan=plan,
        output_dir=label_dir,
        scorer=returns_labels,
    )
    assert label_result["status"] == "FAILED"
    assert label_result["failed_variants"] == 3


def test_execute_fails_closed_for_plan_mismatch_and_bad_scorer(tmp_path: Path) -> None:
    variants = _variants()
    plan = _plan(variants)
    with pytest.raises(ValueError, match="do not match"):
        execute_batch(variants[:2], plan=plan, output_dir=tmp_path / "mismatch", scorer=_scorer)

    def wrong_order(rows: list[BatchVariant]):
        return [
            {"normalized_variant_id": "GRCh38:chrM:999:A>C"}
            for _ in rows
        ]

    result = execute_batch(
        variants,
        plan=plan,
        output_dir=tmp_path / "wrong-order",
        scorer=wrong_order,
    )
    assert result["status"] == "FAILED"
    assert result["failed_shards"] == 2

    empty_plan = build_batch_plan(
        [],
        input_sha256="c" * 64,
        input_format="csv",
        shard_size=2,
        batch_size=1,
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision="b" * 40,
        context_length_bp=8192,
        orientation="both",
    )
    empty = execute_batch([], plan=empty_plan, output_dir=tmp_path / "empty", scorer=_scorer)
    assert empty["status"] == "COMPLETED"
    assert empty["total_shards"] == 0


def test_execute_reprocesses_corrupt_shards_and_validates_scorer_shapes(tmp_path: Path) -> None:
    variants = _variants()
    plan = _plan(variants)
    output_dir = tmp_path / "corrupt"
    execute_batch(variants, plan=plan, output_dir=output_dir, scorer=_scorer)
    first_shard = sorted((output_dir / "shards").glob("*.json"))[0]
    first_shard.write_text("not-json\n", encoding="utf-8")
    rerun = execute_batch(variants, plan=plan, output_dir=output_dir, scorer=_scorer)
    assert rerun["status"] == "COMPLETED"
    assert rerun["reused_shards"] == 1

    def wrong_count(rows: list[BatchVariant]):
        return _scorer(rows[:-1])

    count_result = execute_batch(
        variants,
        plan=plan,
        output_dir=tmp_path / "wrong-count",
        scorer=wrong_count,
    )
    assert count_result["status"] == "FAILED"

    def non_object(rows: list[BatchVariant]):
        return [None for _ in rows]

    object_result = execute_batch(
        variants,
        plan=plan,
        output_dir=tmp_path / "non-object",
        scorer=non_object,
    )
    assert object_result["status"] == "FAILED"

    duplicate_export = tmp_path / "duplicate-export"
    execute_batch(variants, plan=plan, output_dir=duplicate_export, scorer=_scorer)
    shard_files = sorted((duplicate_export / "shards").glob("*.json"))
    second = json.loads(shard_files[1].read_text(encoding="utf-8"))
    first = json.loads(shard_files[0].read_text(encoding="utf-8"))
    second["payload"]["rows"] = first["payload"]["rows"]
    shard_files[1].write_text(json.dumps(second), encoding="utf-8")
    with pytest.raises(ValueError, match="tampered|invalid"):
        export_batch_results(duplicate_export, tmp_path / "duplicate.jsonl")

    unexpected_export = tmp_path / "unexpected-export"
    execute_batch(variants, plan=plan, output_dir=unexpected_export, scorer=_scorer)
    unexpected = unexpected_export / "shards" / "unexpected.json"
    unexpected.write_text(json.dumps({"payload": {"status": "completed"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        export_batch_results(unexpected_export, tmp_path / "unexpected.jsonl")

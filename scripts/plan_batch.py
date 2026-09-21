#!/usr/bin/env python3
"""Create a validated, immutable Phase 15 batch plan without scoring variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evovariant_tr.batch_pipeline import (
    build_batch_plan,
    parse_variant_input,
    sha256_file,
    write_batch_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--format", choices=("csv", "vcf"), default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-id", default="evo2")
    parser.add_argument("--checkpoint", default="evo2_7b")
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--context-length-bp", type=int, default=8192)
    parser.add_argument("--orientation", choices=("forward", "reverse", "both"), default="both")
    parser.add_argument("--shard-size", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seconds-per-variant", type=float, default=None)
    parser.add_argument("--gpu-usd-per-hour", type=float, default=None)
    parser.add_argument("--fixed-seconds", type=float, default=0.0)
    args = parser.parse_args(argv)

    variants = parse_variant_input(args.input, input_format=args.format)
    input_format = args.format
    if input_format is None:
        input_format = "vcf" if args.input.name.lower().endswith((".vcf", ".vcf.gz")) else "csv"
    plan = build_batch_plan(
        variants,
        input_sha256=sha256_file(args.input),
        input_format=input_format,
        shard_size=args.shard_size,
        batch_size=args.batch_size,
        model_id=args.model_id,
        checkpoint=args.checkpoint,
        model_revision=args.model_revision,
        context_length_bp=args.context_length_bp,
        orientation=args.orientation,
        seconds_per_variant=args.seconds_per_variant,
        gpu_usd_per_hour=args.gpu_usd_per_hour,
        fixed_seconds=args.fixed_seconds,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = write_batch_plan(plan, args.output_dir / "batch_plan.json")
    summary = {
        "status": "PLANNED",
        "scientific_outputs_created": False,
        "job_id": plan.job_id,
        "input": str(args.input),
        "input_sha256": plan.input_sha256,
        "input_format": plan.input_format,
        "total_variants": plan.total_variants,
        "total_shards": plan.total_shards,
        "estimated_seconds": plan.estimated_seconds,
        "estimated_cost_usd": plan.estimated_cost_usd,
        "plan_path": str(plan_path),
        "notes": "Planning and validation only; no scorer or remote endpoint was invoked.",
    }
    (args.output_dir / "planning_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run an explicitly approved Phase 6 or Phase 7 cohort execution.

This command has no implicit endpoint, no implicit approval, and no default
paid-compute acknowledgement.  It is intentionally unusable until the caller
supplies a current approval artifact, the exact scope token(s), and an explicit
Modal endpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr.cost_policy import load_current_ml_protocol_hash
from evovariant_tr.phase_execution import (
    JsonEndpointClient,
    PhaseExecutionError,
    build_execution_plan,
    execute_cohort,
    load_cohort_records,
    require_current_paid_approval,
    sha256_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Approval-gated, resumable EvoVariant-TR Phase 6/7 execution."
    )
    parser.add_argument("--phase", type=int, choices=(6, 7), required=True)
    parser.add_argument("--family", required=True, help="ZS or REP")
    parser.add_argument("--endpoint-kind", choices=("score", "embedding"), required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--split",
        action="append",
        required=True,
        choices=("TRAIN", "VALIDATION", "LOCKED_TEST"),
        help="Repeat for every split to execute; labels never cross the endpoint boundary.",
    )
    parser.add_argument("--split-manifest", type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--approval",
        type=Path,
        default=Path("artifacts/approvals/full_run_approval.json"),
    )
    parser.add_argument(
        "--scope-token",
        action="append",
        required=True,
        help="Every token must occur in the current approval run_scope.",
    )
    parser.add_argument("--shard-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--embedding-layer")
    parser.add_argument(
        "--include-labels",
        action="store_true",
        help="Explicitly copy local labels into the output; labels are never sent remotely.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.endpoint_kind == "embedding" and not args.embedding_layer:
            raise PhaseExecutionError(
                "--embedding-layer is required for an embedding execution"
            )
        if args.endpoint_kind == "score" and args.embedding_layer:
            raise PhaseExecutionError(
                "--embedding-layer is only valid for an embedding execution"
            )

        protocol_hash = load_current_ml_protocol_hash()
        approval = require_current_paid_approval(
            args.approval,
            scope_tokens=args.scope_token,
        )
        records, cohort_hash = load_cohort_records(args.manifest, splits=args.split)
        split_hash = sha256_file(args.split_manifest) if args.split_manifest else None
        plan = build_execution_plan(
            records,
            phase=args.phase,
            family=args.family,
            endpoint_kind=args.endpoint_kind,
            model_id=args.model_id,
            checkpoint=args.checkpoint,
            model_revision=args.model_revision,
            protocol_hash=protocol_hash,
            cohort_manifest_sha256=cohort_hash,
            split_manifest_sha256=split_hash,
            shard_size=args.shard_size,
            batch_size=args.batch_size,
            include_labels_in_output=args.include_labels,
            embedding_layer=args.embedding_layer,
        )
        summary = execute_cohort(
            records,
            plan=plan,
            output_dir=args.output_dir,
            endpoint=JsonEndpointClient(args.endpoint),
            embedding_layer=args.embedding_layer,
        )
        print(
            json.dumps(
                {
                    "status": summary["status"],
                    "summary": summary,
                    "approval_budget_usd": approval.max_budget_usd,
                    "approval_gpu": approval.gpu_type,
                    "protocol_hash": protocol_hash,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except PhaseExecutionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

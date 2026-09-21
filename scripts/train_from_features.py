#!/usr/bin/env python3
"""Run local Phase 8 baselines from a verified development feature artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr.downstream_pipeline import DownstreamPipelineError, run_baseline_training


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train CPU baselines from verified TRAIN/VALIDATION feature JSONL."
    )
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-id")
    parser.add_argument("--layer")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mlp-epochs", type=int, default=100)
    args = parser.parse_args(argv)
    try:
        summary = run_baseline_training(
            args.features,
            args.output_dir,
            model_id=args.model_id,
            layer=args.layer,
            seed=args.seed,
            mlp_epochs=args.mlp_epochs,
        )
    except (DownstreamPipelineError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

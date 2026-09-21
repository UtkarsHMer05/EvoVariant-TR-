#!/usr/bin/env python3
"""Run bounded, validation-only logistic HPO from a verified feature artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr.downstream_pipeline import (
    DownstreamPipelineError,
    load_hpo_configs,
    run_logistic_hpo_from_features,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run validation-only logistic HPO without reading locked-test labels."
    )
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-id")
    parser.add_argument("--layer")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    try:
        study = run_logistic_hpo_from_features(
            args.features,
            args.output_dir,
            load_hpo_configs(args.configs),
            model_id=args.model_id,
            layer=args.layer,
            seed=args.seed,
        )
    except (DownstreamPipelineError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(study.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

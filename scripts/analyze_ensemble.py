#!/usr/bin/env python3
"""Run validation-only ensemble/calibration/abstention analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr.analysis_pipeline import (
    AnalysisPipelineError,
    analyze_validation_ensemble,
    load_prediction_rows,
    write_analysis_artifact,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze two prediction models on VALIDATION only."
    )
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--left-model", required=True)
    parser.add_argument("--right-model", required=True)
    parser.add_argument("--left-weight", type=float, default=0.5)
    parser.add_argument("--right-weight", type=float, default=0.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        artifact = analyze_validation_ensemble(
            load_prediction_rows(args.predictions),
            left_model=args.left_model,
            right_model=args.right_model,
            weights=(args.left_weight, args.right_weight),
        )
        write_analysis_artifact(args.output, artifact)
    except (AnalysisPipelineError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

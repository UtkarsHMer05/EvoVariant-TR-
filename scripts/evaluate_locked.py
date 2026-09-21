#!/usr/bin/env python3
"""Run the final locked-test evaluator after configuration freeze."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr.final_evaluation import (
    FinalEvaluationError,
    evaluate_locked_once,
    load_frozen_config,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate one frozen model/configuration on LOCKED_TEST exactly once."
    )
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        artifact = evaluate_locked_once(
            args.predictions,
            args.output,
            model_id=args.model_id,
            frozen_config=load_frozen_config(args.config),
            expected_config_sha256=args.config_sha256,
        )
    except (FinalEvaluationError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Record the no-spend Phase 15 parity boundary and planning estimate."""

# ruff: noqa: E501

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from evovariant_tr.registry import hash_file

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/runs/phase15_batch_status.json"


def main() -> int:
    phase14_path = ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json"
    phase14 = json.loads(phase14_path.read_text(encoding="utf-8"))
    phase14_cost = float(phase14["cost"]["estimated_run_cost_usd"])
    phase14_rows = int(phase14["submission"]["submitted_rows"])
    phase14_runtime = float(phase14["runtime"]["remote_runtime_seconds"])
    smoke_rows = 64
    payload = {
        "phase": 15,
        "family": "BATCH",
        "status": "BLOCKED_NEW_PAID_AUTHORIZATION_REQUIRED",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "no_remote_compute": True,
        "local_contract": {
            "label_free_plan_and_atomic_shard_resume": "PASS",
            "evidence": "tests/unit/test_batch_pipeline.py::test_execute_resumes_after_process_interruption",
            "full_cohort_remote_parity": "NOT_RUN",
        },
        "minimum_future_development_smoke": {
            "rows": smoke_rows,
            "model": "Evo2 7B",
            "revision": phase14["model_contract"]["revision"],
            "assembly": "GRCh38",
            "context_length_bp": 8192,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "labels_remote_transport": False,
            "locked_test_rows": 0,
            "planned_remote_calls": 1,
            "estimated_remote_seconds": round(phase14_runtime * smoke_rows / phase14_rows, 6),
            "estimated_direct_h100_cost_usd": round(phase14_cost * smoke_rows / phase14_rows, 9),
            "estimate_basis": (
                f"{smoke_rows} rows x Phase 14 direct estimate ${phase14_cost:.9f} "
                f"/ {phase14_rows} rows; excludes startup, retry, and provider-meter uncertainty"
            ),
        },
        "full_cohort_parity_target": {
            "rows": 4000,
            "purpose": "development-only batch planner/parity validation",
            "status": "NOT_AUTHORIZED",
            "locked_test_rows": 0,
        },
        "authorization": {
            "hard_cap_usd": None,
            "safety_stop_usd": None,
            "required_action": "Obtain a fresh exact-scope paid approval before any Modal invocation.",
        },
        "source_artifacts": [
            {
                "path": str(phase14_path.relative_to(ROOT)),
                "sha256": hash_file(phase14_path),
            }
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUTPUT), "smoke_rows": smoke_rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

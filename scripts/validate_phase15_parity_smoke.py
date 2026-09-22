#!/usr/bin/env python3
"""Materialize the Phase 15 parity, cache, and restart acceptance audit."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from validate_phase15_parity_smoke_approval import validate_approval

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "artifacts/phase15/phase15_parity_smoke_20260922.json"
INITIAL = ROOT / "artifacts/phase15/phase15_parity_smoke_20260922_initial.json"
CANONICAL = ROOT / "research/runs/phase6_formal_evo2_20260921_full_overnight_20260922/predictions.jsonl"
OUTPUT = ROOT / "artifacts/phase15/phase15_parity_smoke_validation_20260922.json"
STATUS_OUTPUT = ROOT / "research/runs/phase15_batch_status.json"
TOLERANCE = 1e-5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} contains a non-object row")
    return rows


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def modal_json(command: str) -> Any:
    result = subprocess.run(
        [str(ROOT / ".venv/bin/modal"), *command.split()],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    approval = validate_approval(ROOT / "artifacts/approvals/phase15_parity_smoke_20260922.json", ROOT)
    initial = load_json(INITIAL)
    final = load_json(FINAL)
    final_rows = load_rows(ROOT / final["outputs"]["predictions_jsonl"])
    canonical = {row["normalized_variant_id"]: row for row in load_rows(CANONICAL)}

    expected_ids = []
    cache_ids = set()
    selection = approval["selection"]
    manifest = load_json(ROOT / approval["dataset"]["development_manifest_path"])
    cache = load_json(ROOT / approval["dataset"]["cache_artifact_path"])
    cache_ids = {
        str(row["normalized_variant_id"])
        for row in cache["verified_rows"]
        if isinstance(row, dict)
    }
    by_id = {
        str(row["normalized_variant_id"]): row
        for row in manifest["records"]
        if isinstance(row, dict)
    }
    expected_ids = sorted(cache_ids) + sorted(set(by_id) - cache_ids)[:8]
    actual_ids = [str(row["normalized_variant_id"]) for row in final_rows]
    errors: list[str] = []
    max_abs_diff = 0.0
    score_fields = (
        "reference_forward",
        "alternate_forward",
        "reference_reverse",
        "alternate_reverse",
    )
    derived_fields = ("delta_forward", "delta_reverse", "delta_primary", "orientation_disagreement")
    for row in final_rows:
        row_id = row.get("normalized_variant_id")
        reference = canonical.get(row_id)
        if reference is None:
            errors.append(f"missing canonical row: {row_id}")
            continue
        for field in score_fields:
            actual = row.get("raw_scores", {}).get(field)
            expected = reference.get("raw_scores", {}).get(field)
            if not finite(actual) or not finite(expected):
                errors.append(f"non-finite or missing {field}: {row_id}")
                continue
            difference = abs(float(actual) - float(expected))
            max_abs_diff = max(max_abs_diff, difference)
            if difference > TOLERANCE:
                errors.append(f"parity mismatch {field}: {row_id}: {difference}")
        for field in derived_fields:
            actual = row.get(field)
            expected = reference.get(field)
            if not finite(actual) or not finite(expected):
                errors.append(f"non-finite or missing {field}: {row_id}")
                continue
            difference = abs(float(actual) - float(expected))
            max_abs_diff = max(max_abs_diff, difference)
            if difference > TOLERANCE:
                errors.append(f"parity mismatch {field}: {row_id}: {difference}")

    checks = {
        "expected_ids_exact": set(actual_ids) == set(expected_ids),
        "expected_rows_64": len(final_rows) == 64,
        "returned_ids_64": len(actual_ids) == 64,
        "duplicates_zero": len(actual_ids) == len(set(actual_ids)),
        "unexpected_ids_zero": set(actual_ids) == set(expected_ids),
        "reference_mismatches_zero": final["acceptance"]["reference_mismatches"] == 0,
        "nonfinite_values_zero": all(
            final["acceptance"][key] == 0
            for key in (
                "nonfinite_forward_scores",
                "nonfinite_reverse_complement_scores",
                "invalid_aggregate_scores",
            )
        ),
        "labels_remote_false": final["scientific_boundary"]["labels_sent_to_modal"] is False,
        "locked_overlap_zero": final["acceptance"]["locked_test_rows"] == 0,
        "canonical_score_parity_pass": not errors and max_abs_diff <= TOLERANCE,
        "persisted_shard_reuse_pass": final["cache"]["stored_shards_reused"] == 1,
        "restart_resume_pass": (
            final["runtime"]["resume"]["remote_invocations_this_execution"] == 0
            and final["runtime"]["resume"]["zero_recomputation"] is True
        ),
        "duplicate_recomputation_zero": final["cache"]["new_remote_records_this_execution"] == 0,
        "ordered_export_pass": actual_ids == sorted(actual_ids),
        "prediction_hash_stable": initial["outputs"]["predictions_sha256"] == final["outputs"]["predictions_sha256"],
        "phase14_untouched": sha256(ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json") == approval["frozen_phase14_artifact"]["sha256"],
    }
    if not all(checks.values()):
        raise ValueError(f"Phase 15 acceptance failed: {checks}; details={errors[:5]}")
    billing_after = modal_json("billing summary --json")
    active_containers = modal_json("container list --json")
    if active_containers != []:
        raise ValueError(f"paid workers remain active after Phase 15: {active_containers}")

    validation = {
        "artifact_id": "phase15-parity-smoke-validation-20260922",
        "phase": 15,
        "status": "PASS_PHASE15_PARITY_AND_RESUME",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "approval": {
            "path": str((ROOT / "artifacts/approvals/phase15_parity_smoke_20260922.json").relative_to(ROOT)),
            "sha256": sha256(ROOT / "artifacts/approvals/phase15_parity_smoke_20260922.json"),
            "git_commit": approval["git"]["commit"],
        },
        "selection": {
            "expected_rows": selection["expected_rows"],
            "verified_cache_rows": selection["verified_cache_rows"],
            "remote_rows": selection["remote_rows"],
            "ids_sha256": selection["ids_sha256"],
            "train_rows": sum(row.get("split") == "TRAIN" for row in final_rows),
            "validation_rows": sum(row.get("split") == "VALIDATION" for row in final_rows),
        },
        "checks": checks,
        "canonical_parity": {
            "source": str(CANONICAL.relative_to(ROOT)),
            "source_sha256": sha256(CANONICAL),
            "tolerance": TOLERANCE,
            "max_abs_diff": max_abs_diff,
            "mismatch_count": len(errors),
        },
        "initial_paid_execution": {
            "artifact": str(INITIAL.relative_to(ROOT)),
            "sha256": sha256(INITIAL),
            "status": initial["status"],
            "remote_invocations": initial["cache"]["remote_invocations"],
            "historical_cache_hits": initial["cache"]["historical_cache_hits_this_execution"],
            "new_remote_records": initial["cache"]["new_remote_records_this_execution"],
            "remote_runtime_seconds": initial["runtime"]["total_remote_wall_seconds"],
            "estimated_cost_usd": initial["cost"]["cumulative_client_wall_rate_estimate_usd"],
            "function_call_ids": initial["runtime"]["function_call_ids"],
            "billing_before": initial["modal_billing"]["before"],
            "billing_after": initial["modal_billing"]["after"],
        },
        "resume_execution": {
            "artifact": str(FINAL.relative_to(ROOT)),
            "sha256": sha256(FINAL),
            "status": final["status"],
            "stored_shards_reused": final["cache"]["stored_shards_reused"],
            "remote_invocations": final["cache"]["remote_invocations"],
            "new_remote_records": final["cache"]["new_remote_records_this_execution"],
            "prediction_sha256": final["outputs"]["predictions_sha256"],
        },
        "scientific_boundary": {
            "labels_remote": False,
            "locked_rows": 0,
            "phase14_started": False,
            "training_hpo_finetuning_started": False,
        },
        "billing_after": {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "snapshot": billing_after,
            "active_containers": active_containers,
            "provider_confirmed_remaining_free_credit_balance": False,
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status = {
        "phase": 15,
        "status": "PASS",
        "recorded_at_utc": validation["recorded_at_utc"],
        "local_contract": {
            "label_free_plan_and_atomic_shard_resume": "PASS",
            "full_cohort_remote_parity": "PASS_FOR_64_ROW_DEVELOPMENT_SMOKE_ONLY",
            "evidence": "artifacts/phase15/phase15_parity_smoke_validation_20260922.json",
        },
        "formal_smoke": validation["selection"],
        "acceptance": validation["checks"],
        "no_remote_compute_after_smoke": True,
        "locked_test_rows": 0,
        "approval": validation["approval"],
    }
    STATUS_OUTPUT.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": validation["status"], "output": str(OUTPUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

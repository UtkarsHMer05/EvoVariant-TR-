#!/usr/bin/env python3
"""Finalize a verified, locally stopped Phase 6 shard cache without remote work."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
LOCKED_MANIFEST = REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
MANIFEST_HASH = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
RECORD_SET_HASH = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
SHARD_SIZE = 32


def stable_hash(value: object) -> str:
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def billing_snapshot() -> dict[str, Any]:
    binary = str(Path(os.sys.executable).with_name("modal"))
    result = subprocess.run(
        [binary, "billing", "summary"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal billing summary",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "interpretation": "workspace-level provider summary, not a per-run invoice",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--billing-high-water-usd", type=float, required=True)
    parser.add_argument("--practical-stop-usd", type=float, required=True)
    args = parser.parse_args()
    args.run_root = args.run_root.resolve()
    args.artifact = args.artifact.resolve()

    manifest_document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256_file(MANIFEST) != MANIFEST_HASH:
        raise RuntimeError("formal development manifest hash changed")
    if manifest_document.get("record_set_sha256") != RECORD_SET_HASH:
        raise RuntimeError("formal development record-set hash changed")
    records = sorted(
        manifest_document.get("records", []),
        key=lambda row: str(row["normalized_variant_id"]),
    )
    if len(records) != 4_000:
        raise RuntimeError("formal development manifest must contain 4,000 records")
    if sha256_file(LOCKED_MANIFEST) == "":
        raise RuntimeError("locked manifest could not be read")

    plan_path = args.run_root / "execution_plan.json"
    plan_document = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_hash = plan_document.pop("execution_plan_sha256", None)
    if plan_hash != stable_hash(plan_document):
        raise RuntimeError("execution plan hash mismatch")
    shard_root = args.run_root / "shards"
    shard_paths = sorted(shard_root.glob("shard_*.json"))
    if not shard_paths:
        raise RuntimeError("no completed shards found")

    rows_by_id: dict[str, dict[str, Any]] = {}
    estimated_usd = 0.0
    historical_cache_hits = 0
    remote_invocations = 0
    function_call_ids: set[str] = set()
    shard_indexes: list[int] = []
    for path in shard_paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise RuntimeError(f"shard is not an object: {path}")
        payload = dict(document)
        recorded_hash = payload.pop("payload_sha256", None)
        if recorded_hash != stable_hash(payload):
            raise RuntimeError(f"shard hash mismatch: {path}")
        index = int(document["shard_index"])
        shard_indexes.append(index)
        expected_ids = [
            str(row["normalized_variant_id"])
            for row in records[index * SHARD_SIZE : (index + 1) * SHARD_SIZE]
        ]
        if (
            document.get("execution_plan_sha256") != plan_hash
            or document.get("status") != "COMPLETED"
            or document.get("source_ids") != expected_ids
        ):
            raise RuntimeError(f"shard does not match the frozen plan: {path}")
        shard_rows = document.get("rows")
        if not isinstance(shard_rows, list) or len(shard_rows) != len(expected_ids):
            raise RuntimeError(f"shard row count is invalid: {path}")
        for row, expected_id in zip(shard_rows, expected_ids, strict=True):
            if not isinstance(row, dict) or row.get("normalized_variant_id") != expected_id:
                raise RuntimeError(f"shard row identity mismatch: {path}")
            if expected_id in rows_by_id:
                raise RuntimeError(f"duplicate completed row: {expected_id}")
            rows_by_id[expected_id] = row
        rate = float(document.get("client_wall_rate_estimate_usd", 0.0))
        if rate < 0:
            raise RuntimeError(f"negative shard rate estimate: {path}")
        estimated_usd += rate
        historical_cache_hits += int(document.get("historical_cache_hits", 0))
        remote_invocations += int(bool(document.get("function_call_id")))
        if document.get("function_call_id"):
            function_call_ids.add(str(document["function_call_id"]))

    if shard_indexes != list(range(len(shard_paths))):
        raise RuntimeError("completed shard indexes are not contiguous from zero")
    observed_ids = set(rows_by_id)
    expected_observed_ids = {
        str(row["normalized_variant_id"])
        for row in records[: len(rows_by_id)]
    }
    if observed_ids != expected_observed_ids:
        raise RuntimeError("completed shard IDs do not match the deterministic prefix")

    ordered_rows = [rows_by_id[identity] for identity in sorted(rows_by_id)]
    predictions_path = args.run_root / "predictions.jsonl"
    atomic_write(
        predictions_path,
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in ordered_rows),
    )
    split_counts = {
        split: sum(row.get("split") == split for row in ordered_rows)
        for split in ("TRAIN", "VALIDATION")
    }
    artifact = {
        "artifact_id": "phase6-formal-evo2-20260921-full-overnight-20260922-partial",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "PARTIAL_BUDGET_STOP",
        "stop_reason": (
            "paid Phase 6 runner stopped before the conservative workspace billing guard; "
            "verified shards remain resumable and no automatic retry was attempted"
        ),
        "approval_artifact": "artifacts/approvals/overnight_completion_20260922.json",
        "protocol_hash": PROTOCOL_HASH,
        "git": {
            "commit": git_value("rev-parse", "HEAD"),
            "dirty": bool(git_value("status", "--porcelain=v1", "--untracked-files=no")),
        },
        "dataset": {
            "formal_manifest_sha256": MANIFEST_HASH,
            "formal_record_set_sha256": RECORD_SET_HASH,
            "full_development_records": 4_000,
            "processed_records": len(ordered_rows),
            "remaining_records": 4_000 - len(ordered_rows),
            "processed_split_counts": split_counts,
        },
        "model": {
            "model_id": "evo2_7b",
            "checkpoint": "evo2_7b",
            "revision": MODEL_REVISION,
            "gpu": "H100",
            "context_length_bp": 8192,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
        },
        "cache": {
            "cache_root": str(shard_root.relative_to(REPO_ROOT)),
            "completed_shards": len(shard_paths),
            "cache_hit_records": historical_cache_hits,
            "historical_cache_reuse_records": historical_cache_hits,
            "new_remote_records": len(ordered_rows) - historical_cache_hits,
            "remote_invocations": remote_invocations,
            "function_call_ids": sorted(function_call_ids),
            "resume_policy": "verified completed shards are skipped; tampering fails closed",
        },
        "cost": {
            "approval_max_budget_usd": 14.0,
            "rate_estimate_stop_usd": 13.5,
            "locked_test_reserve_min_usd": 2.5,
            "cumulative_client_wall_rate_estimate_usd": round(estimated_usd, 6),
            "billing_high_water_metered_usd": args.billing_high_water_usd,
            "practical_stop_metered_usd": args.practical_stop_usd,
            "measured_invoice_usd": None,
            "interpretation": (
                "wall-time estimate and workspace billing snapshots are not a per-run invoice"
            ),
        },
        "runtime": {
            "function_call_ids": sorted(function_call_ids),
            "failure": None,
            "stop_reason": "manual stop at conservative billing high-water guard",
        },
        "outputs": {
            "predictions_jsonl": str(predictions_path.relative_to(REPO_ROOT)),
            "predictions_sha256": sha256_file(predictions_path),
            "execution_plan": str(plan_path.relative_to(REPO_ROOT)),
            "execution_plan_sha256": plan_hash,
        },
        "modal_billing": {"after_stop": billing_snapshot()},
        "scientific_boundary": {
            "labels_sent_to_modal": False,
            "locked_test_labels_accessed": False,
            "full_development_cohort_complete": False,
            "formal_sample_complete": False,
            "metrics_claimed": False,
            "phase14_started": False,
            "training_hpo_finetuning_started": False,
        },
        "acceptance": {
            "selected_rows": 4_000,
            "returned_valid_rows": len(ordered_rows),
            "remaining_rows": 4_000 - len(ordered_rows),
            "reference_mismatches": 0,
            "nonfinite_forward_scores": 0,
            "nonfinite_reverse_complement_scores": 0,
            "invalid_aggregate_scores": 0,
            "unexpected_ids": 0,
            "duplicate_results": 0,
            "labels_sent": False,
            "locked_test_rows": 0,
        },
    }
    atomic_write(args.artifact, json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

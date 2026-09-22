#!/usr/bin/env python3
"""Prepare and validate the narrow, resumable Phase 6 Evo2 authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_APPROVAL_PATH",
    "artifacts/approvals/formal_phase6_resume_20260922.json",
)
PREFLIGHT_PATH = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_PREFLIGHT_GATE_PATH",
    "artifacts/phase6/formal_phase6_resume_preflight_20260922.json",
)
RUN_ROOT = REPO_ROOT / ("research/runs/phase6_formal_evo2_20260921_full_overnight_20260922")
MANIFEST_PATH = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
TRAIN_MANIFEST_PATH = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_train_manifest.json"
)
VALIDATION_MANIFEST_PATH = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_validation_manifest.json"
)
LOCKED_MANIFEST_PATH = REPO_ROOT / (
    "research/ml_extension/splits/authoritative_locked_test_manifest.json"
)
CACHE_PATH = REPO_ROOT / ("artifacts/phase6/formal_budgeted_cache_reuse_verification_20260921.json")
PROTOCOL_PATH = REPO_ROOT / "research/ml_extension/protocol.yaml"
EXPECTED_PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
EXPECTED_MANIFEST_HASH = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
EXPECTED_RECORD_SET_HASH = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_LOCKED_HASH = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_CACHE_HASH = "1bf988be8777cc7299ea0d2154690e301dced9089402acfd9a83122b38424011"
EXPECTED_TRAIN_HASH = "32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1"
EXPECTED_VALIDATION_HASH = "b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b"
PAR_RESOLUTION_PATH = REPO_ROOT / "artifacts/reference/par_mask_resolution_20260922.json"
EXPECTED_PAR_RESOLUTION_HASH = "2f71248d7a97329db24301a73bdd427a2673af7ebc62a29a2ee4467060815b42"
EXPECTED_MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
EXPECTED_MODEL_SNAPSHOT = "bda0089f92582d5baabf0f22d9fc85f3588f6b58"
EXPECTED_PLAN_HASH = "92be77325911e13b172f180c2328b2ec1ebb6ff43f671b6978cb28f3c86c4b7a"
EXPECTED_COMPLETED_ROWS = int(
    os.environ.get("EVOVARIANT_TR_FORMAL_RESUME_COMPLETED_ROWS", "3232")
)
EXPECTED_COMPLETED_SHARDS = int(
    os.environ.get("EVOVARIANT_TR_FORMAL_RESUME_COMPLETED_SHARDS", "101")
)
EXPECTED_TOTAL_ROWS = 4_000
SHARD_SIZE = 32
HARD_CAP_USD = float(os.environ.get("EVOVARIANT_TR_FORMAL_RESUME_HARD_CAP_USD", "2.50"))
SAFETY_STOP_USD = float(
    os.environ.get("EVOVARIANT_TR_FORMAL_RESUME_SAFETY_STOP_USD", "2.25")
)
APPROVAL_VERSION = os.environ.get(
    "EVOVARIANT_TR_FORMAL_RESUME_APPROVAL_VERSION",
    "formal-phase6-resume-v1",
)


class ResumeApprovalError(ValueError):
    """Raised when the narrow Phase 6 resume scope is not provable."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: object) -> str:
    return sha256_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResumeApprovalError(f"cannot read JSON artifact {path}: {exc}") from exc


def git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def repository_snapshot() -> dict[str, Any]:
    head = git_value("rev-parse", "HEAD")
    tree = git_value("rev-parse", "HEAD^{tree}")
    return {
        "branch": git_value("branch", "--show-current"),
        "commit": head,
        "head_tree": tree,
        "working_tree_dirty": bool(git_value("status", "--porcelain=v1", "--untracked-files=no")),
        "working_tree_policy": "approval binds HEAD; existing local changes remain preserved",
    }


def _run_modal(*args: str) -> subprocess.CompletedProcess[str]:
    binary = str(Path(sys.executable).with_name("modal"))
    return subprocess.run(
        [binary, *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30, check=False
    )


def billing_snapshot() -> dict[str, Any]:
    result = _run_modal("billing", "summary")
    if result.returncode != 0:
        raise ResumeApprovalError(f"modal billing snapshot failed: {result.stderr.strip()}")
    metered = re.search(r"Metered Cost:\s*([0-9]+(?:\.[0-9]+)?)", result.stdout)
    billed = re.search(r"Billed Cost:\s*\$\s*([0-9]+(?:\.[0-9]+)?)", result.stdout)
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal billing summary",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "workspace_metered_usd": float(metered.group(1)) if metered else None,
        "workspace_billed_usd": float(billed.group(1)) if billed else None,
        "interpretation": "workspace-level provider evidence, not a per-run invoice",
    }


def container_snapshot() -> dict[str, Any]:
    result = _run_modal("container", "list", "--json")
    if result.returncode != 0:
        raise ResumeApprovalError(f"modal container snapshot failed: {result.stderr.strip()}")
    try:
        containers = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise ResumeApprovalError("modal container list was not valid JSON") from exc
    if not isinstance(containers, list):
        raise ResumeApprovalError("modal container list must be a JSON list")
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal container list --json",
        "returncode": result.returncode,
        "containers": containers,
        "active_containers": len(containers),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def app_snapshot() -> dict[str, Any]:
    result = _run_modal("app", "list")
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal app list",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def load_records() -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    if sha256_file(PROTOCOL_PATH) != EXPECTED_PROTOCOL_HASH:
        raise ResumeApprovalError("protocol hash changed")
    if sha256_file(TRAIN_MANIFEST_PATH) != EXPECTED_TRAIN_HASH:
        raise ResumeApprovalError("formal train manifest hash changed")
    if sha256_file(VALIDATION_MANIFEST_PATH) != EXPECTED_VALIDATION_HASH:
        raise ResumeApprovalError("formal validation manifest hash changed")
    if sha256_file(MANIFEST_PATH) != EXPECTED_MANIFEST_HASH:
        raise ResumeApprovalError("formal development manifest hash changed")
    if sha256_file(LOCKED_MANIFEST_PATH) != EXPECTED_LOCKED_HASH:
        raise ResumeApprovalError("locked-test manifest hash changed")
    manifest = read_json(MANIFEST_PATH)
    if manifest.get("record_set_sha256") != EXPECTED_RECORD_SET_HASH:
        raise ResumeApprovalError("formal record-set hash changed")
    records = sorted(manifest.get("records", []), key=lambda row: str(row["normalized_variant_id"]))
    if len(records) != EXPECTED_TOTAL_ROWS:
        raise ResumeApprovalError("formal development manifest is not exactly 4,000 rows")
    locked = read_json(LOCKED_MANIFEST_PATH)
    locked_ids = {
        str(row["normalized_variant_id"])
        for row in locked.get("records", [])
        if isinstance(row, dict) and "normalized_variant_id" in row
    }
    ids = [str(row["normalized_variant_id"]) for row in records]
    if len(set(ids)) != EXPECTED_TOTAL_ROWS or set(ids) & locked_ids:
        raise ResumeApprovalError("formal IDs are duplicated or overlap the locked set")
    return (
        records,
        locked_ids,
        {
            "formal_development_manifest_path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "formal_development_manifest_sha256": EXPECTED_MANIFEST_HASH,
            "formal_record_set_sha256": EXPECTED_RECORD_SET_HASH,
            "formal_record_count": EXPECTED_TOTAL_ROWS,
            "formal_train_manifest_path": str(TRAIN_MANIFEST_PATH.relative_to(REPO_ROOT)),
            "formal_train_manifest_sha256": EXPECTED_TRAIN_HASH,
            "formal_validation_manifest_path": str(VALIDATION_MANIFEST_PATH.relative_to(REPO_ROOT)),
            "formal_validation_manifest_sha256": EXPECTED_VALIDATION_HASH,
            "locked_test_manifest_path": str(LOCKED_MANIFEST_PATH.relative_to(REPO_ROOT)),
            "locked_test_manifest_sha256": EXPECTED_LOCKED_HASH,
            "locked_test_count": len(locked_ids),
        },
    )


def load_historical_cache() -> set[str]:
    if sha256_file(CACHE_PATH) != EXPECTED_CACHE_HASH:
        raise ResumeApprovalError("historical cache-reuse artifact hash changed")
    document = read_json(CACHE_PATH)
    rows = document.get("verified_rows")
    if document.get("status") != "PASS_COMPATIBLE_CACHE_REUSE_56" or not isinstance(rows, list):
        raise ResumeApprovalError("historical cache-reuse artifact is not the verified 56-row set")
    ids = [str(row["normalized_variant_id"]) for row in rows]
    if len(ids) != 56 or len(set(ids)) != 56:
        raise ResumeApprovalError("historical cache-reuse IDs are not exactly 56 unique rows")
    return set(ids)


def load_par_resolution() -> dict[str, Any]:
    if sha256_file(PAR_RESOLUTION_PATH) != EXPECTED_PAR_RESOLUTION_HASH:
        raise ResumeApprovalError("PAR mask-resolution artifact hash changed")
    document = read_json(PAR_RESOLUTION_PATH)
    if document.get("status") != "PASS_ALIAS_ELIGIBILITY":
        raise ResumeApprovalError("PAR mask-resolution artifact is not PASS")
    variants = document.get("variants")
    ids = {
        str(item.get("original_locus", {}).get("normalized_variant_id"))
        for item in variants
        if isinstance(item, dict)
    }
    if ids != {
        "GRCh38:Y:1286043:T>C",
        "GRCh38:Y:1309674:G>T",
    }:
        raise ResumeApprovalError("PAR mask-resolution artifact does not authorize exactly two IDs")
    return document


def _finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def verify_coverage(
    records: list[dict[str, Any]], locked_ids: set[str], cache_ids: set[str]
) -> dict[str, Any]:
    plan_path = RUN_ROOT / "execution_plan.json"
    plan = read_json(plan_path)
    recorded_plan_hash = plan.pop("execution_plan_sha256", None)
    if recorded_plan_hash != stable_hash(plan) or recorded_plan_hash != EXPECTED_PLAN_HASH:
        raise ResumeApprovalError("existing execution plan hash is stale or invalid")
    for key, expected in {
        "protocol_hash": EXPECTED_PROTOCOL_HASH,
        "development_manifest_sha256": EXPECTED_MANIFEST_HASH,
        "formal_manifest_record_set_sha256": EXPECTED_RECORD_SET_HASH,
        "locked_manifest_sha256": EXPECTED_LOCKED_HASH,
        "model_id": "evo2_7b",
        "model_revision": EXPECTED_MODEL_REVISION,
        "gpu_type": "H100",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
        "record_count": EXPECTED_TOTAL_ROWS,
        "shard_size": SHARD_SIZE,
    }.items():
        if plan.get(key) != expected:
            raise ResumeApprovalError(f"execution plan field {key} is not frozen")
    shard_root = RUN_ROOT / "shards"
    pending = sorted(shard_root.glob("*.pending.json"))
    if pending:
        raise ResumeApprovalError("a stale pending Modal call marker exists")
    shard_paths = sorted(shard_root.glob("shard_*.json"))
    if len(shard_paths) != EXPECTED_COMPLETED_SHARDS:
        raise ResumeApprovalError("verified checkpoint does not contain exactly 101 shards")
    observed: dict[str, dict[str, Any]] = {}
    rates: list[float] = []
    function_call_ids: set[str] = set()
    historical_hits = 0
    for expected_index, path in enumerate(shard_paths):
        match = re.fullmatch(r"shard_(\d{6})\.json", path.name)
        if not match or int(match.group(1)) != expected_index:
            raise ResumeApprovalError(f"shard prefix is not contiguous: {path.name}")
        document = read_json(path)
        payload = dict(document)
        recorded_hash = payload.pop("payload_sha256", None)
        if recorded_hash != stable_hash(payload):
            raise ResumeApprovalError(f"shard payload hash mismatch: {path.name}")
        expected_ids = [
            str(row["normalized_variant_id"])
            for row in records[expected_index * SHARD_SIZE : (expected_index + 1) * SHARD_SIZE]
        ]
        if (
            document.get("execution_plan_sha256") != recorded_plan_hash
            or document.get("status") != "COMPLETED"
            or document.get("source_ids") != expected_ids
        ):
            raise ResumeApprovalError(f"shard does not match the frozen source prefix: {path.name}")
        rows = document.get("rows")
        if not isinstance(rows, list) or len(rows) != len(expected_ids):
            raise ResumeApprovalError(f"invalid row count: {path.name}")
        for row, expected_id in zip(rows, expected_ids, strict=True):
            if not isinstance(row, dict) or row.get("normalized_variant_id") != expected_id:
                raise ResumeApprovalError(f"row identity mismatch: {path.name}")
            if expected_id in observed or expected_id in locked_ids:
                raise ResumeApprovalError(f"duplicate or locked row in cache: {expected_id}")
            raw = row.get("raw_scores")
            if not isinstance(raw, dict) or not all(
                _finite(raw.get(key))
                for key in (
                    "reference_forward",
                    "alternate_forward",
                    "reference_reverse",
                    "alternate_reverse",
                )
            ):
                raise ResumeApprovalError(f"non-finite raw score in cache: {expected_id}")
            if not all(
                _finite(row.get(key)) for key in ("delta_forward", "delta_reverse", "delta_primary")
            ):
                raise ResumeApprovalError(f"non-finite aggregate score in cache: {expected_id}")
            observed[expected_id] = row
        rate = float(document.get("client_wall_rate_estimate_usd", 0.0))
        if rate < 0 or not math.isfinite(rate):
            raise ResumeApprovalError(f"invalid cost estimate in cache: {path.name}")
        rates.append(rate)
        historical_hits += int(document.get("historical_cache_hits", 0))
        if document.get("function_call_id"):
            function_call_ids.add(str(document["function_call_id"]))
    if len(observed) != EXPECTED_COMPLETED_ROWS:
        raise ResumeApprovalError(
            f"verified checkpoint row count is not {EXPECTED_COMPLETED_ROWS}"
        )
    all_ids = [str(row["normalized_variant_id"]) for row in records]
    completed_ids = set(all_ids[:EXPECTED_COMPLETED_ROWS])
    if set(observed) != completed_ids:
        raise ResumeApprovalError("verified checkpoint is not the deterministic 3,232-row prefix")
    remaining_ids = all_ids[EXPECTED_COMPLETED_ROWS:]
    remaining_cache_ids = [identity for identity in remaining_ids if identity in cache_ids]
    remote_ids = [identity for identity in remaining_ids if identity not in cache_ids]
    if set(remaining_cache_ids) & set(observed) or set(remote_ids) & set(observed):
        raise ResumeApprovalError("remaining IDs overlap completed IDs")
    if len(remaining_ids) != EXPECTED_TOTAL_ROWS - EXPECTED_COMPLETED_ROWS:
        raise ResumeApprovalError("remaining coverage count is inconsistent with the checkpoint")
    last_rates = rates[-3:]
    conservative_estimate = max(last_rates) * math.ceil(len(remote_ids) / SHARD_SIZE)
    if conservative_estimate > SAFETY_STOP_USD:
        raise ResumeApprovalError("remaining remote projection exceeds the $2.25 safety stop")

    def id_hash(values: list[str]) -> str:
        return sha256_bytes(("\n".join(values) + "\n").encode())

    return {
        "run_root": str(RUN_ROOT.relative_to(REPO_ROOT)),
        "execution_plan_path": str(plan_path.relative_to(REPO_ROOT)),
        "execution_plan_sha256": recorded_plan_hash,
        "completed_shards": EXPECTED_COMPLETED_SHARDS,
        "completed_rows": EXPECTED_COMPLETED_ROWS,
        "remaining_rows": len(remaining_ids),
        "remaining_ids_sha256": id_hash(remaining_ids),
        "historical_cache_remaining_rows": len(remaining_cache_ids),
        "historical_cache_remaining_ids_sha256": id_hash(remaining_cache_ids),
        "remote_submission_rows": len(remote_ids),
        "remote_submission_ids_sha256": id_hash(remote_ids),
        "historical_cache_total_rows": len(cache_ids),
        "historical_cache_completed_rows": historical_hits,
        "remaining_shards": math.ceil(len(remaining_ids) / SHARD_SIZE),
        "conservative_remaining_rate_estimate_usd": round(conservative_estimate, 6),
        "function_call_ids": sorted(function_call_ids),
    }


def build_document(user_credits: dict[str, float]) -> tuple[dict[str, Any], dict[str, Any]]:
    records, locked_ids, dataset = load_records()
    cache_ids = load_historical_cache()
    par_resolution = load_par_resolution()
    coverage = verify_coverage(records, locked_ids, cache_ids)
    billing = billing_snapshot()
    containers = container_snapshot()
    if containers["active_containers"] != 0:
        raise ResumeApprovalError("active Modal containers exist before the resume")
    apps = app_snapshot()
    git = repository_snapshot()
    now = datetime.now(UTC).isoformat()
    user_credits = dict(user_credits)
    user_credits["evidence_source"] = "user-provided current Modal account evidence"
    approval = {
        "artifact_id": "evovariant-tr-formal-phase6-resume-20260922",
        "study_id": "ML-DEV-BUDGETED-001",
        "approval_version": APPROVAL_VERSION,
        "approved_by": "user",
        "approved_at": now,
        "authorization_source": (
            "explicit user authorization in the current request; remaining formal Phase 6 "
            "Evo2 workload only"
        ),
        "max_budget_usd": HARD_CAP_USD,
        "budget_control": {
            "hard_cap_usd": HARD_CAP_USD,
            "runner_safety_stop_usd": SAFETY_STOP_USD,
            "locked_test_reserve_min_usd": 0.0,
            "no_silent_budget_widening": True,
            "billing_basis": (
                "user-reported free credits; provider snapshots are workspace evidence"
            ),
        },
        "protocol": {
            "path": str(PROTOCOL_PATH.relative_to(REPO_ROOT)),
            "sha256": EXPECTED_PROTOCOL_HASH,
        },
        "dataset": {
            **dataset,
            "formal_train_manifest_path": (
                "research/ml_extension/splits/formal_budgeted_20260921/formal_train_manifest.json"
            ),
            "formal_train_manifest_sha256": EXPECTED_TRAIN_HASH,
            "formal_validation_manifest_path": (
                "research/ml_extension/splits/formal_budgeted_20260921/formal_validation_manifest.json"
            ),
            "formal_validation_manifest_sha256": EXPECTED_VALIDATION_HASH,
            "cache_reuse_verification_path": str(CACHE_PATH.relative_to(REPO_ROOT)),
            "cache_reuse_verification_sha256": EXPECTED_CACHE_HASH,
            "locked_labels_boundary": "no locked-test labels or rows may enter this workload",
        },
        "reference_handling_amendment": {
            "path": str(PAR_RESOLUTION_PATH.relative_to(REPO_ROOT)),
            "sha256": EXPECTED_PAR_RESOLUTION_HASH,
            "status": par_resolution["status"],
            "allowed_par_alias_ids": [
                "GRCh38:Y:1286043:T>C",
                "GRCh38:Y:1309674:G>T",
            ],
        },
        "git": git,
        "model": {
            "model_id": "evo2",
            "checkpoint": "evo2_7b",
            "revision": EXPECTED_MODEL_REVISION,
            "model_snapshot_revision": EXPECTED_MODEL_SNAPSHOT,
            "assembly": "GRCh38",
            "context_length_bp": 8192,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
        },
        "gpu": {"type": "H100", "count": 1},
        "allowed_workloads": [
            "only the remaining formal Phase 6 Evo2 records proven by the resume coverage",
            "reuse of all verified completed shards and compatible historical cache rows",
            "local Phase 6 integrity verification after completion",
        ],
        "excluded_workloads": [
            "NT or Nucleotide Transformer scoring",
            "Caduceus scoring",
            "fine-tuning, HPO, ensemble, calibration, robustness, or Phase 14",
            "the 946-row locked test",
            "labels in Modal requests",
            "deployment, publication, push, or credential use",
        ],
        "stop_conditions": [
            "stop at the $2.25 safety stop and absolutely before the $2.50 hard cap",
            (
                "stop on any unexpected ID, duplicate, reference mismatch, non-finite "
                "FWD/RC/aggregate score, or stale hash"
            ),
            "stop if labels are sent to Modal or any locked-test row is accessed",
            "stop if any active paid container remains after the workload",
            "do not recompute verified shards; preserve resumability on any failure",
        ],
        "execution_contract": {
            "scope": "remaining formal Phase 6 Evo2 workload only",
            "formal_development_records": EXPECTED_TOTAL_ROWS,
            "completed_checkpoint_records": EXPECTED_COMPLETED_ROWS,
            "remaining_formal_records": coverage["remaining_rows"],
            "remote_submission_records": coverage["remote_submission_rows"],
            "cohort_splits": ["TRAIN", "VALIDATION"],
            "reuse_verified_shards": True,
            "zero_recomputation": True,
            "labels_remote_transport": "prohibited",
            "locked_test_access": "prohibited",
            "coverage": coverage,
        },
        "cost_baseline": {
            "captured_at_utc": now,
            "modal_billing": billing,
            "modal_container_inventory": containers,
            "modal_app_inventory": apps,
            "active_containers": containers["active_containers"],
            "user_credit_evidence": user_credits,
        },
    }
    gate = {
        "artifact_id": "formal-phase6-resume-preflight-20260922",
        "approval_version": APPROVAL_VERSION,
        "status": "PASS_FORMAL_PHASE6_RESUME_PREFLIGHT",
        "created_at_utc": now,
        "approval_path": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "approval_sha256": stable_hash(approval),
        "git_commit": git["commit"],
        "protocol_hash": EXPECTED_PROTOCOL_HASH,
        "coverage": coverage,
        "billing_before": billing,
        "containers_before": containers,
        "user_credit_evidence": user_credits,
        "no_labels_or_locked_rows": True,
    }
    return approval, gate


def validate_approval(path: str | Path = APPROVAL_PATH) -> dict[str, Any]:
    approval = read_json(Path(path))
    if approval.get("approval_version") != APPROVAL_VERSION:
        raise ResumeApprovalError("unsupported Phase 6 resume approval version")
    if approval.get("max_budget_usd") != HARD_CAP_USD:
        raise ResumeApprovalError("resume approval hard cap must be $2.50")
    budget = approval.get("budget_control", {})
    if (
        budget.get("hard_cap_usd") != HARD_CAP_USD
        or budget.get("runner_safety_stop_usd") != SAFETY_STOP_USD
    ):
        raise ResumeApprovalError(
            f"resume approval budget must be ${HARD_CAP_USD:.2f} hard / "
            f"${SAFETY_STOP_USD:.2f} safety"
        )
    if budget.get("locked_test_reserve_min_usd") != 0.0:
        raise ResumeApprovalError("resume approval cannot reserve or authorize locked-test work")
    if approval.get("git", {}).get("commit") != git_value("rev-parse", "HEAD"):
        raise ResumeApprovalError("resume approval is not bound to current HEAD")
    if approval.get("git", {}).get("head_tree") != git_value("rev-parse", "HEAD^{tree}"):
        raise ResumeApprovalError("resume approval HEAD tree is stale")
    if approval.get("protocol", {}).get("sha256") != EXPECTED_PROTOCOL_HASH:
        raise ResumeApprovalError("resume approval protocol hash is stale")
    model = approval.get("model", {})
    if (
        model.get("revision") != EXPECTED_MODEL_REVISION
        or model.get("model_snapshot_revision") != EXPECTED_MODEL_SNAPSHOT
        or model.get("assembly") != "GRCh38"
        or model.get("context_length_bp") != 8192
        or model.get("orientation") != "forward_and_reverse"
        or model.get("score_semantics") != "alternate_minus_reference_log_likelihood"
    ):
        raise ResumeApprovalError("resume approval model contract is stale")
    records, locked_ids, _ = load_records()
    cache_ids = load_historical_cache()
    load_par_resolution()
    coverage = verify_coverage(records, locked_ids, cache_ids)
    if coverage != approval.get("execution_contract", {}).get("coverage"):
        raise ResumeApprovalError("resume approval coverage no longer matches the verified cache")
    if approval.get("cost_baseline", {}).get("active_containers") != 0:
        raise ResumeApprovalError("resume approval baseline has active containers")
    return approval


def validate_preflight(
    path: str | Path = PREFLIGHT_PATH, approval_path: str | Path = APPROVAL_PATH
) -> dict[str, Any]:
    gate = read_json(Path(path))
    approval = validate_approval(approval_path)
    if gate.get("status") != "PASS_FORMAL_PHASE6_RESUME_PREFLIGHT":
        raise ResumeApprovalError("resume preflight gate is not PASS")
    if gate.get("approval_sha256") != sha256_file(Path(approval_path)):
        raise ResumeApprovalError("resume preflight approval hash is stale")
    if gate.get("git_commit") != git_value("rev-parse", "HEAD"):
        raise ResumeApprovalError("resume preflight commit is stale")
    if gate.get("coverage") != approval["execution_contract"]["coverage"]:
        raise ResumeApprovalError("resume preflight coverage is stale")
    containers = gate.get("containers_before", {})
    if containers.get("active_containers") != 0 or gate.get("no_labels_or_locked_rows") is not True:
        raise ResumeApprovalError("resume preflight does not prove a safe boundary")
    return gate


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--monthly-credits", type=float, default=30.0)
    parser.add_argument("--credits-used", type=float, default=22.83)
    parser.add_argument("--credits-left", type=float, default=7.17)
    parser.add_argument("--billed-spend", type=float, default=0.0)
    args = parser.parse_args()
    if args.prepare:
        approval, gate = build_document(
            {
                "monthly_credits_usd": args.monthly_credits,
                "credits_used_usd": args.credits_used,
                "credits_left_usd": args.credits_left,
                "billed_spend_usd": args.billed_spend,
            }
        )
        write_json(APPROVAL_PATH, approval)
        gate["approval_sha256"] = sha256_file(APPROVAL_PATH)
        write_json(PREFLIGHT_PATH, gate)
        validate_preflight(PREFLIGHT_PATH, APPROVAL_PATH)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "approval": str(APPROVAL_PATH),
                    "preflight": str(PREFLIGHT_PATH),
                    "coverage": approval["execution_contract"]["coverage"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    approval = validate_approval()
    validate_preflight()
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval": str(APPROVAL_PATH),
                "hard_cap_usd": approval["max_budget_usd"],
                "safety_stop_usd": approval["budget_control"]["runner_safety_stop_usd"],
                "coverage": approval["execution_contract"]["coverage"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

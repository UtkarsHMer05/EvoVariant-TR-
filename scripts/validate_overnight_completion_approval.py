#!/usr/bin/env python3
"""Validate the user-authorized overnight completion approval.

This validator is intentionally separate from the historical $8.00 formal
preflight approval.  It binds the same immutable scientific inputs to the
current checkout and the overnight card's $14.00/$13.50 budget boundary.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/overnight_completion_20260922.json"
EXPECTED_APPROVAL_VERSION = "overnight-completion-v1"
EXPECTED_PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
EXPECTED_FORMAL_HASHES = {
    "formal_train_manifest.json": (
        "32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1"
    ),
    "formal_validation_manifest.json": (
        "b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b"
    ),
    "formal_development_manifest.json": (
        "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
    ),
}
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_CACHE_REUSE_ARTIFACT = (
    "artifacts/phase6/formal_budgeted_cache_reuse_verification_20260921.json"
)
EXPECTED_CACHE_REUSE_SHA256 = "1bf988be8777cc7299ea0d2154690e301dced9089402acfd9a83122b38424011"
EXPECTED_SOURCE_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
EXPECTED_MODEL_SNAPSHOT = "bda0089f92582d5baabf0f22d9fc85f3588f6b58"
EXPECTED_HARD_CAP_USD = 14.0
EXPECTED_SAFETY_STOP_USD = 13.5
MIN_LOCKED_RESERVE_USD = 2.5


class OvernightApprovalError(ValueError):
    """Raised when the overnight approval is missing or stale."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OvernightApprovalError(f"cannot read JSON artifact {path}: {exc}") from exc


def repo_path(value: object, context: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise OvernightApprovalError(f"{context} must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise OvernightApprovalError(f"{context} must be repository-relative")
    target = REPO_ROOT / path
    if not target.is_file():
        raise OvernightApprovalError(f"{context} does not exist: {value}")
    return target


def required_string(mapping: object, key: str, context: str) -> str:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise OvernightApprovalError(f"{context}.{key} must be a non-empty string")
    return value


def required_list(mapping: object, key: str, context: str) -> list[str]:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise OvernightApprovalError(f"{context}.{key} must be a non-empty list of strings")
    return value


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _check_hash(path_value: object, hash_value: object, context: str) -> Path:
    path = repo_path(path_value, f"{context}.path")
    if not isinstance(hash_value, str) or sha256_file(path) != hash_value:
        raise OvernightApprovalError(f"{context} hash does not match the checked-in artifact")
    return path


def validate_approval(path: str | Path = DEFAULT_APPROVAL_PATH) -> dict[str, Any]:
    """Validate the exact overnight approval and all scientific bindings."""
    approval = read_json(Path(path))
    if not isinstance(approval, dict):
        raise OvernightApprovalError("approval artifact must be a JSON object")

    required = {
        "artifact_id",
        "study_id",
        "approval_version",
        "approved_by",
        "approved_at",
        "authorization_source",
        "max_budget_usd",
        "budget_control",
        "protocol",
        "dataset",
        "git",
        "model",
        "gpu",
        "allowed_workloads",
        "excluded_workloads",
        "stop_conditions",
        "execution_contract",
        "cost_baseline",
    }
    missing = sorted(required.difference(approval))
    if missing:
        raise OvernightApprovalError("approval missing fields: " + ", ".join(missing))
    if approval["study_id"] != "ML-DEV-BUDGETED-001":
        raise OvernightApprovalError("approval is for a different study")
    if approval["approval_version"] != EXPECTED_APPROVAL_VERSION:
        raise OvernightApprovalError("unsupported overnight approval version")
    for key in ("approved_by", "approved_at", "authorization_source"):
        required_string(approval, key, "approval")
    if "explicit user authorization" not in str(approval["authorization_source"]).casefold():
        raise OvernightApprovalError("authorization_source must record explicit user authorization")
    if approval["max_budget_usd"] != EXPECTED_HARD_CAP_USD:
        raise OvernightApprovalError("max_budget_usd must be exactly 14.00")

    budget = approval["budget_control"]
    if not isinstance(budget, dict):
        raise OvernightApprovalError("budget_control must be an object")
    if budget.get("hard_cap_usd") != EXPECTED_HARD_CAP_USD:
        raise OvernightApprovalError("budget hard cap must be exactly 14.00")
    if budget.get("runner_safety_stop_usd") != EXPECTED_SAFETY_STOP_USD:
        raise OvernightApprovalError("runner safety stop must be exactly 13.50")
    if budget.get("locked_test_reserve_min_usd", 0) < MIN_LOCKED_RESERVE_USD:
        raise OvernightApprovalError("locked-test reserve must be at least 2.50")
    if budget.get("no_silent_budget_widening") is not True:
        raise OvernightApprovalError("no_silent_budget_widening must be true")

    protocol = approval["protocol"]
    protocol_path = repo_path(
        protocol.get("path") if isinstance(protocol, dict) else None, "protocol"
    )
    if (
        not isinstance(protocol, dict)
        or protocol.get("path") != "research/ml_extension/protocol.yaml"
        or protocol.get("sha256") != EXPECTED_PROTOCOL_HASH
        or sha256_file(protocol_path) != EXPECTED_PROTOCOL_HASH
    ):
        raise OvernightApprovalError("approval protocol hash is not the current frozen hash")

    dataset = approval["dataset"]
    if not isinstance(dataset, dict):
        raise OvernightApprovalError("dataset must be an object")
    for filename, expected_hash in EXPECTED_FORMAL_HASHES.items():
        path_key = {
            "formal_train_manifest.json": "formal_train_manifest_path",
            "formal_validation_manifest.json": "formal_validation_manifest_path",
            "formal_development_manifest.json": "formal_development_manifest_path",
        }[filename]
        hash_key = path_key.removesuffix("_path") + "_sha256"
        _check_hash(dataset.get(path_key), dataset.get(hash_key), f"dataset.{path_key}")
        if dataset.get(hash_key) != expected_hash:
            raise OvernightApprovalError(f"dataset.{hash_key} is not the frozen hash")
    if dataset.get("formal_record_set_sha256") != EXPECTED_RECORD_SET_SHA256:
        raise OvernightApprovalError("formal record-set hash is not frozen")
    locked = _check_hash(
        dataset.get("locked_test_manifest_path"),
        dataset.get("locked_test_manifest_sha256"),
        "dataset.locked_test_manifest",
    )
    if sha256_file(locked) != EXPECTED_LOCKED_MANIFEST_SHA256:
        raise OvernightApprovalError("locked-test manifest hash is not frozen")
    if dataset.get("cache_reuse_verification_path") != EXPECTED_CACHE_REUSE_ARTIFACT:
        raise OvernightApprovalError("cache reuse artifact path is not canonical")
    cache = _check_hash(
        dataset.get("cache_reuse_verification_path"),
        dataset.get("cache_reuse_verification_sha256"),
        "dataset.cache_reuse_verification",
    )
    cache_document = read_json(cache)
    if cache_document.get("status") != "PASS_COMPATIBLE_CACHE_REUSE_56" or cache_document.get(
        "record_count"
    ) != 56:
        raise OvernightApprovalError("verified 56-row cache reuse artifact is not current")

    git = approval["git"]
    if not isinstance(git, dict) or git.get("commit") != current_commit():
        raise OvernightApprovalError(
            f"approval commit {git.get('commit') if isinstance(git, dict) else None} "
            f"is not current HEAD {current_commit()}"
        )

    model = approval["model"]
    expected_model = {
        "model_id": "evo2",
        "checkpoint": "evo2_7b",
        "revision": EXPECTED_SOURCE_REVISION,
        "source_repository": "https://github.com/ArcInstitute/evo2.git",
        "model_repository": "https://huggingface.co/arcinstitute/evo2_7b",
        "model_snapshot_revision": EXPECTED_MODEL_SNAPSHOT,
        "assembly": "GRCh38",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
    }
    for key, expected in expected_model.items():
        if not isinstance(model, dict) or model.get(key) != expected:
            raise OvernightApprovalError(f"model.{key} is not canonical")
    gpu = approval["gpu"]
    if not isinstance(gpu, dict) or gpu.get("type") != "H100":
        raise OvernightApprovalError("GPU must be H100")

    allowed = required_list(approval, "allowed_workloads", "approval")
    allowed_text = " ".join(allowed).casefold()
    for token in ("formal phase 6", "phase 7", "phase 14"):
        if token not in allowed_text:
            raise OvernightApprovalError(f"allowed_workloads must include {token!r}")
    excluded = " ".join(required_list(approval, "excluded_workloads", "approval")).casefold()
    for token in ("full t0", "full evo2 fine-tuning", "clinical", "automatic deployment"):
        if token not in excluded:
            raise OvernightApprovalError(f"excluded_workloads must include {token!r}")
    stop_text = " ".join(required_list(approval, "stop_conditions", "approval")).casefold()
    for token in ("13.50", "14.00", "2.50", "no labels", "active container"):
        if token not in stop_text:
            raise OvernightApprovalError(f"stop_conditions must mention {token!r}")

    contract = approval["execution_contract"]
    if not isinstance(contract, dict):
        raise OvernightApprovalError("execution_contract must be an object")
    if contract.get("formal_development_records") != 4000:
        raise OvernightApprovalError("formal development contract must contain 4,000 records")
    if set(contract.get("development_splits", [])) != {"TRAIN", "VALIDATION"}:
        raise OvernightApprovalError(
            "development contract must restrict scoring to TRAIN/VALIDATION"
        )
    if contract.get("labels_remote_transport") != "prohibited":
        raise OvernightApprovalError("remote label transport must be prohibited")
    if contract.get("locked_test_selection_before_freeze") != "prohibited":
        raise OvernightApprovalError("locked-test selection before freeze must be prohibited")
    if contract.get("phase14") != "one_shot_after_selection_freeze":
        raise OvernightApprovalError("Phase 14 must be one-shot after selection freeze")

    baseline = approval["cost_baseline"]
    if not isinstance(baseline, dict):
        raise OvernightApprovalError("cost_baseline must be an object")
    for key in ("captured_at_utc", "modal_billing_command", "modal_app_inventory_command"):
        required_string(baseline, key, "cost_baseline")
    for key in ("workspace_metered_usd", "workspace_billed_usd"):
        value = baseline.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise OvernightApprovalError(f"cost_baseline.{key} must be finite")
        if value < 0:
            raise OvernightApprovalError(f"cost_baseline.{key} must be non-negative")
    if baseline.get("active_containers") != 0:
        raise OvernightApprovalError("approval baseline must have zero active containers")

    return approval


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_APPROVAL_PATH
    approval = validate_approval(path)
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval_artifact": str(path),
                "study_id": approval["study_id"],
                "hard_cap_usd": approval["budget_control"]["hard_cap_usd"],
                "runner_safety_stop_usd": approval["budget_control"]["runner_safety_stop_usd"],
                "locked_test_reserve_min_usd": approval["budget_control"][
                    "locked_test_reserve_min_usd"
                ],
                "git_commit": approval["git"]["commit"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

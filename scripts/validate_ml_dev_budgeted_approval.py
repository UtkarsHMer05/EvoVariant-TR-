#!/usr/bin/env python3
"""Validate the exact-scope ML-DEV-BUDGETED-001 compute approval."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/ml_dev_budgeted_001_compute_20260921.json"
PROTOCOL_HASHES = REPO_ROOT / "research/ml_extension/protocol_hashes.json"
FORMAL_DIR = REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921"
LOCKED_MANIFEST = REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
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


class ApprovalValidationError(ValueError):
    """Raised when the exact-scope approval is missing or stale."""


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
        raise ApprovalValidationError(f"cannot read JSON artifact {path}: {exc}") from exc


def repo_relative_path(value: object, context: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalValidationError(f"{context} must be a non-empty path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ApprovalValidationError(f"{context} must be repository-relative")
    target = REPO_ROOT / path
    if not target.is_file():
        raise ApprovalValidationError(f"{context} does not exist: {value}")
    return target


def require_string(mapping: object, key: str, context: str) -> str:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ApprovalValidationError(f"{context}.{key} must be a non-empty string")
    return value


def require_list(mapping: object, key: str, context: str) -> list[str]:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ApprovalValidationError(f"{context}.{key} must be a non-empty list of strings")
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


def validate_approval(path: str | Path = APPROVAL_PATH) -> dict[str, Any]:
    raw = read_json(Path(path))
    if not isinstance(raw, dict):
        raise ApprovalValidationError("approval artifact must be a JSON object")
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
        "phase10_status",
        "stop_conditions",
        "execution_contract",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ApprovalValidationError("approval missing fields: " + ", ".join(missing))
    if raw["study_id"] != "ML-DEV-BUDGETED-001":
        raise ApprovalValidationError("approval is for a different study")
    if raw["approval_version"] != "ml-dev-budgeted-001-v1":
        raise ApprovalValidationError("unsupported approval version")
    for key in ("approved_by", "approved_at", "authorization_source"):
        require_string(raw, key, "approval")
    if "explicit user authorization" not in str(raw["authorization_source"]).casefold():
        raise ApprovalValidationError(
            "authorization_source must record explicit user authorization"
        )
    if raw["max_budget_usd"] != 8.0:
        raise ApprovalValidationError("max_budget_usd must be exactly 8.00")
    budget = raw["budget_control"]
    if not isinstance(budget, dict):
        raise ApprovalValidationError("budget_control must be an object")
    if budget.get("hard_cap_usd") != 8.0 or budget.get("runner_safety_stop_usd") != 7.75:
        raise ApprovalValidationError("budget caps must be 8.00 hard / 7.75 runner stop")
    if budget.get("no_silent_budget_widening") is not True:
        raise ApprovalValidationError("no_silent_budget_widening must be true")
    protocol = raw["protocol"]
    protocol_path = repo_relative_path(
        protocol.get("path") if isinstance(protocol, dict) else None, "protocol"
    )
    recorded_protocol = require_string(protocol, "sha256", "protocol")
    hashes = read_json(PROTOCOL_HASHES)
    current = hashes["files"]["research/ml_extension/protocol.yaml"]
    if recorded_protocol != EXPECTED_PROTOCOL_HASH or recorded_protocol != current:
        raise ApprovalValidationError("approval protocol hash is not the current frozen hash")
    if sha256_file(protocol_path) != recorded_protocol:
        raise ApprovalValidationError("approval protocol file hash does not match")

    dataset = raw["dataset"]
    if not isinstance(dataset, dict):
        raise ApprovalValidationError("dataset must be an object")
    for key in (
        "formal_train_manifest_path",
        "formal_validation_manifest_path",
        "formal_development_manifest_path",
    ):
        target = repo_relative_path(dataset.get(key), f"dataset.{key}")
        expected = EXPECTED_FORMAL_HASHES[target.name]
        if (
            dataset.get(key.replace("_path", "_sha256")) != expected
            or sha256_file(target) != expected
        ):
            raise ApprovalValidationError(f"dataset hash mismatch for {key}")
    if dataset.get("formal_record_set_sha256") != EXPECTED_RECORD_SET_SHA256:
        raise ApprovalValidationError("formal record-set hash is not the frozen value")
    locked = repo_relative_path(
        dataset.get("locked_test_manifest_path"), "dataset.locked_test_manifest_path"
    )
    if (
        dataset.get("locked_test_manifest_sha256") != EXPECTED_LOCKED_MANIFEST_SHA256
        or sha256_file(locked) != EXPECTED_LOCKED_MANIFEST_SHA256
    ):
        raise ApprovalValidationError("locked-test manifest hash changed")
    cache_path = repo_relative_path(
        dataset.get("cache_reuse_verification_path"), "dataset.cache_reuse_verification_path"
    )
    cache = read_json(cache_path)
    if cache.get("status") != "PASS_COMPATIBLE_CACHE_REUSE_56" or cache.get("record_count") != 56:
        raise ApprovalValidationError(
            "verified historical cache reuse artifact is not PASS for 56 rows"
        )
    if dataset.get("cache_reuse_verification_sha256") != sha256_file(cache_path):
        raise ApprovalValidationError("cache reuse verification hash does not match")

    git = raw["git"]
    approved_commit = require_string(git, "commit", "git")
    if approved_commit != current_commit():
        raise ApprovalValidationError(
            f"approval commit {approved_commit} is not current HEAD {current_commit()}"
        )
    model = raw["model"]
    expected_model = {
        "model_id": "evo2",
        "checkpoint": "evo2_7b",
        "revision": "4b509ec2a22d6de472659f908bcb0714265ad3a7",
        "assembly": "GRCh38",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
    }
    for key, expected in expected_model.items():
        if not isinstance(model, dict) or model.get(key) != expected:
            raise ApprovalValidationError(f"model.{key} is not the canonical value")
    gpu = raw["gpu"]
    if not isinstance(gpu, dict) or gpu.get("type") != "H100":
        raise ApprovalValidationError("GPU must be H100")
    allowed = require_list(raw, "allowed_workloads", "approval")
    excluded = " ".join(require_list(raw, "excluded_workloads", "approval")).casefold()
    for token in (
        "locked_test",
        "phase 14",
        "239992",
        "fine-tun",
        "context-length sweep",
        "gpn",
        "deployment",
        "publication",
    ):
        if token not in excluded:
            raise ApprovalValidationError(f"excluded_workloads must include {token!r}")
    if not any("4000" in item and "evo2" in item.casefold() for item in allowed):
        raise ApprovalValidationError(
            "allowed_workloads must include formal 4,000-row Evo2 scoring"
        )
    if raw["phase10_status"] != "DEFERRED_BY_COMPUTE":
        raise ApprovalValidationError("Phase 10 must remain DEFERRED_BY_COMPUTE")
    stops = require_list(raw, "stop_conditions", "approval")
    stop_text = " ".join(stops).casefold()
    for token in ("7.75", "8.00", "projected", "active paid", "schema", "provenance"):
        if token not in stop_text:
            raise ApprovalValidationError(f"stop_conditions must mention {token!r}")
    contract = raw["execution_contract"]
    if not isinstance(contract, dict):
        raise ApprovalValidationError("execution_contract must be an object")
    if set(contract.get("cohort_splits", [])) != {"TRAIN", "VALIDATION"}:
        raise ApprovalValidationError("execution must be restricted to TRAIN and VALIDATION")
    if (
        contract.get("locked_test_access") != "prohibited"
        or contract.get("labels_remote_transport") != "prohibited"
    ):
        raise ApprovalValidationError("locked-test access and remote labels must be prohibited")
    if contract.get("formal_total") != 4_000 or contract.get("new_evo2_maximum") != 3_944:
        raise ApprovalValidationError("formal workload counts are not exact")
    return raw


def main() -> int:
    approval = validate_approval()
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
                "study_id": approval["study_id"],
                "max_budget_usd": approval["max_budget_usd"],
                "runner_safety_stop_usd": approval["budget_control"]["runner_safety_stop_usd"],
                "git_commit": approval["git"]["commit"],
                "protocol_hash": approval["protocol"]["sha256"],
                "formal_record_set_sha256": approval["dataset"]["formal_record_set_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

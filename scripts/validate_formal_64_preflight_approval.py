#!/usr/bin/env python3
"""Validate the exact, formal-manifest-only 64-row Evo2 preflight approval."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/formal_64_preflight_20260921.json"
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
EXPECTED_PREFLIGHT_SEED = "ML-DEV-BUDGETED-001|FORMAL-64-PREFLIGHT|2026-09-21|sha256-v1"


class FormalPreflightApprovalError(ValueError):
    """Raised when the formal 64-row approval is missing or stale."""


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
        raise FormalPreflightApprovalError(f"cannot read JSON artifact {path}: {exc}") from exc


def repo_path(value: object, context: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise FormalPreflightApprovalError(f"{context} must be a non-empty path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise FormalPreflightApprovalError(f"{context} must be repository-relative")
    target = REPO_ROOT / path
    if not target.is_file():
        raise FormalPreflightApprovalError(f"{context} does not exist: {value}")
    return target


def required_string(mapping: object, key: str, context: str) -> str:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise FormalPreflightApprovalError(f"{context}.{key} must be a non-empty string")
    return value


def required_list(mapping: object, key: str, context: str) -> list[str]:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise FormalPreflightApprovalError(f"{context}.{key} must be a non-empty list of strings")
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


def validate_approval(path: str | Path = DEFAULT_APPROVAL_PATH) -> dict[str, Any]:
    approval = read_json(Path(path))
    if not isinstance(approval, dict):
        raise FormalPreflightApprovalError("approval artifact must be a JSON object")
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
        "preflight",
    }
    missing = sorted(required.difference(approval))
    if missing:
        raise FormalPreflightApprovalError("approval missing fields: " + ", ".join(missing))
    if approval["study_id"] != "ML-DEV-BUDGETED-001":
        raise FormalPreflightApprovalError("approval is for a different study")
    if approval["approval_version"] != "formal-64-preflight-v1":
        raise FormalPreflightApprovalError("unsupported formal preflight approval version")
    for key in ("approved_by", "approved_at", "authorization_source"):
        required_string(approval, key, "approval")
    if "explicit user authorization" not in str(approval["authorization_source"]).casefold():
        raise FormalPreflightApprovalError(
            "authorization_source must record explicit user authorization"
        )
    if approval["max_budget_usd"] != 0.75:
        raise FormalPreflightApprovalError("max_budget_usd must be exactly 0.75")
    budget = approval["budget_control"]
    if not isinstance(budget, dict):
        raise FormalPreflightApprovalError("budget_control must be an object")
    if budget.get("hard_cap_usd") != 0.75 or budget.get("runner_safety_stop_usd") != 0.65:
        raise FormalPreflightApprovalError("budget caps must be 0.75 hard / 0.65 runner stop")
    if budget.get("no_silent_budget_widening") is not True:
        raise FormalPreflightApprovalError("no_silent_budget_widening must be true")

    protocol = approval["protocol"]
    protocol_path = repo_path(
        protocol.get("path") if isinstance(protocol, dict) else None, "protocol"
    )
    if (
        not isinstance(protocol, dict)
        or protocol.get("sha256") != EXPECTED_PROTOCOL_HASH
        or sha256_file(protocol_path) != EXPECTED_PROTOCOL_HASH
    ):
        raise FormalPreflightApprovalError("approval protocol hash is not the frozen value")

    dataset = approval["dataset"]
    if not isinstance(dataset, dict):
        raise FormalPreflightApprovalError("dataset must be an object")
    for key, expected in EXPECTED_FORMAL_HASHES.items():
        path_key = next(
            key_name
            for key_name in (
                "formal_train_manifest_path",
                "formal_validation_manifest_path",
                "formal_development_manifest_path",
            )
            if key_name.removesuffix("_path") + ".json" == key
        )
        target = repo_path(dataset.get(path_key), f"dataset.{path_key}")
        hash_key = path_key.removesuffix("_path") + "_sha256"
        if dataset.get(hash_key) != expected or sha256_file(target) != expected:
            raise FormalPreflightApprovalError(f"dataset hash mismatch for {path_key}")
    if dataset.get("formal_record_set_sha256") != EXPECTED_RECORD_SET_SHA256:
        raise FormalPreflightApprovalError("formal record-set hash is not frozen")
    locked = repo_path(
        dataset.get("locked_test_manifest_path"), "dataset.locked_test_manifest_path"
    )
    if (
        dataset.get("locked_test_manifest_sha256") != EXPECTED_LOCKED_MANIFEST_SHA256
        or sha256_file(locked) != EXPECTED_LOCKED_MANIFEST_SHA256
    ):
        raise FormalPreflightApprovalError("locked-test manifest hash changed")
    cache_path = repo_path(
        dataset.get("cache_reuse_verification_path"),
        "dataset.cache_reuse_verification_path",
    )
    if dataset.get("cache_reuse_verification_path") != EXPECTED_CACHE_REUSE_ARTIFACT:
        raise FormalPreflightApprovalError("cache reuse artifact path is not canonical")
    cache = read_json(cache_path)
    if (
        cache.get("status") != "PASS_COMPATIBLE_CACHE_REUSE_56"
        or cache.get("record_count") != 56
        or dataset.get("cache_reuse_verification_sha256") != EXPECTED_CACHE_REUSE_SHA256
        or sha256_file(cache_path) != EXPECTED_CACHE_REUSE_SHA256
    ):
        raise FormalPreflightApprovalError("verified 56-row cache reuse artifact is not current")

    git = approval["git"]
    if not isinstance(git, dict) or git.get("commit") != current_commit():
        raise FormalPreflightApprovalError(
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
            raise FormalPreflightApprovalError(f"model.{key} is not canonical")
    gpu = approval["gpu"]
    if not isinstance(gpu, dict) or gpu.get("type") != "H100":
        raise FormalPreflightApprovalError("GPU must be H100")

    allowed = required_list(approval, "allowed_workloads", "approval")
    if not any("64" in item and "evo2" in item.casefold() for item in allowed):
        raise FormalPreflightApprovalError(
            "allowed workloads must include the 64-row Evo2 preflight"
        )
    excluded = " ".join(required_list(approval, "excluded_workloads", "approval")).casefold()
    for token in (
        "4000",
        "nt/caduceus",
        "locked_test",
        "phase 14",
        "fine-tun",
        "context",
        "deployment",
        "release",
    ):
        if token not in excluded:
            raise FormalPreflightApprovalError(f"excluded_workloads must include {token!r}")
    if approval.get("phase10_status") != "DEFERRED_BY_COMPUTE":
        raise FormalPreflightApprovalError("Phase 10 must remain DEFERRED_BY_COMPUTE")
    stop_text = " ".join(required_list(approval, "stop_conditions", "approval")).casefold()
    for token in ("0.65", "0.75", "schema", "provenance", "active paid"):
        if token not in stop_text:
            raise FormalPreflightApprovalError(f"stop conditions must mention {token!r}")

    contract = approval["execution_contract"]
    if not isinstance(contract, dict):
        raise FormalPreflightApprovalError("execution_contract must be an object")
    if contract.get("sample_size") != 64 or contract.get("formal_total") != 4000:
        raise FormalPreflightApprovalError("formal preflight counts are not 64 of 4,000")
    if set(contract.get("cohort_splits", [])) != {"TRAIN", "VALIDATION"}:
        raise FormalPreflightApprovalError("execution must be restricted to TRAIN and VALIDATION")
    if (
        contract.get("locked_test_access") != "prohibited"
        or contract.get("labels_remote_transport") != "prohibited"
        or contract.get("selection_uses_labels") is not False
        or contract.get("selection_uses_predictions") is not False
    ):
        raise FormalPreflightApprovalError("preflight leakage boundaries are not fail-closed")
    if contract.get("selection_seed") != EXPECTED_PREFLIGHT_SEED:
        raise FormalPreflightApprovalError("preflight selection seed is not frozen")
    if "sha256(normalized_variant_id|selection_seed)" not in str(
        contract.get("selection_method", "")
    ).casefold():
        raise FormalPreflightApprovalError("preflight selection is not the approved hash rule")

    preflight = approval["preflight"]
    if not isinstance(preflight, dict) or preflight.get("sample_size") != 64:
        raise FormalPreflightApprovalError("preflight metadata must declare sample_size 64")
    for key in ("sample_artifact", "gate_artifact", "provenance_artifact"):
        value = preflight.get(key)
        if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
            raise FormalPreflightApprovalError(f"preflight.{key} must be repository-relative")
    provenance_path = repo_path(
        preflight["provenance_artifact"], "preflight.provenance_artifact"
    )
    provenance = read_json(provenance_path)
    if provenance.get("revision_reconciliation", {}).get("status") != "PASS":
        raise FormalPreflightApprovalError("model provenance reconciliation is not PASS")
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
                "git_commit": approval["git"]["commit"],
                "selection_seed": approval["execution_contract"]["selection_seed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

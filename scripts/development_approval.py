"""Validation for the explicit bounded Phase 6/7 development approval.

This lives in the script layer so the established full-run cost-policy model
remains strict and cannot accept a development artifact by accident.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_APPROVAL_VERSION = "phase6-phase7-development-v1"
EXPECTED_PROTOCOL_HASH = "39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3"
EXPECTED_BUDGET_USD = 5.0
EXPECTED_MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"


class DevelopmentApprovalError(ValueError):
    """Raised when the bounded development approval is not current and complete."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_split_hash(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _mapping_string(mapping: object, key: str, context: str) -> str:
    if not isinstance(mapping, dict):
        raise DevelopmentApprovalError(f"{context} must be an object")
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DevelopmentApprovalError(f"{context}.{key} must be a non-empty string")
    return value


def _path_from_artifact(repo_root: Path, value: str, context: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise DevelopmentApprovalError(f"{context} is not a safe repository-relative path")
    path = repo_root / relative
    if not path.is_file():
        raise DevelopmentApprovalError(f"{context} does not exist: {value}")
    return path


def _require_list(document: object, key: str) -> list[str]:
    value = document.get(key) if isinstance(document, dict) else None
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise DevelopmentApprovalError(f"{key} must be a non-empty list of strings")
    return value


def validate_development_approval(
    approval_path: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Validate the approval, its current hashes, and its split-level hashes."""
    target = Path(approval_path)
    root = Path(repo_root)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentApprovalError(f"cannot read approval artifact {target}: {exc}") from exc
    if not isinstance(raw, dict):
        raise DevelopmentApprovalError("approval artifact must be a JSON object")

    required = {
        "artifact_id",
        "approval_version",
        "approved_by",
        "approved_at",
        "authorization_source",
        "max_budget_usd",
        "budget_control",
        "protocol",
        "dataset",
        "train_validation_hashes",
        "model",
        "allowed_workloads",
        "excluded_workloads",
        "phase10_status",
        "stop_conditions",
        "execution_contract",
        "git",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise DevelopmentApprovalError(f"approval artifact is missing fields: {', '.join(missing)}")
    if raw["approval_version"] != EXPECTED_APPROVAL_VERSION:
        raise DevelopmentApprovalError(
            "approval artifact version is not the bounded development version"
        )
    identity_fields = ("approved_by", "approved_at", "authorization_source")
    if not all(
        isinstance(raw[key], str) and raw[key].strip() for key in identity_fields
    ):
        raise DevelopmentApprovalError("approval identity and timestamp fields must be non-empty")
    if raw["max_budget_usd"] != EXPECTED_BUDGET_USD:
        raise DevelopmentApprovalError("development approval budget must be exactly 5.00 USD")

    budget = raw["budget_control"]
    if not isinstance(budget, dict):
        raise DevelopmentApprovalError("budget_control must be an object")
    if budget.get("approval_cap_usd") != EXPECTED_BUDGET_USD:
        raise DevelopmentApprovalError("approval cap does not match the authorized 5.00 USD")
    if budget.get("stop_if_projected_additional_usd_exceeds") != EXPECTED_BUDGET_USD:
        raise DevelopmentApprovalError("projected-spend stop does not match the authorized cap")
    if budget.get("no_silent_budget_widening") is not True:
        raise DevelopmentApprovalError("no_silent_budget_widening must be true")

    protocol = raw["protocol"]
    protocol_path = _path_from_artifact(
        root, _mapping_string(protocol, "path", "protocol"), "protocol.path"
    )
    if _mapping_string(protocol, "path", "protocol") != "research/ml_extension/protocol.yaml":
        raise DevelopmentApprovalError("approval must bind research/ml_extension/protocol.yaml")
    recorded_protocol_hash = _mapping_string(protocol, "sha256", "protocol")
    if recorded_protocol_hash != EXPECTED_PROTOCOL_HASH:
        raise DevelopmentApprovalError("approval protocol hash is not the current frozen hash")
    if _sha256_file(protocol_path) != recorded_protocol_hash:
        raise DevelopmentApprovalError("approval protocol file hash does not match the artifact")

    dataset = raw["dataset"]
    if not isinstance(dataset, dict):
        raise DevelopmentApprovalError("dataset must be an object")
    expected_dataset_paths = (
        ("development_manifest_path", "development_manifest_sha256"),
        ("generated_split_manifest_path", "generated_split_manifest_sha256"),
        ("authoritative_split_summary_path", "authoritative_split_summary_sha256"),
        (
            "authoritative_locked_test_cohort_manifest_path",
            "authoritative_locked_test_cohort_manifest_sha256",
        ),
    )
    dataset_files: dict[str, Path] = {}
    for path_key, hash_key in expected_dataset_paths:
        path_value = _mapping_string(dataset, path_key, "dataset")
        file_path = _path_from_artifact(root, path_value, f"dataset.{path_key}")
        recorded_hash = _mapping_string(dataset, hash_key, "dataset")
        if _sha256_file(file_path) != recorded_hash:
            raise DevelopmentApprovalError(f"dataset hash mismatch for {path_key}")
        dataset_files[path_key] = file_path
    if dataset.get("locked_test_excluded_from_development") is not True:
        raise DevelopmentApprovalError("locked_test_excluded_from_development must be true")

    try:
        generated = json.loads(dataset_files["development_manifest_path"].read_text())
        records = generated["records"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise DevelopmentApprovalError(f"cannot inspect development records: {exc}") from exc
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise DevelopmentApprovalError("development manifest records must be objects")
    if generated.get("split_hash") != dataset.get("semantic_split_hash"):
        raise DevelopmentApprovalError("semantic split hash does not match the generated manifest")
    if generated.get("source_manifest_hash") != dataset.get("development_source_manifest_hash"):
        raise DevelopmentApprovalError("source manifest hash does not match the generated manifest")

    split_hashes = raw["train_validation_hashes"]
    if not isinstance(split_hashes, dict):
        raise DevelopmentApprovalError("train_validation_hashes must be an object")
    for split in ("TRAIN", "VALIDATION"):
        expected = split_hashes.get(split)
        if not isinstance(expected, dict):
            raise DevelopmentApprovalError(f"missing {split} record-set hash")
        split_records = [row for row in records if row.get("split") == split]
        if expected.get("count") != len(split_records):
            raise DevelopmentApprovalError(f"{split} count does not match the generated manifest")
        if expected.get("record_set_sha256") != _canonical_split_hash(split_records):
            raise DevelopmentApprovalError(
                f"{split} record-set hash does not match the generated manifest"
            )

    model = raw["model"]
    for key, expected in {
        "model_id": "evo2",
        "checkpoint": "evo2_7b",
        "revision": EXPECTED_MODEL_REVISION,
        "gpu": "H100",
        "modal_environment": "evovariant-tr",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
    }.items():
        if not isinstance(model, dict) or model.get(key) != expected:
            raise DevelopmentApprovalError(f"model.{key} is not the approved canonical value")
    _require_list(raw, "allowed_workloads")
    excluded = " ".join(_require_list(raw, "excluded_workloads")).casefold()
    if "locked_test" not in excluded or "phase 14" not in excluded:
        raise DevelopmentApprovalError("approval must exclude locked-test and Phase 14 work")
    if raw["phase10_status"] != "DEFERRED":
        raise DevelopmentApprovalError("Phase 10 must remain DEFERRED")
    _require_list(raw, "stop_conditions")

    contract = raw["execution_contract"]
    if not isinstance(contract, dict):
        raise DevelopmentApprovalError("execution_contract must be an object")
    if set(contract.get("cohort_splits", [])) != {"TRAIN", "VALIDATION"}:
        raise DevelopmentApprovalError(
            "execution contract must restrict work to TRAIN and VALIDATION"
        )
    if contract.get("locked_test_access") != "prohibited":
        raise DevelopmentApprovalError("locked_test_access must be prohibited")
    if contract.get("labels_remote_transport") != "prohibited":
        raise DevelopmentApprovalError("labels_remote_transport must be prohibited")
    return raw

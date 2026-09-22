#!/usr/bin/env python3
"""Validate the exact, current-HEAD, one-shot Phase 14 approval."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.analysis_plans import freeze_analysis_config  # noqa: E402

DEFAULT_APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase14_locked_evo2_20260922.json"
EXPECTED_APPROVAL_VERSION = "phase14-locked-v1"
EXPECTED_HARD_CAP_USD = 2.75
EXPECTED_SAFETY_STOP_USD = 2.50
EXPECTED_CONFIG_SHA256 = "01cd0569c4d7177a838506b70a050c5b4cbc401d5fa2ea2c6c37c46719f623a3"
EXPECTED_MODEL_ARTIFACT_SHA256 = "f42de3bc5e803ee2c0fea2a2159c9b6a3c6ef69fba6ed51c5f7b3bd708d4b043"
EXPECTED_CALIBRATION_ARTIFACT_SHA256 = (
    "bf1f9078386f35619d5188eabb07e8345f168cf0717565180cb0bca4c42520a3"
)
EXPECTED_ML_PROTOCOL_SHA256 = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
EXPECTED_RESEARCH_PROTOCOL_SHA256 = (
    "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"
)
EXPECTED_TRAIN_MANIFEST_SHA256 = "32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1"
EXPECTED_VALIDATION_MANIFEST_SHA256 = (
    "b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b"
)
EXPECTED_DEVELOPMENT_MANIFEST_SHA256 = (
    "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
)
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"


class Phase14ApprovalError(ValueError):
    """Raised when the Phase 14 approval is missing or stale."""


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
        raise Phase14ApprovalError(f"cannot read JSON artifact {path}: {exc}") from exc


def repo_path(value: object, context: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise Phase14ApprovalError(f"{context} must be a non-empty path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise Phase14ApprovalError(f"{context} must be repository-relative")
    target = REPO_ROOT / path
    if not target.is_file():
        raise Phase14ApprovalError(f"{context} does not exist: {value}")
    return target


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def required_string(mapping: object, key: str, context: str) -> str:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise Phase14ApprovalError(f"{context}.{key} must be a non-empty string")
    return value


def required_list(mapping: object, key: str, context: str) -> list[str]:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise Phase14ApprovalError(f"{context}.{key} must be a non-empty list of strings")
    return value


def require_hash(path_value: object, expected: str, context: str) -> Path:
    path = repo_path(path_value, f"{context}.path")
    if sha256_file(path) != expected:
        raise Phase14ApprovalError(f"{context} hash does not match the frozen value")
    return path


def validate_approval(path: str | Path = DEFAULT_APPROVAL_PATH) -> dict[str, Any]:
    raw = read_json(Path(path))
    if not isinstance(raw, dict):
        raise Phase14ApprovalError("approval must be a JSON object")
    required = {
        "artifact_id",
        "study_id",
        "approval_version",
        "approved_by",
        "approved_at",
        "authorization_source",
        "max_budget_usd",
        "budget_control",
        "protocols",
        "dataset",
        "git",
        "model",
        "gpu",
        "frozen_config",
        "allowed_workloads",
        "excluded_workloads",
        "stop_conditions",
        "execution_contract",
        "cost_baseline",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise Phase14ApprovalError("approval missing fields: " + ", ".join(missing))
    if raw["study_id"] != "ML-DEV-BUDGETED-001":
        raise Phase14ApprovalError("approval is for a different study")
    if raw["approval_version"] != EXPECTED_APPROVAL_VERSION:
        raise Phase14ApprovalError("unsupported Phase 14 approval version")
    for key in ("approved_by", "approved_at", "authorization_source"):
        required_string(raw, key, "approval")
    if "explicit user authorization" not in raw["authorization_source"].casefold():
        raise Phase14ApprovalError("authorization_source must record explicit user authorization")
    if raw["max_budget_usd"] != EXPECTED_HARD_CAP_USD:
        raise Phase14ApprovalError("max_budget_usd must be exactly 2.75")

    budget = raw["budget_control"]
    if not isinstance(budget, dict):
        raise Phase14ApprovalError("budget_control must be an object")
    if budget.get("hard_cap_usd") != EXPECTED_HARD_CAP_USD:
        raise Phase14ApprovalError("hard cap must be exactly 2.75")
    if budget.get("safety_stop_usd") != EXPECTED_SAFETY_STOP_USD:
        raise Phase14ApprovalError("safety stop must be exactly 2.50")
    if budget.get("no_silent_budget_widening") is not True:
        raise Phase14ApprovalError("no_silent_budget_widening must be true")

    protocols = raw["protocols"]
    if not isinstance(protocols, dict):
        raise Phase14ApprovalError("protocols must be an object")
    protocol_specs = {
        "research": ("research/protocol/protocol.yaml", EXPECTED_RESEARCH_PROTOCOL_SHA256),
        "ml_extension": ("research/ml_extension/protocol.yaml", EXPECTED_ML_PROTOCOL_SHA256),
    }
    for name, (expected_path, expected_hash) in protocol_specs.items():
        spec = protocols.get(name)
        if not isinstance(spec, dict) or spec.get("path") != expected_path:
            raise Phase14ApprovalError(f"protocol {name} path is not canonical")
        require_hash(spec.get("path"), expected_hash, f"protocols.{name}")
        if spec.get("sha256") != expected_hash:
            raise Phase14ApprovalError(f"protocol {name} hash is not canonical")

    frozen = raw["frozen_config"]
    if not isinstance(frozen, dict):
        raise Phase14ApprovalError("frozen_config must be an object")
    config_path = require_hash(
        frozen.get("path"), EXPECTED_CONFIG_SHA256, "frozen_config"
    )
    if frozen.get("sha256") != EXPECTED_CONFIG_SHA256:
        raise Phase14ApprovalError("frozen config hash is not canonical")
    config = read_json(config_path)
    if freeze_analysis_config(config).sha256 != EXPECTED_CONFIG_SHA256:
        raise Phase14ApprovalError("frozen config content hash does not replay")
    if (
        config.get("selection_closed") is not True
        or config.get("locked_test_evaluated") is not False
    ):
        raise Phase14ApprovalError("frozen config selection/locked boundary is invalid")
    if config.get("required_remote_tracks") != ["evo2"]:
        raise Phase14ApprovalError("frozen config requires an unexpected remote track")
    if config.get("model", {}).get("artifact_sha256") != EXPECTED_MODEL_ARTIFACT_SHA256:
        raise Phase14ApprovalError("frozen config model artifact binding is stale")
    model_artifact = require_hash(
        config.get("model", {}).get("artifact_path"),
        EXPECTED_MODEL_ARTIFACT_SHA256,
        "frozen_config.model",
    )
    if config.get("calibration", {}).get("artifact_sha256") != EXPECTED_CALIBRATION_ARTIFACT_SHA256:
        raise Phase14ApprovalError("frozen config calibration artifact binding is stale")
    require_hash(
        config.get("calibration", {}).get("artifact_path"),
        EXPECTED_CALIBRATION_ARTIFACT_SHA256,
        "frozen_config.calibration",
    )

    dataset = raw["dataset"]
    if not isinstance(dataset, dict):
        raise Phase14ApprovalError("dataset must be an object")
    manifest_specs = {
        "formal_train": EXPECTED_TRAIN_MANIFEST_SHA256,
        "formal_validation": EXPECTED_VALIDATION_MANIFEST_SHA256,
        "formal_development": EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
    }
    for name, expected_hash in manifest_specs.items():
        spec = dataset.get(name)
        if not isinstance(spec, dict) or spec.get("sha256") != expected_hash:
            raise Phase14ApprovalError(f"dataset.{name} hash is not canonical")
        require_hash(spec.get("path"), expected_hash, f"dataset.{name}")
    if dataset.get("formal_record_set_sha256") != EXPECTED_RECORD_SET_SHA256:
        raise Phase14ApprovalError("formal record-set hash is not canonical")
    locked = dataset.get("locked_test")
    if not isinstance(locked, dict) or locked.get("sha256") != EXPECTED_LOCKED_MANIFEST_SHA256:
        raise Phase14ApprovalError("locked-test manifest hash is not canonical")
    require_hash(locked.get("path"), EXPECTED_LOCKED_MANIFEST_SHA256, "dataset.locked_test")
    if locked.get("expected_count") != 946:
        raise Phase14ApprovalError("locked-test cohort must contain 946 rows")
    if locked.get("expected_label_counts") != {"0": 536, "1": 410}:
        raise Phase14ApprovalError("locked-test label counts are not the frozen 536/410 cohort")
    if locked.get("labels_read_before_raw_inference") is not False:
        raise Phase14ApprovalError("approval must prohibit locked-label reads before raw inference")

    git = raw["git"]
    if not isinstance(git, dict) or git.get("commit") != current_commit():
        raise Phase14ApprovalError(
            f"approval commit {git.get('commit') if isinstance(git, dict) else None} "
            f"is not current HEAD {current_commit()}"
        )

    model = raw["model"]
    expected_model = {
        "model_id": "evo2_7b",
        "checkpoint": "evo2_7b",
        "revision": EXPECTED_MODEL_REVISION,
        "assembly": "GRCh38",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
    }
    for key, expected in expected_model.items():
        if not isinstance(model, dict) or model.get(key) != expected:
            raise Phase14ApprovalError(f"model.{key} is not canonical")
    gpu = raw["gpu"]
    if not isinstance(gpu, dict) or gpu.get("type") != "H100" or gpu.get("count") != 1:
        raise Phase14ApprovalError("GPU must be one H100")

    allowed = " ".join(required_list(raw, "allowed_workloads", "approval")).casefold()
    if "phase 14" not in allowed or "evo2" not in allowed or "one-shot" not in allowed:
        raise Phase14ApprovalError("allowed workload is not the one-shot Evo2 Phase 14 scope")
    excluded = " ".join(required_list(raw, "excluded_workloads", "approval")).casefold()
    for token in (
        "nt",
        "caduceus",
        "fine-tun",
        "hpo",
        "threshold",
        "calibration refit",
        "deployment",
        "release",
    ):
        if token not in excluded:
            raise Phase14ApprovalError(f"excluded workload must mention {token!r}")
    stops = " ".join(required_list(raw, "stop_conditions", "approval")).casefold()
    for token in ("2.50", "2.75", "no labels", "non-finite", "duplicate", "active container"):
        if token not in stops:
            raise Phase14ApprovalError(f"stop conditions must mention {token!r}")

    contract = raw["execution_contract"]
    if not isinstance(contract, dict):
        raise Phase14ApprovalError("execution_contract must be an object")
    expected_contract = {
        "locked_test_rows": 946,
        "remote_labels": "prohibited",
        "label_join": "after raw prediction artifact hash",
        "final_statistics": "one_shot",
        "retry_policy": "clearly_transient_shard_failures_only",
        "post_test_tuning": "prohibited",
    }
    for key, expected in expected_contract.items():
        if contract.get(key) != expected:
            raise Phase14ApprovalError(f"execution_contract.{key} is not fail-closed")

    baseline = raw["cost_baseline"]
    if not isinstance(baseline, dict) or baseline.get("active_containers") != 0:
        raise Phase14ApprovalError("cost baseline must prove zero active containers")
    for key in ("metered_cost_usd", "billed_cost_usd"):
        value = baseline.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise Phase14ApprovalError(f"cost_baseline.{key} must be finite")
        if value < 0:
            raise Phase14ApprovalError(f"cost_baseline.{key} cannot be negative")
    if not required_string(baseline, "captured_at_utc", "cost_baseline"):
        raise Phase14ApprovalError("cost baseline timestamp is required")

    return {**raw, "_config_path": str(config_path), "_model_artifact_path": str(model_artifact)}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_APPROVAL_PATH
    approval = validate_approval(path)
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval_artifact": str(path),
                "git_commit": approval["git"]["commit"],
                "config_sha256": approval["frozen_config"]["sha256"],
                "hard_cap_usd": approval["budget_control"]["hard_cap_usd"],
                "safety_stop_usd": approval["budget_control"]["safety_stop_usd"],
                "locked_test_rows": approval["dataset"]["locked_test"]["expected_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

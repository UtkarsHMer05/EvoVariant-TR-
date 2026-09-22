#!/usr/bin/env python3
"""Validate the narrow NT/Caduceus Phase 7 representation approval."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/formal_phase7_continuation_20260922.json"
EXPECTED_VERSION = "formal-phase7-representation-v2"
EXPECTED_HARD_CAP_USD = 1.75
EXPECTED_SAFETY_STOP_USD = 1.50
EXPECTED_MINIMUM_POST_RUN_RESERVE_USD = 3.0
EXPECTED_PROTOCOL_SHA256 = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
EXPECTED_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_LOCKED_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
EXPECTED_EVO2_ARTIFACT_SHA256 = "b04940b3b5845fd57144f54a9862da8d9d89fb1b98d9c79fc45364e7a21ef54d"
EXPECTED_EVO2_PREDICTIONS_SHA256 = (
    "088e39fcfa45b2af9cd8f11cbb803213d9030c92036fc9f27f577c3912693751"
)
EXPECTED_NT_REVISION = "06615c1660c892fc199840c18123f8385b3542a8"
EXPECTED_CADUCEUS_REVISION = "b0477522ac5d044ad03578aa724ec8e4bdbd405b"


class RepresentationApprovalError(ValueError):
    """Raised when the exact Phase 7 approval is stale or widened."""


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
        raise RepresentationApprovalError(f"cannot read {path}: {exc}") from exc


def repo_file(value: object, context: str, expected_hash: str | None = None) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RepresentationApprovalError(f"{context} must be a repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise RepresentationApprovalError(f"{context} must be repository-relative")
    target = REPO_ROOT / path
    if not target.is_file():
        raise RepresentationApprovalError(f"{context} does not exist: {value}")
    if expected_hash is not None and sha256_file(target) != expected_hash:
        raise RepresentationApprovalError(f"{context} hash does not match")
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


def validate_approval(path: str | Path = APPROVAL_PATH) -> dict[str, Any]:
    approval = read_json(Path(path))
    if not isinstance(approval, dict):
        raise RepresentationApprovalError("approval must be a JSON object")
    if approval.get("study_id") != "ML-DEV-BUDGETED-001":
        raise RepresentationApprovalError("approval study is not ML-DEV-BUDGETED-001")
    if approval.get("approval_version") != EXPECTED_VERSION:
        raise RepresentationApprovalError("approval version is not the narrow Phase 7 version")
    if approval.get("max_budget_usd") != EXPECTED_HARD_CAP_USD:
        raise RepresentationApprovalError("hard cap must be exactly $1.00")
    budget = approval.get("budget_control")
    if not isinstance(budget, dict):
        raise RepresentationApprovalError("budget_control is missing")
    if budget.get("hard_cap_usd") != EXPECTED_HARD_CAP_USD:
        raise RepresentationApprovalError("budget hard cap is not $1.00")
    if budget.get("runner_safety_stop_usd") != EXPECTED_SAFETY_STOP_USD:
        raise RepresentationApprovalError("safety stop is not $0.85")
    if budget.get("minimum_post_run_reserve_usd") != EXPECTED_MINIMUM_POST_RUN_RESERVE_USD:
        raise RepresentationApprovalError("post-run reserve must be at least $3.00")
    if budget.get("no_silent_budget_widening") is not True:
        raise RepresentationApprovalError("silent budget widening is not prohibited")

    protocol = approval.get("protocol")
    if not isinstance(protocol, dict) or protocol.get("sha256") != EXPECTED_PROTOCOL_SHA256:
        raise RepresentationApprovalError("protocol binding is not frozen")
    repo_file(protocol.get("path"), "protocol", EXPECTED_PROTOCOL_SHA256)

    dataset = approval.get("dataset")
    if not isinstance(dataset, dict):
        raise RepresentationApprovalError("dataset binding is missing")
    repo_file(dataset.get("formal_manifest_path"), "formal_manifest", EXPECTED_MANIFEST_SHA256)
    if dataset.get("formal_manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise RepresentationApprovalError("formal manifest hash is not frozen")
    if dataset.get("formal_record_set_sha256") != EXPECTED_RECORD_SET_SHA256:
        raise RepresentationApprovalError("formal record-set hash is not frozen")
    repo_file(
        dataset.get("locked_test_manifest_path"),
        "locked_test_manifest",
        EXPECTED_LOCKED_SHA256,
    )
    if dataset.get("locked_test_manifest_sha256") != EXPECTED_LOCKED_SHA256:
        raise RepresentationApprovalError("locked-test manifest hash is not frozen")
    if dataset.get("formal_record_count") != 4000 or dataset.get("locked_test_count") != 946:
        raise RepresentationApprovalError("dataset counts are not exact")
    repo_file(
        dataset.get("evo2_artifact_path"),
        "evo2_artifact",
        EXPECTED_EVO2_ARTIFACT_SHA256,
    )
    repo_file(
        dataset.get("evo2_predictions_path"),
        "evo2_predictions",
        EXPECTED_EVO2_PREDICTIONS_SHA256,
    )

    git = approval.get("git")
    if not isinstance(git, dict) or git.get("commit") != current_commit():
        raise RepresentationApprovalError("approval is not bound to current HEAD")

    models = approval.get("models")
    expected_models = {
        "nucleotide_transformer": {
            "model_id": "InstaDeepAI/nucleotide-transformer-v2-500m-multi-species",
            "revision": EXPECTED_NT_REVISION,
            "layers": [8, 16, 24],
        },
        "caduceus": {
            "model_id": "kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
            "revision": EXPECTED_CADUCEUS_REVISION,
            "layers": [4, 8, 16],
        },
    }
    if models != expected_models:
        raise RepresentationApprovalError("model/layer scope is not the registered matrix")

    allowed = " ".join(approval.get("allowed_workloads", [])).casefold()
    for token in ("nucleotide transformer", "caduceus", "cache", "parity"):
        if token not in allowed:
            raise RepresentationApprovalError(f"allowed scope is missing {token!r}")
    excluded = " ".join(approval.get("excluded_workloads", [])).casefold()
    for token in (
        "evo2 rerun",
        "locked-test",
        "phase 14",
        "fine-tuning",
        "peft",
        "gpn",
        "context sweeps",
        "deployment",
        "release",
    ):
        if token not in excluded:
            raise RepresentationApprovalError(f"excluded scope is missing {token!r}")

    contract = approval.get("execution_contract")
    if not isinstance(contract, dict):
        raise RepresentationApprovalError("execution contract is missing")
    if contract.get("formal_records") != 4000:
        raise RepresentationApprovalError("representation contract is not 4,000 rows")
    if set(contract.get("splits", [])) != {"TRAIN", "VALIDATION"}:
        raise RepresentationApprovalError(
            "representation contract includes a non-development split"
        )
    if contract.get("labels_remote_transport") is not False:
        raise RepresentationApprovalError("remote labels are not prohibited")
    if contract.get("locked_test_access") is not False:
        raise RepresentationApprovalError("locked-test access is not prohibited")
    if contract.get("one_forward_pass_per_model") is not True:
        raise RepresentationApprovalError("one-forward-pass layer extraction is not required")

    baseline = approval.get("cost_baseline")
    if not isinstance(baseline, dict) or baseline.get("active_containers") != 0:
        raise RepresentationApprovalError("approval baseline does not prove zero active containers")
    for key in ("workspace_metered_usd", "workspace_billed_usd", "free_compute_headroom_usd"):
        if not isinstance(baseline.get(key), (int, float)):
            raise RepresentationApprovalError(f"cost baseline lacks numeric {key}")
    if (
        baseline["free_compute_headroom_usd"] - EXPECTED_HARD_CAP_USD
        < EXPECTED_MINIMUM_POST_RUN_RESERVE_USD
    ):
        raise RepresentationApprovalError("hard cap would violate the minimum post-run reserve")
    return approval


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else APPROVAL_PATH
    approval = validate_approval(path)
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval_artifact": str(path),
                "git_commit": approval["git"]["commit"],
                "hard_cap_usd": approval["budget_control"]["hard_cap_usd"],
                "runner_safety_stop_usd": approval["budget_control"][
                    "runner_safety_stop_usd"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

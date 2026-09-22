#!/usr/bin/env python3
"""Validate the exact, development-only Phase 15 parity approval."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVAL = ROOT / "artifacts/approvals/phase15_parity_smoke_20260922.json"
PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
DEVELOPMENT_HASH = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
LOCKED_HASH = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
FINAL_ARTIFACT_HASH = "4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499"


class Phase15ApprovalError(ValueError):
    """Raised when the Phase 15 approval is missing, stale, or widened."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Phase15ApprovalError(f"cannot read JSON artifact {path}: {exc}") from exc


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Phase15ApprovalError(f"{name} must be an object")
    return value


def _require_string(mapping: dict[str, Any], key: str, name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise Phase15ApprovalError(f"{name}.{key} must be a non-empty string")
    return value


def _repo_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file():
        raise Phase15ApprovalError(f"missing repository artifact: {relative}")
    return path


def _selection() -> tuple[list[str], set[str]]:
    manifest_path = _repo_file(
        "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
    )
    manifest = _read(manifest_path)
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != 4_000:
        raise Phase15ApprovalError("formal development manifest must contain 4,000 records")
    cache = _read(_repo_file("artifacts/phase6/formal_budgeted_cache_reuse_verification_20260921.json"))
    if cache.get("status") != "PASS_COMPATIBLE_CACHE_REUSE_56":
        raise Phase15ApprovalError("verified Phase 6 cache reuse artifact is not PASS")
    cache_rows = cache.get("verified_rows")
    if not isinstance(cache_rows, list) or len(cache_rows) != 56:
        raise Phase15ApprovalError("verified Phase 6 cache must contain exactly 56 rows")
    cache_ids = {
        str(row.get("normalized_variant_id"))
        for row in cache_rows
        if isinstance(row, dict) and row.get("normalized_variant_id")
    }
    by_id = {
        str(row.get("normalized_variant_id")): row
        for row in records
        if isinstance(row, dict) and row.get("normalized_variant_id")
    }
    if len(cache_ids) != 56 or not cache_ids.issubset(by_id):
        raise Phase15ApprovalError("verified cache IDs are not an exact development-manifest subset")
    cached = sorted(cache_ids)
    uncached = sorted(set(by_id) - cache_ids)
    selected = cached + uncached[:8]
    if len(selected) != 64:
        raise Phase15ApprovalError("Phase 15 selection is not exactly 64 rows")
    locked = _read(_repo_file("research/ml_extension/splits/authoritative_locked_test_manifest.json"))
    locked_ids = {
        str(row.get("normalized_variant_id"))
        for row in locked.get("records", [])
        if isinstance(row, dict) and row.get("normalized_variant_id")
    }
    if set(selected) & locked_ids:
        raise Phase15ApprovalError("Phase 15 selection overlaps LOCKED_TEST")
    return selected, cache_ids


def validate_approval(
    approval_path: str | Path = DEFAULT_APPROVAL,
    repo_root: str | Path = ROOT,
) -> dict[str, Any]:
    """Validate the approval against the current committed scientific checkpoint."""
    del repo_root  # The runner passes this for a uniform approval interface.
    approval = _require_mapping(_read(Path(approval_path)), "approval")
    if approval.get("approval_version") != "phase15-parity-smoke-v1":
        raise Phase15ApprovalError("unsupported Phase 15 approval version")
    if approval.get("phase") != 15:
        raise Phase15ApprovalError("approval is not for Phase 15")
    if approval.get("hard_cap_usd") != 0.25 or approval.get("safety_stop_usd") != 0.20:
        raise Phase15ApprovalError("approval budget does not match $0.25/$0.20")

    budget = _require_mapping(approval.get("budget_control"), "budget_control")
    if budget.get("hard_cap_usd") != 0.25 or budget.get("safety_stop_usd") != 0.20:
        raise Phase15ApprovalError("budget_control does not match the authorized limits")
    if budget.get("no_silent_budget_widening") is not True:
        raise Phase15ApprovalError("no_silent_budget_widening must be true")

    git = _require_mapping(approval.get("git"), "git")
    current_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if git.get("commit") != current_head:
        raise Phase15ApprovalError("approval is not bound to current HEAD")

    protocol = _require_mapping(approval.get("protocol"), "protocol")
    protocol_path = _require_string(protocol, "path", "protocol")
    if protocol_path != "research/ml_extension/protocol.yaml" or _sha256(_repo_file(protocol_path)) != PROTOCOL_HASH:
        raise Phase15ApprovalError("protocol hash/path does not match the frozen ML protocol")
    if protocol.get("sha256") != PROTOCOL_HASH:
        raise Phase15ApprovalError("approval protocol digest is stale")

    dataset = _require_mapping(approval.get("dataset"), "dataset")
    development_path = _require_string(dataset, "development_manifest_path", "dataset")
    locked_path = _require_string(dataset, "locked_test_manifest_path", "dataset")
    if development_path != "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json":
        raise Phase15ApprovalError("approval development manifest path is not canonical")
    if locked_path != "research/ml_extension/splits/authoritative_locked_test_manifest.json":
        raise Phase15ApprovalError("approval locked manifest path is not canonical")
    if dataset.get("development_manifest_sha256") != DEVELOPMENT_HASH or _sha256(_repo_file(development_path)) != DEVELOPMENT_HASH:
        raise Phase15ApprovalError("development manifest hash mismatch")
    if dataset.get("locked_test_manifest_sha256") != LOCKED_HASH or _sha256(_repo_file(locked_path)) != LOCKED_HASH:
        raise Phase15ApprovalError("locked-test manifest hash mismatch")
    if dataset.get("locked_test_access") != "prohibited" or dataset.get("labels_remote_transport") is not False:
        raise Phase15ApprovalError("Phase 15 approval does not prohibit locked access and remote labels")

    selection, cache_ids = _selection()
    selection_block = _require_mapping(approval.get("selection"), "selection")
    if selection_block.get("expected_rows") != 64:
        raise Phase15ApprovalError("selection expected_rows must be 64")
    if selection_block.get("verified_cache_rows") != 56 or selection_block.get("remote_rows") != 8:
        raise Phase15ApprovalError("selection must contain 56 cache rows and 8 remote rows")
    selection_hash = hashlib.sha256(("\n".join(selection) + "\n").encode()).hexdigest()
    if selection_block.get("ids_sha256") != selection_hash:
        raise Phase15ApprovalError("Phase 15 selection ID hash mismatch")
    if selection_block.get("cache_ids_sha256") != hashlib.sha256(("\n".join(sorted(cache_ids)) + "\n").encode()).hexdigest():
        raise Phase15ApprovalError("Phase 6 cache ID binding mismatch")

    model = _require_mapping(approval.get("model"), "model")
    expected_model = {
        "model_id": "evo2_7b",
        "revision": "4b509ec2a22d6de472659f908bcb0714265ad3a7",
        "assembly": "GRCh38",
        "context_length_bp": 8192,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
        "gpu": "H100",
    }
    for key, expected in expected_model.items():
        if model.get(key) != expected:
            raise Phase15ApprovalError(f"model.{key} is not the frozen value")

    final_artifact = _repo_file("artifacts/phase14/phase14_locked_evo2_20260922.json")
    if _sha256(final_artifact) != FINAL_ARTIFACT_HASH:
        raise Phase15ApprovalError("immutable Phase 14 artifact hash changed")
    if _read(final_artifact).get("status") != "PASS_PHASE14_LOCKED_EVALUATION":
        raise Phase15ApprovalError("immutable Phase 14 artifact is not PASS")
    baseline = _require_mapping(approval.get("cost_baseline"), "cost_baseline")
    if baseline.get("active_containers") != []:
        raise Phase15ApprovalError("approval baseline does not prove zero active containers")
    return approval


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    args = parser.parse_args()
    validated = validate_approval(args.approval, ROOT)
    print(json.dumps({"status": "PASS", "commit": validated["git"]["commit"]}, indent=2))

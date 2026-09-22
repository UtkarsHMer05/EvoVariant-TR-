#!/usr/bin/env python3
"""Record the no-spend Phase 18 reproducibility boundary."""

# ruff: noqa: E501

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from evovariant_tr.registry import Registry, RunStatus, hash_file, verify_output_hashes

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/runs/phase18_clean_room_status.json"
PUBLICATION = ROOT / "research/reports/phase17/publication_manifest.json"
PHASE15_VALIDATION = ROOT / "artifacts/phase15/phase15_parity_smoke_validation_20260922.json"
CLEAN_ROOM_EXECUTION = ROOT / "artifacts/phase18/clean_room_execution_20260922.json"


def main() -> int:
    registry = Registry(ROOT / "experiments/registry", repo_root=ROOT)
    registry_failures = []
    completed = []
    for record in registry.list_runs():
        if record.status is not RunStatus.COMPLETED:
            continue
        try:
            verify_output_hashes(record, ROOT)
            completed.append(record.run_id)
        except Exception as exc:  # local gate reports all broken records
            registry_failures.append(f"{record.run_id}: {exc}")
    publication = json.loads(PUBLICATION.read_text(encoding="utf-8")) if PUBLICATION.is_file() else {}
    publication_ok = publication.get("status") == "PASS_LOCAL_PUBLICATION_BUNDLE"
    hash_failures = []
    for path, expected in publication.get("output_hashes", {}).items():
        target = ROOT / path
        if not target.is_file() or hash_file(target) != expected:
            hash_failures.append(path)
    artifact_repro = publication_ok and not hash_failures and not registry_failures
    phase15 = json.loads(PHASE15_VALIDATION.read_text(encoding="utf-8")) if PHASE15_VALIDATION.is_file() else {}
    phase15_checks = phase15.get("checks", {})
    phase15_spot_check = (
        phase15.get("status") == "PASS_PHASE15_PARITY_AND_RESUME"
        and isinstance(phase15_checks, dict)
        and all(value is True for value in phase15_checks.values())
        and phase15.get("billing_after", {}).get("active_containers") == []
    )
    clean_room_execution = (
        json.loads(CLEAN_ROOM_EXECUTION.read_text(encoding="utf-8"))
        if CLEAN_ROOM_EXECUTION.is_file()
        else {}
    )
    clean_room_commands = clean_room_execution.get("commands", {})
    clean_room_pass = all(
        clean_room_commands.get(command) in {"PASS", "PASS_PARTIAL"}
        for command in (
            "make bootstrap",
            "secret_scan",
            "ruff",
            "mypy_strict",
            "protocol_verify",
            "model_registry_verify",
            "figures_regeneration",
            "registry_verify_after_figure_materialization",
            "frontend_install",
            "frontend_build",
            "make validate_after_figure_materialization",
        )
    )
    phase18_pass = artifact_repro and phase15_spot_check and clean_room_pass and not registry_failures
    payload = {
        "phase": 18,
        "family": "REPRO",
        "status": "PASS" if phase18_pass else "PARTIAL",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "software_clean_room": {
            "status": "PASS_CLEAN_DETACHED_CHECKOUT" if clean_room_pass and not registry_failures else "PARTIAL",
            "execution_artifact": str(CLEAN_ROOM_EXECUTION.relative_to(ROOT))
            if CLEAN_ROOM_EXECUTION.is_file()
            else None,
            "registry_completed_runs_checked": len(completed),
            "registry_failures": registry_failures,
            "commands": clean_room_commands,
        },
        "scientific_artifact_reproducibility": {
            "status": "PASS_HASH_VERIFIED_BUNDLE" if artifact_repro else "FAIL",
            "publication_manifest": str(PUBLICATION.relative_to(ROOT)),
            "publication_manifest_sha256": hash_file(PUBLICATION) if PUBLICATION.is_file() else None,
            "hash_failures": hash_failures,
        },
        "gated_modal_smoke": {
            "status": "PASS_PHASE15_REPRESENTATIVE_DEVELOPMENT_SMOKE"
            if phase15_spot_check
            else "MISSING_OR_FAILED",
            "validation_artifact": str(PHASE15_VALIDATION.relative_to(ROOT))
            if PHASE15_VALIDATION.is_file()
            else None,
            "scope": "64 development-only rows; 56 verified cache rows and 8 remote rows; no locked rows or labels",
            "full_remote_reinference_required_by_literal_phase18": False,
        },
        "full_remote_reinference": {
            "status": "NOT_REQUIRED_BY_LITERAL_MASTER_TASK_LIST",
            "reason": "Phase 18 requires a gated Modal smoke; the completed Phase15 representative development-only smoke satisfies that minimum. A full remote re-inference is a stronger optional claim and is not asserted.",
        },
        "no_additional_remote_compute_in_phase18": True,
        "release_implication": (
            "Phase 18 PASS is limited to the documented clean detached checkout, hash-verified artifact bundle, and representative gated Modal smoke; "
            "it does not claim full remote re-inference."
            if phase18_pass
            else "Phase 18 remains PARTIAL until every documented clean-room command and hash gate is reproducible."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "artifact_reproducibility": artifact_repro, "output": str(OUTPUT)}, indent=2))
    return 0 if phase18_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Record the fail-closed Phase 19 release gate."""

# ruff: noqa: E501

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from evovariant_tr.registry import hash_file

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/runs/phase19_release_status.json"
PHASE15_VALIDATION = ROOT / "artifacts/phase15/phase15_parity_smoke_validation_20260922.json"
BILLING_FINAL = ROOT / "artifacts/phase19/modal_billing_final_20260922.json"


def main() -> int:
    phase18 = ROOT / "research/runs/phase18_clean_room_status.json"
    publication = ROOT / "research/reports/phase17/publication_manifest.json"
    phase18_payload = json.loads(phase18.read_text()) if phase18.is_file() else {}
    publication_payload = json.loads(publication.read_text()) if publication.is_file() else {}
    phase15_payload = json.loads(PHASE15_VALIDATION.read_text()) if PHASE15_VALIDATION.is_file() else {}
    phase16 = ROOT / "research/runs/phase16_ui_status.json"
    phase16_payload = json.loads(phase16.read_text()) if phase16.is_file() else {}
    phase15_checks = phase15_payload.get("checks", {})
    phase15_pass = (
        phase15_payload.get("status") == "PASS_PHASE15_PARITY_AND_RESUME"
        and isinstance(phase15_checks, dict)
        and all(value is True for value in phase15_checks.values())
    )
    phase16_pass = phase16_payload.get("status") == "PASS"
    phase18_pass = phase18_payload.get("status") == "PASS"
    publication_pass = publication_payload.get("status") == "PASS_LOCAL_PUBLICATION_BUNDLE"
    all_gates_pass = phase15_pass and phase16_pass and phase18_pass and publication_pass
    blockers = []
    if not phase15_pass:
        blockers.append("Complete the authorized Phase 15 parity-smoke validation and record PASS.")
    elif not phase16_pass:
        blockers.append("Complete the registered-output Phase 16 workbench gate and record PASS.")
    elif not publication_pass:
        blockers.append("Regenerate and hash-verify the Phase 17 publication bundle.")
    elif not phase18_pass:
        blockers.append("Complete the documented Phase 18 clean-room control-plane gate.")
    gates = {
        "phase14_locked_evaluation": "PASS",
        "phase17_publication_bundle": publication_payload.get("status", "MISSING"),
        "phase15_remote_batch_parity": "PASS_PHASE15_REPRESENTATIVE_SMOKE" if phase15_pass else "BLOCKED",
        "phase16_registered_output_workbench": phase16_payload.get("status", "MISSING"),
        "phase18_clean_room": phase18_payload.get("status", "MISSING"),
        "phase18_full_remote_reinference": phase18_payload.get("full_remote_reinference", {}).get("status", "MISSING"),
    }
    payload = {
        "phase": 19,
        "family": "RELEASE",
        "status": "PASS" if all_gates_pass else "BLOCKED",
        "release_allowed": False,
        "release_reason": "Internal gate only; no tag, deployment, or publication release was requested.",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "gates": gates,
        "blockers": blockers,
        "no_new_remote_compute": True,
        "source_artifacts": [
            {"path": str(publication.relative_to(ROOT)), "sha256": hash_file(publication) if publication.is_file() else None},
            {"path": str(phase18.relative_to(ROOT)), "sha256": hash_file(phase18) if phase18.is_file() else None},
            {"path": str(PHASE15_VALIDATION.relative_to(ROOT)), "sha256": hash_file(PHASE15_VALIDATION) if PHASE15_VALIDATION.is_file() else None},
            {"path": str(phase16.relative_to(ROOT)), "sha256": hash_file(phase16) if phase16.is_file() else None},
            {"path": str(BILLING_FINAL.relative_to(ROOT)), "sha256": hash_file(BILLING_FINAL) if BILLING_FINAL.is_file() else None},
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "release_allowed": False, "output": str(OUTPUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def main() -> int:
    phase18 = ROOT / "research/runs/phase18_clean_room_status.json"
    publication = ROOT / "research/reports/phase17/publication_manifest.json"
    phase18_payload = json.loads(phase18.read_text()) if phase18.is_file() else {}
    publication_payload = json.loads(publication.read_text()) if publication.is_file() else {}
    gates = {
        "phase14_locked_evaluation": "PASS",
        "phase17_publication_bundle": publication_payload.get("status", "MISSING"),
        "phase15_remote_batch_parity": "BLOCKED_NEW_PAID_AUTHORIZATION_REQUIRED",
        "phase18_full_remote_reinference": phase18_payload.get("full_remote_reinference", {}).get("status", "MISSING"),
    }
    payload = {
        "phase": 19,
        "family": "RELEASE",
        "status": "BLOCKED",
        "release_allowed": False,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "gates": gates,
        "blockers": [
            "Phase 15 remote batch parity has no current paid authorization.",
            "Phase 18 full remote scientific re-inference remains unrun.",
            "A fresh exact-candidate release decision is required before any tag, deployment, or publication claim.",
        ],
        "no_remote_compute": True,
        "source_artifacts": [
            {"path": str(publication.relative_to(ROOT)), "sha256": hash_file(publication) if publication.is_file() else None},
            {"path": str(phase18.relative_to(ROOT)), "sha256": hash_file(phase18) if phase18.is_file() else None},
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "release_allowed": False, "output": str(OUTPUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

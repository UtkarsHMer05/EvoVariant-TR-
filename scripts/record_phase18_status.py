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
    payload = {
        "phase": 18,
        "family": "REPRO",
        "status": "PARTIAL",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "software_clean_room": {
            "status": "PASS_LOCAL_REPOSITORY_CHECKS" if not registry_failures else "FAIL",
            "registry_completed_runs_checked": len(completed),
            "registry_failures": registry_failures,
        },
        "scientific_artifact_reproducibility": {
            "status": "PASS_HASH_VERIFIED_BUNDLE" if artifact_repro else "FAIL",
            "publication_manifest": str(PUBLICATION.relative_to(ROOT)),
            "publication_manifest_sha256": hash_file(PUBLICATION) if PUBLICATION.is_file() else None,
            "hash_failures": hash_failures,
        },
        "full_remote_reinference": {
            "status": "NOT_RUN_AUTHORIZATION_BOUNDARY",
            "reason": "A fresh paid exact-scope approval is required; no remote re-inference was started in this continuation.",
        },
        "no_remote_compute": True,
        "release_implication": "Phase 18 is not PASS because full remote scientific re-inference remains unrun; software and artifact reproducibility are separate claims.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "artifact_reproducibility": artifact_repro, "output": str(OUTPUT)}, indent=2))
    return 0 if artifact_repro else 1


if __name__ == "__main__":
    raise SystemExit(main())

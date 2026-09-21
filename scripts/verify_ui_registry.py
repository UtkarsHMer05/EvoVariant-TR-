#!/usr/bin/env python3
"""Verify that the research workbench has real registry metadata to display.

This is a control-plane check, not a claim that the scientific result is final.
Completed PRELIMINARY runs make the read-only registry panel usable; missing
full-cohort or locked-test artifacts remain visible to the downstream gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evovariant_tr.evidence import AGGREGATE_ALLOWED_STAGES
from evovariant_tr.registry import Registry, RunStatus, verify_output_hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("experiments/registry"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("research/runs/phase16_ui_status.json"))
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    registry = Registry(args.registry, repo_root=repo_root)
    records = registry.list_runs()
    eligible = []
    blockers: list[str] = []
    for record in records:
        if record.status is not RunStatus.COMPLETED:
            continue
        if record.evidence_stage not in AGGREGATE_ALLOWED_STAGES:
            continue
        try:
            verify_output_hashes(record, repo_root)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            blockers.append(f"{record.run_id}: output verification failed: {exc}")
            continue
        eligible.append(record.run_id)

    if not eligible:
        blockers.append("no completed PRELIMINARY or FINAL registry runs are available")
    payload = {
        "status": "PARTIAL" if eligible else "BLOCKED",
        "phase": 16,
        "registry_connected": bool(eligible),
        "registered_run_count": len(records),
        "completed_scientific_run_count": len(eligible),
        "locked_test_evaluated": False,
        "blockers": sorted(set(blockers)),
        "notes": (
            "The UI registry panel may display immutable metadata from eligible runs; "
            "scientific result panels remain evidence-gated."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

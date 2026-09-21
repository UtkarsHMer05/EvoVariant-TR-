#!/usr/bin/env python3
"""Validate the current bounded Phase 6/7 development approval artifact."""

from __future__ import annotations

import json
from pathlib import Path

from development_approval import validate_development_approval


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    approval_path = repo_root / "artifacts/approvals/phase6_phase7_development_20260921.json"
    approval = validate_development_approval(approval_path, repo_root)
    dataset = approval["dataset"]
    split_hashes = approval["train_validation_hashes"]
    print(
        json.dumps(
            {
                "status": "PASS",
                "approval_artifact": str(approval_path.relative_to(repo_root)),
                "max_budget_usd": approval["max_budget_usd"],
                "protocol_hash": approval["protocol"]["sha256"],
                "development_manifest_sha256": dataset["development_manifest_sha256"],
                "semantic_split_hash": dataset["semantic_split_hash"],
                "TRAIN_record_set_sha256": split_hashes["TRAIN"]["record_set_sha256"],
                "VALIDATION_record_set_sha256": split_hashes["VALIDATION"]["record_set_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

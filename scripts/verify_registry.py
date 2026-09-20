#!/usr/bin/env python3
"""Verify the immutable experiment registry (Milestone 20).

Checks:
- every run record parses as a valid ``RunRecord`` (strict schema);
- every FINAL record passes the final gate (real commit, clean tree);
- run IDs referenced by parent links resolve to existing records;
- the append-only event log (log.jsonl) is well-formed JSON.

Usage:
    python scripts/verify_registry.py --registry-dir experiments/registry

Exit codes: 0 = OK, 1 = verification failures, 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evovariant_tr.registry import (  # noqa: E402
    Registry,
    RegistryError,
    RunStatus,
    validate_final_gate,
    verify_output_hashes,
)


def verify_registry(registry_dir: Path, *, repo_root: Path = REPO_ROOT) -> list[str]:
    """Return a list of human-readable failures (empty list = healthy)."""
    failures: list[str] = []
    registry = Registry(registry_dir, repo_root=repo_root)

    try:
        records = registry.list_runs()
    except (RegistryError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot enumerate run records: {exc}"]

    run_ids = {record.run_id for record in records}
    for record in records:
        if record.parent_run_id is not None and record.parent_run_id not in run_ids:
            failures.append(
                f"{record.run_id}: parent_run_id {record.parent_run_id!r} "
                f"does not resolve to a known run"
            )
        try:
            validate_final_gate(record)
        except RegistryError as exc:
            failures.append(str(exc))
        if record.status is RunStatus.COMPLETED:
            try:
                verify_output_hashes(record, repo_root)
            except RegistryError as exc:
                failures.append(str(exc))

    log_path = registry.log_path
    if log_path.is_file():
        for line_no, line in enumerate(
            log_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"log.jsonl:{line_no}: malformed JSON — {exc}")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry-dir",
        type=Path,
        default=Path("experiments/registry"),
        help="Registry root directory (contains runs/ and log.jsonl)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used for FINAL-tree and output-hash verification",
    )
    args = parser.parse_args(argv)

    if not args.registry_dir.is_dir():
        print(f"OK: registry dir {args.registry_dir} does not exist yet (nothing to verify)")
        return 0

    failures = verify_registry(args.registry_dir, repo_root=args.repo_root)
    if failures:
        print(f"FAIL: {len(failures)} registry verification failure(s):")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"OK: registry at {args.registry_dir} verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

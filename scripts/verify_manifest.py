#!/usr/bin/env python3
"""Verify a file manifest against on-disk assets.

Usage:
    python scripts/verify_manifest.py --manifest data/manifests/clinvar_t0.json \
        --base-dir data/raw

Exit codes: 0 = all entries verify, 1 = verification failures, 2 = usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evovariant_tr.manifest import load_manifest, verify_manifest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to the manifest JSON file")
    parser.add_argument(
        "--base-dir",
        required=True,
        help="Directory that manifest entry paths are relative to",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    base_dir = Path(args.base_dir)
    if not manifest_path.is_file():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    if not base_dir.is_dir():
        print(f"ERROR: base directory not found: {base_dir}", file=sys.stderr)
        return 2

    manifest = load_manifest(manifest_path)
    failures = verify_manifest(manifest, base_dir)
    if failures:
        print(f"FAIL: {len(failures)} of {len(manifest.entries)} entries failed verification:")
        for failure in failures:
            print(f"  {failure.path}: {failure.kind} — {failure.detail}")
        return 1
    print(f"OK: all {len(manifest.entries)} entries verified ({manifest.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

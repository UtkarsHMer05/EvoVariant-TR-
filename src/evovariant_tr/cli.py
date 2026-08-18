"""EvoVariant-TR command-line control surface.

Subcommands are added as their milestones land; every command validates the
frozen protocol first so no operation can drift from the registered contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evovariant_tr import __version__
from evovariant_tr.config import load_protocol
from evovariant_tr.manifest import load_manifest, verify_manifest

DEFAULT_PROTOCOL = Path("research/protocol/protocol.yaml")


def cmd_validate_protocol(args: argparse.Namespace) -> int:
    protocol = load_protocol(args.protocol)
    print(
        f"OK: protocol {protocol.protocol_version} validated "
        f"(t0={protocol.temporal_design.t0_release.release_date}, "
        f"t1={protocol.temporal_design.t1_release.release_date}, "
        f"assembly={protocol.temporal_design.reference_assembly}, "
        f"context={protocol.sequence_contract.context_length_bp}bp)"
    )
    return 0


def cmd_verify_manifest(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    failures = verify_manifest(manifest, args.base_dir)
    if failures:
        print(f"FAIL: {len(failures)} of {len(manifest.entries)} entries failed:")
        for failure in failures:
            print(f"  {failure.path}: {failure.kind} — {failure.detail}")
        return 1
    print(f"OK: all {len(manifest.entries)} entries verified ({manifest.name})")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(json.dumps({"package": "evovariant-tr", "version": __version__}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evovariant-tr",
        description="EvoVariant-TR research tooling (research use only).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate-protocol", help="Validate the frozen research protocol YAML"
    )
    validate.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    validate.set_defaults(func=cmd_validate_protocol)

    verify = subparsers.add_parser(
        "verify-manifest", help="Verify a file manifest against on-disk assets"
    )
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--base-dir", type=Path, required=True)
    verify.set_defaults(func=cmd_verify_manifest)

    version = subparsers.add_parser("version", help="Print package version as JSON")
    version.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())

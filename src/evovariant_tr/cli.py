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
from evovariant_tr.cohort import build_primary_cohort
from evovariant_tr.config import load_protocol
from evovariant_tr.control_plane import verify_ml_control_plane
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


def cmd_validate_ml_control_plane(args: argparse.Namespace) -> int:
    """Validate additive ML-extension files without changing the frozen protocol."""
    failures = verify_ml_control_plane(args.repo_root)
    if failures:
        print(f"FAIL: {len(failures)} ML control-plane checks failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("OK: ML-extension control plane validated and frozen protocol hash preserved")
    return 0


def cmd_build_ml_splits(args: argparse.Namespace) -> int:
    """Build the Phase 3 temporal audit and development split artifacts."""
    from evovariant_tr.splits import build_phase3_artifacts

    summary = build_phase3_artifacts(
        args.t0,
        args.t1,
        output_dir=args.output_dir,
        t0_manifest=args.t0_manifest,
        t1_manifest=args.t1_manifest,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


def cmd_modal_smoke(args: argparse.Namespace) -> int:
    """Run a safe Modal preflight and record unavailable/deferred evidence."""
    from evovariant_tr.cost_ledger import append_entry, new_entry
    from evovariant_tr.modal_config import check_modal_environment

    environment = check_modal_environment()
    installed = environment.get("modal_installed") is True
    authenticated = environment.get("modal_authenticated") is True
    ready = installed and authenticated
    if ready and args.execute:
        from evovariant_tr.cost_policy import assert_paid_compute_allowed

        assert_paid_compute_allowed()
        raise RuntimeError(
            "real Modal execution is intentionally explicit and must be implemented by "
            "the authorized pilot runner"
        )
    notes = (
        "Modal preflight passed; no remote invocation requested"
        if ready
        else f"Modal smoke deferred: environment={environment}"
    )
    entry = new_entry(
        run_id=args.run_id,
        workload="evo2_modal_smoke",
        backend="modal" if ready else "unavailable",
        gpu_type="H100" if ready else None,
        status="PLANNED" if ready else "DEFERRED",
        notes=notes,
    )
    append_entry(args.ledger, entry)
    print(json.dumps({"environment": environment, "ledger_entry": entry.to_dict()}, indent=2))
    return 0


def cmd_verify_model_registry(args: argparse.Namespace) -> int:
    """Verify model manifests and report the explicit inclusion boundary."""
    from evovariant_tr.model_registry import (
        included_models,
        load_model_registry,
        verify_model_registry,
    )

    failures = verify_model_registry(args.models_dir, schema_path=args.schema)
    if failures:
        print(f"FAIL: {len(failures)} model registry checks failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    models = load_model_registry(args.models_dir, schema_path=args.schema)
    included = included_models(models)
    statuses = {model.model_id: model.status for model in models}
    print(
        json.dumps(
            {
                "status": "PASS",
                "manifest_count": len(models),
                "included_count": len(included),
                "statuses": statuses,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_deferred_phase(args: argparse.Namespace) -> int:
    """Record a truthful no-result status for a gated later phase."""
    from evovariant_tr.experiment_control import deferred_artifact, write_artifact

    artifact = deferred_artifact(
        phase=args.phase,
        family=args.family,
        blockers=tuple(args.blocker),
        inputs={"command": args.command_name},
    )
    output = write_artifact(args.output, artifact)
    print(json.dumps({"status": artifact.status.value, "artifact": str(output)}, indent=2))
    return 0


def cmd_build_cohort(args: argparse.Namespace) -> int:
    from datetime import date

    t0_date = date.fromisoformat(args.t0_date) if args.t0_date else None
    t1_date = date.fromisoformat(args.t1_date) if args.t1_date else None

    cohort = build_primary_cohort(
        args.t0, args.t1,
        t0_release_date=t0_date,
        t1_release_date=t1_date,
    )

    output = {
        "n_total": cohort.n_total,
        "n_resolved_pathogenic": cohort.n_resolved_pathogenic,
        "n_resolved_benign": cohort.n_resolved_benign,
        "n_unresolved": cohort.n_unresolved,
        "n_excluded": cohort.n_excluded,
        "class_counts": cohort.class_counts(),
        "flow": cohort.flow.to_dict(),
    }

    print(json.dumps(output, indent=2, default=str))
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

    cohort = subparsers.add_parser(
        "build-cohort", help="Build temporal VUS-resolution cohort from t0/t1 archives"
    )
    cohort.add_argument("--t0", type=Path, required=True, help="Path to t0 variant_summary.txt.gz")
    cohort.add_argument("--t1", type=Path, required=True, help="Path to t1 variant_summary.txt.gz")
    cohort.add_argument("--t0-date", type=str, default=None, help="t0 release date (YYYY-MM-DD)")
    cohort.add_argument("--t1-date", type=str, default=None, help="t1 release date (YYYY-MM-DD)")
    cohort.add_argument("--output", type=Path, default=None, help="Write JSON to file")
    cohort.set_defaults(func=cmd_build_cohort)

    version = subparsers.add_parser("version", help="Print package version as JSON")
    version.set_defaults(func=cmd_version)

    ml_control = subparsers.add_parser(
        "validate-ml-control-plane",
        help="Validate the additive ML-extension protocol, schemas, and hashes",
    )
    ml_control.add_argument("--repo-root", type=Path, default=Path("."))
    ml_control.set_defaults(func=cmd_validate_ml_control_plane)

    splits = subparsers.add_parser(
        "build-ml-splits",
        help="Audit the temporal cohort and build deterministic development splits",
    )
    splits.add_argument("--t0", type=Path, required=True)
    splits.add_argument("--t1", type=Path, required=True)
    splits.add_argument("--t0-manifest", type=Path, required=True)
    splits.add_argument("--t1-manifest", type=Path, required=True)
    splits.add_argument("--output-dir", type=Path, required=True)
    splits.add_argument("--seed", type=int, default=20260814)
    splits.set_defaults(func=cmd_build_ml_splits)

    modal_smoke = subparsers.add_parser(
        "modal-smoke",
        help="Run a no-spend Modal preflight and append a cost-ledger record",
    )
    modal_smoke.add_argument(
        "--ledger", type=Path, default=Path("research/runs/cost_ledger.jsonl")
    )
    modal_smoke.add_argument("--run-id", default="modal-smoke-preflight")
    modal_smoke.add_argument(
        "--execute",
        action="store_true",
        help="Require paid acknowledgement for the separately authorized remote runner",
    )
    modal_smoke.set_defaults(func=cmd_modal_smoke)

    model_registry = subparsers.add_parser(
        "verify-model-registry",
        help="Verify schema-conformant model candidate manifests",
    )
    model_registry.add_argument(
        "--models-dir", type=Path, default=Path("research/ml_extension/models")
    )
    model_registry.add_argument(
        "--schema", type=Path, default=Path("research/schemas/model_manifest.schema.json")
    )
    model_registry.set_defaults(func=cmd_verify_model_registry)

    deferred = subparsers.add_parser(
        "phase-status",
        help="Record an explicit blocked/deferred status for a gated phase",
    )
    deferred.add_argument("--phase", type=int, required=True)
    deferred.add_argument("--family", required=True)
    deferred.add_argument("--command-name", default="phase-status")
    deferred.add_argument("--output", type=Path, required=True)
    deferred.add_argument("--blocker", action="append", required=True)
    deferred.set_defaults(func=cmd_deferred_phase)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())

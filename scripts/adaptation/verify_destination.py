#!/usr/bin/env python3
"""Verify the writable post-hoc adaptation destination without an old-source gate."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evovariant_tr.adaptation.data import (
    load_formal_rows,
    sha256_file,
    verify_formal_data,
    verify_reference_rows,
)
from evovariant_tr.adaptation.models import MODEL_IDS, MODEL_REVISIONS

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"
REFERENCE_HASH = "5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51"
PROOF_PATH = "artifacts/adaptation/caduceus_partial_small_finetune_smoke.json"


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"{type(error).__name__}: {error}"
    return value if isinstance(value, dict) else None, None


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _preserve_previous(output: Path) -> str | None:
    if not output.is_file():
        return None
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    preserved = output.with_name(f"{output.stem}.superseded_{stamp}{output.suffix}")
    shutil.copy2(output, preserved)
    return str(preserved)


def _positive_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _proof_report(drive: Path) -> dict[str, Any]:
    path = drive / PROOF_PATH
    if not path.is_file():
        return {"status": "MISSING_OPTIONAL_REGENERATE", "path": str(path)}
    report, error = _read_json(path)
    if report is None:
        return {"status": "INVALID", "path": str(path), "error": error}
    total = report.get("total_params", report.get("total_parameters"))
    trainable = report.get("trainable_params", report.get("trainable_parameters"))
    encoder_delta = _positive_number(report.get("encoder_delta_norm"))
    frozen_delta = _positive_number(report.get("frozen_control_delta_norm"))
    valid = (
        report.get("status") == "PASS"
        and report.get("model_revision") == MODEL_REVISIONS["caduceus"]
        and report.get("protocol_sha256") == PROTOCOL_HASH
        and total == 7_728_385
        and trainable == 1_933_313
        and report.get("trainable_backbone_blocks") == [12, 13, 14, 15]
        and report.get("frozen_backbone_blocks") == list(range(12))
        and encoder_delta is not None
        and encoder_delta > 0
        and frozen_delta == 0
    )
    return {
        "status": "PASS" if valid else "INVALID",
        "path": str(path),
        "sha256": sha256_file(path),
        "total_params": total,
        "trainable_params": trainable,
        "trainable_backbone_blocks": report.get("trainable_backbone_blocks"),
        "frozen_backbone_blocks": report.get("frozen_backbone_blocks"),
        "encoder_delta_norm": report.get("encoder_delta_norm"),
        "frozen_control_delta_norm": report.get("frozen_control_delta_norm"),
        "details": "REAL_ENCODER_UPDATE_PROOF; not a completed fine-tuning experiment",
    }


def _reference_report(root: Path, reference: Path) -> dict[str, Any]:
    if not reference.is_file():
        return {"status": "MISSING", "path": str(reference)}
    actual = sha256_file(reference)
    if actual != REFERENCE_HASH:
        return {
            "status": "INVALID",
            "path": str(reference),
            "sha256": actual,
            "expected_sha256": REFERENCE_HASH,
        }
    try:
        from pyfaidx import Fasta

        train, validation = load_formal_rows(root)
        fasta = Fasta(str(reference), as_raw=True, sequence_always_upper=True)
        checked = verify_reference_rows(fasta, (*train, *validation))
    except Exception as error:  # dependency/runtime diagnostics belong in the report
        return {
            "status": "INVALID",
            "path": str(reference),
            "sha256": actual,
            "error": f"{type(error).__name__}: {error}",
        }
    return {
        "status": "PASS" if checked == 4000 else "INVALID",
        "path": str(reference),
        "sha256": actual,
        "expected_sha256": REFERENCE_HASH,
        "checked_formal_ref_alleles": checked,
    }


def verify_destination(
    root: str | Path,
    drive: str | Path,
    reference: str | Path,
    output: str | Path,
    source: str | Path | None = None,
) -> dict[str, Any]:
    """Write an auditable destination report; absence of source is non-blocking."""
    root_path = Path(root).resolve()
    drive_path = Path(drive)
    output_path = Path(output)
    old_source = Path(source) if source is not None else drive_path.parent / "EvoVariantTR_original"
    previous = _preserve_previous(output_path)
    checks: dict[str, Any] = {}

    try:
        drive_path.mkdir(parents=True, exist_ok=True)
        if drive_path.is_symlink():
            raise RuntimeError("destination must be an owned directory, not a symlink")
        sentinel = drive_path / "state/destination_write_test.txt"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("destination-write-ok\n", encoding="utf-8")
        checks["destination_writable"] = True
        checks["destination"] = str(drive_path)
    except (OSError, RuntimeError) as error:
        checks["destination_writable"] = False
        checks["destination_error"] = f"{type(error).__name__}: {error}"

    source_visible = old_source.is_dir()
    checks["migration_source"] = {
        "status": "VISIBLE_OPTIONAL" if source_visible else "MIGRATION_SOURCE_NOT_AVAILABLE",
        "path": str(old_source),
        "used_as_gate": False,
    }

    try:
        checks["formal_data"] = {"status": "PASS", **verify_formal_data(root_path)}
    except Exception as error:  # preserve exact failure evidence for the notebook
        checks["formal_data"] = {
            "status": "INVALID",
            "error": f"{type(error).__name__}: {error}",
        }
    checks["reference"] = _reference_report(root_path, Path(reference))
    protocol_path = root_path / "research/adaptation/protocol.yaml"
    protocol_hash = sha256_file(protocol_path)
    checks["protocol"] = {
        "status": "PASS" if protocol_hash == PROTOCOL_HASH else "INVALID",
        "sha256": protocol_hash,
        "expected_sha256": PROTOCOL_HASH,
    }
    checks["caduceus"] = {
        "status": "PINNED",
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
    }
    checks["encoder_update_proof"] = _proof_report(drive_path)

    formal_ok = checks["formal_data"].get("status") == "PASS"
    reference_ok = checks["reference"].get("status") == "PASS"
    protocol_ok = checks["protocol"].get("status") == "PASS"
    writable_ok = checks.get("destination_writable", False)
    if writable_ok and formal_ok and protocol_ok and reference_ok:
        status = "DESTINATION_READY_TO_RESUME"
    elif writable_ok and formal_ok and protocol_ok:
        status = "DESTINATION_WAITING_FOR_REFERENCE"
    else:
        status = "DESTINATION_VERIFICATION_FAILED"
    report = {
        "status": status,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "root": str(root_path),
        "drive": str(drive_path),
        "reference": str(Path(reference)),
        "checks": checks,
        "previous_report_preserved": previous,
    }
    _write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--drive-root", default="/content/drive/MyDrive/EvoVariantTR")
    parser.add_argument("--reference", default="/content/Homo_sapiens_assembly38.fasta")
    parser.add_argument(
        "--source-drive-root", default="/content/drive/MyDrive/EvoVariantTR_original"
    )
    parser.add_argument(
        "--output",
        default="/content/drive/MyDrive/EvoVariantTR/artifacts/adaptation/destination_verification.json",
    )
    args = parser.parse_args()
    report = verify_destination(
        args.root, args.drive_root, args.reference, args.output, args.source_drive_root
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

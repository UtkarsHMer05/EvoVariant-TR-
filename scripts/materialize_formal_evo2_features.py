#!/usr/bin/env python3
"""Convert a completed formal Evo2 raw-score artifact to feature JSONL.

The Phase 6 scorer intentionally keeps its raw-score schema separate from the
downstream classifier schema.  This adapter verifies the exact formal cohort,
the recorded prediction hash, and finite alternate-minus-reference scores
before emitting local TRAIN/VALIDATION feature artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

from evovariant_tr.feature_store import make_feature_record

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
EXPECTED_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_COUNT = 4_000
FAMILIES: dict[str, tuple[str, ...]] = {
    "delta_primary": ("delta_primary",),
    "delta_forward_reverse": ("delta_forward", "delta_reverse"),
    "delta_orientation_difference": ("delta_forward", "delta_reverse"),
}


class Evo2MaterializationError(ValueError):
    """Raised when the raw Evo2 artifact fails the formal boundary checks."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if sha256_file(path) != EXPECTED_MANIFEST_SHA256:
        raise Evo2MaterializationError("formal development manifest hash changed")
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("record_set_sha256") != EXPECTED_RECORD_SET_SHA256
    ):
        raise Evo2MaterializationError("formal development record-set hash changed")
    raw_records = document.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != EXPECTED_COUNT:
        raise Evo2MaterializationError("formal development manifest must contain 4,000 records")
    records = [row for row in raw_records if isinstance(row, dict)]
    if len(records) != EXPECTED_COUNT:
        raise Evo2MaterializationError("formal development manifest contains a non-object record")
    records.sort(key=lambda row: str(row["normalized_variant_id"]))
    return records


def _finite_number(row: dict[str, Any], key: str, identity: str) -> float:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise Evo2MaterializationError(f"{key} is not finite for {identity}")
    return float(value)


def materialize(
    artifact_path: Path,
    output_dir: Path,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict) or artifact.get("status") != "PASS_FULL_DEVELOPMENT_COHORT":
        raise Evo2MaterializationError("Evo2 artifact is not PASS_FULL_DEVELOPMENT_COHORT")
    if artifact.get("protocol_hash") != (
        "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
    ):
        raise Evo2MaterializationError("Evo2 artifact protocol hash is not frozen")
    dataset = artifact.get("dataset")
    if not isinstance(dataset, dict) or dataset.get("processed_records") != EXPECTED_COUNT:
        raise Evo2MaterializationError("Evo2 artifact does not contain 4,000 processed rows")
    if artifact.get("scientific_boundary", {}).get("labels_sent_to_modal") is not False:
        raise Evo2MaterializationError("Evo2 artifact does not prove labels stayed local")
    outputs = artifact.get("outputs")
    if not isinstance(outputs, dict):
        raise Evo2MaterializationError("Evo2 artifact outputs are missing")
    prediction_value = outputs.get("predictions_jsonl")
    if not isinstance(prediction_value, str):
        raise Evo2MaterializationError("Evo2 predictions JSONL path is missing")
    predictions_path = REPO_ROOT / prediction_value
    if not predictions_path.is_file() or outputs.get("predictions_sha256") != sha256_file(
        predictions_path
    ):
        raise Evo2MaterializationError("Evo2 predictions JSONL hash does not match")
    raw_rows = [
        json.loads(line)
        for line in predictions_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(raw_rows) != EXPECTED_COUNT or not all(isinstance(row, dict) for row in raw_rows):
        raise Evo2MaterializationError("Evo2 predictions JSONL does not contain 4,000 objects")
    expected = {str(row["normalized_variant_id"]): row for row in manifest}
    observed: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        identity = str(row.get("normalized_variant_id", ""))
        if not identity or identity in observed:
            raise Evo2MaterializationError(f"duplicate or empty Evo2 prediction ID: {identity}")
        if identity not in expected:
            raise Evo2MaterializationError(f"unexpected Evo2 prediction ID: {identity}")
        if row.get("split") != expected[identity].get("split"):
            raise Evo2MaterializationError(f"split mismatch for Evo2 prediction {identity}")
        if row.get("gene_symbol") != expected[identity].get("gene_symbol"):
            raise Evo2MaterializationError(f"gene mismatch for Evo2 prediction {identity}")
        for key in ("delta_primary", "delta_forward", "delta_reverse"):
            _finite_number(row, key, identity)
        observed[identity] = row
    if set(observed) != set(expected):
        raise Evo2MaterializationError("Evo2 prediction IDs do not exactly match formal manifest")

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_sha256 = sha256_file(artifact_path)
    prediction_sha256 = sha256_file(predictions_path)
    outputs: list[dict[str, Any]] = []
    sorted_rows = [observed[str(record["normalized_variant_id"])] for record in manifest]
    for family, keys in FAMILIES.items():
        lines: list[str] = []
        for row in sorted_rows:
            identity = str(row["normalized_variant_id"])
            values = [_finite_number(row, key, identity) for key in keys]
            if family == "delta_orientation_difference":
                values = [values[0] - values[1]]
            record = expected[identity]
            feature = make_feature_record(
                normalized_variant_id=identity,
                model_id="evo2",
                layer=family,
                split=str(record["split"]),
                values=values,
                dtype="float64",
                gene_symbol=str(record["gene_symbol"]),
            ).to_dict()
            feature.update(
                {
                    "label": int(record["label"]),
                    "feature_family": family,
                    "score_semantics": "alternate_minus_reference_log_likelihood",
                    "source_artifact": display_path(artifact_path),
                    "source_artifact_sha256": artifact_sha256,
                    "source_predictions": display_path(predictions_path),
                    "source_predictions_sha256": prediction_sha256,
                    "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                    "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
                    "labels_attached_locally": True,
                    "locked_test_present": False,
                }
            )
            lines.append(json.dumps(feature, sort_keys=True) + "\n")
        output_path = output_dir / f"evo2_{family}.jsonl"
        metadata_path = output_path.with_suffix(".metadata.json")
        if output_path.exists() or metadata_path.exists():
            raise Evo2MaterializationError(f"refusing to overwrite existing output: {output_path}")
        atomic_text(output_path, "".join(lines))
        metadata = {
            "status": "PASS_FORMAL_FEATURE_MATERIALIZATION",
            "candidate": "evo2",
            "model_id": "evo2",
            "layer": family,
            "feature_family": family,
            "record_count": EXPECTED_COUNT,
            "train_count": sum(row["split"] == "TRAIN" for row in manifest),
            "validation_count": sum(row["split"] == "VALIDATION" for row in manifest),
            "locked_test_count": 0,
            "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
            "source_artifact": display_path(artifact_path),
            "source_artifact_sha256": artifact_sha256,
            "source_predictions": display_path(predictions_path),
            "source_predictions_sha256": prediction_sha256,
            "feature_artifact": display_path(output_path),
            "feature_artifact_sha256": sha256_file(output_path),
            "labels_attached_locally": True,
            "locked_test_present": False,
        }
        atomic_text(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        outputs.append(metadata)
    summary = {
        "status": "PASS_FORMAL_FEATURE_MATERIALIZATION",
        "candidate": "evo2",
        "source_artifact": display_path(artifact_path),
        "source_artifact_sha256": artifact_sha256,
        "source_predictions_sha256": prediction_sha256,
        "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        "record_count": EXPECTED_COUNT,
        "locked_test_count": 0,
        "output_count": len(outputs),
        "outputs": outputs,
        "labels_attached_locally": True,
        "locked_test_present": False,
    }
    atomic_text(
        output_dir / "materialization_summary.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        summary = materialize(args.artifact, args.output_dir, manifest_path=args.manifest)
    except (Evo2MaterializationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

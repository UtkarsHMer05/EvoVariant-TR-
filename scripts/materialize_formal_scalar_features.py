#!/usr/bin/env python3
"""Create compact scalar summaries from the verified formal representation NPZs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from evovariant_tr.feature_store import make_feature_record

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
LAYERS = {
    "nucleotide_transformer": (8, 16, 24),
    "caduceus": (4, 8, 16),
}
FEATURE_NAMES = (
    "forward_delta_l2",
    "reverse_delta_l2",
    "aggregate_delta_l2",
    "orientation_disagreement_l2",
    "cosine_similarity",
    "aggregate_delta_mean",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_records() -> list[dict[str, Any]]:
    if sha256_file(MANIFEST) != MANIFEST_SHA256:
        raise ValueError("formal manifest hash changed")
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if document.get("record_set_sha256") != RECORD_SET_SHA256:
        raise ValueError("formal record-set hash changed")
    records = document.get("records")
    if not isinstance(records, list) or len(records) != 4000:
        raise ValueError("formal manifest must contain 4,000 records")
    ordered = sorted(records, key=lambda row: str(row["normalized_variant_id"]))
    if {row["split"] for row in ordered} != {"TRAIN", "VALIDATION"}:
        raise ValueError("formal manifest must contain TRAIN and VALIDATION only")
    return ordered


def _array(npz: Any, name: str, rows: int, layers: int) -> np.ndarray:
    value = np.asarray(npz[name])
    if value.shape[:2] != (rows, layers) or not np.isfinite(value).all():
        raise ValueError(f"invalid {name} array shape or finite values: {value.shape}")
    return value


def materialize(npz_path: Path, output_dir: Path, candidate: str) -> dict[str, Any]:
    if candidate not in LAYERS:
        raise ValueError(f"unknown candidate: {candidate}")
    records = load_records()
    expected_layers = LAYERS[candidate]
    npz_sha256 = sha256_file(npz_path)
    with np.load(npz_path, allow_pickle=False) as npz:
        ids = [str(value) for value in np.asarray(npz["variant_ids"])]
        splits = [str(value) for value in np.asarray(npz["splits"])]
        genes = [str(value) for value in np.asarray(npz["gene_symbols"])]
        labels = np.asarray(npz["labels"])
        layers = tuple(int(value) for value in np.asarray(npz["layers"]))
        expected_ids = [str(row["normalized_variant_id"]) for row in records]
        if ids != expected_ids or splits != [str(row["split"]) for row in records]:
            raise ValueError("NPZ IDs or splits do not match the formal manifest")
        if genes != [str(row["gene_symbol"]) for row in records]:
            raise ValueError("NPZ genes do not match the formal manifest")
        if layers != expected_layers or not np.array_equal(
            labels, np.asarray([int(row["label"]) for row in records], dtype=np.int8)
        ):
            raise ValueError("NPZ layers or locally attached labels do not match the manifest")
        forward = _array(npz, "forward_delta", len(records), len(layers))
        reverse = _array(npz, "reverse_delta", len(records), len(layers))
        aggregate = _array(npz, "alt_minus_ref_aggregate", len(records), len(layers))
        distance = _array(npz, "distance_l2", len(records), len(layers))
        disagreement = _array(npz, "orientation_disagreement_l2", len(records), len(layers))
        cosine = _array(npz, "cosine_similarity", len(records), len(layers))
        scalar_values = np.stack(
            [
                np.linalg.norm(forward, axis=2),
                np.linalg.norm(reverse, axis=2),
                distance,
                disagreement,
                cosine,
                aggregate.mean(axis=2),
            ],
            axis=2,
        )
        if not np.isfinite(scalar_values).all():
            raise ValueError("scalar summaries contain non-finite values")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files: list[dict[str, Any]] = []
    family = "+".join(FEATURE_NAMES)
    for layer_index, layer in enumerate(expected_layers):
        output_path = output_dir / f"{candidate}_layer_{layer}_scalar_summary.jsonl"
        metadata_path = output_path.with_suffix(".metadata.json")
        if output_path.exists() or metadata_path.exists():
            raise ValueError(f"refusing to overwrite {output_path}")
        lines: list[str] = []
        for row_index, record in enumerate(records):
            values = [float(value) for value in scalar_values[row_index, layer_index]]
            if not values or not all(math.isfinite(value) for value in values):
                raise ValueError(f"non-finite scalar row for layer {layer}")
            feature = make_feature_record(
                normalized_variant_id=str(record["normalized_variant_id"]),
                model_id=candidate,
                layer=f"{layer}:scalar_summary",
                split=str(record["split"]),
                values=values,
                dtype="float64",
                gene_symbol=str(record["gene_symbol"]),
            ).to_dict()
            feature.update(
                {
                    "label": int(record["label"]),
                    "feature_family": family,
                    "feature_names": list(FEATURE_NAMES),
                    "source_npz": str(npz_path.relative_to(REPO_ROOT)),
                    "source_npz_sha256": npz_sha256,
                    "formal_manifest_sha256": MANIFEST_SHA256,
                    "formal_record_set_sha256": RECORD_SET_SHA256,
                    "labels_attached_locally": True,
                    "locked_test_present": False,
                }
            )
            lines.append(json.dumps(feature, sort_keys=True) + "\n")
        atomic_text(output_path, "".join(lines))
        metadata = {
            "status": "PASS_FORMAL_SCALAR_FEATURE_MATERIALIZATION",
            "candidate": candidate,
            "model_id": candidate,
            "layer": f"{layer}:scalar_summary",
            "feature_names": list(FEATURE_NAMES),
            "record_count": len(records),
            "train_count": sum(row["split"] == "TRAIN" for row in records),
            "validation_count": sum(row["split"] == "VALIDATION" for row in records),
            "locked_test_count": 0,
            "labels_attached_locally": True,
            "locked_test_present": False,
            "source_npz": str(npz_path.relative_to(REPO_ROOT)),
            "source_npz_sha256": npz_sha256,
            "feature_artifact": str(output_path.relative_to(REPO_ROOT)),
            "feature_artifact_sha256": sha256_file(output_path),
        }
        atomic_text(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        output_files.append(metadata)
    summary = {
        "status": "PASS_FORMAL_SCALAR_FEATURE_MATERIALIZATION",
        "candidate": candidate,
        "source_npz": str(npz_path.relative_to(REPO_ROOT)),
        "source_npz_sha256": npz_sha256,
        "record_count": len(records),
        "locked_test_count": 0,
        "feature_names": list(FEATURE_NAMES),
        "outputs": output_files,
    }
    atomic_text(output_dir / "materialization_summary.json", json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--candidate", choices=sorted(LAYERS), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = materialize(args.npz.resolve(), args.output_dir.resolve(), args.candidate)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

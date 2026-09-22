#!/usr/bin/env python3
"""Materialize checked formal representation NPZ arrays as feature JSONL.

This is a deliberately narrow boundary adapter.  The Modal representation
runner writes one packed NPZ per candidate with all predeclared layers and
keeps labels local.  The CPU training code consumes one model/layer/family
JSONL artifact at a time.  This adapter verifies the frozen development
manifest and every array boundary before attaching the local labels.
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

import numpy as np

from evovariant_tr.feature_store import make_feature_record

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
EXPECTED_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
EXPECTED_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
EXPECTED_RECORD_COUNT = 4_000
EXPECTED_LAYERS = {
    "nucleotide_transformer": (8, 16, 24),
    "caduceus": (4, 8, 16),
}
VECTOR_FAMILIES = {
    "forward_delta": "forward_delta",
    "reverse_delta": "reverse_delta",
    "alt_minus_ref_aggregate": "alt_minus_ref_aggregate",
    "abs_alt_minus_ref_aggregate": "abs_alt_minus_ref_aggregate",
}
SCALAR_FAMILIES = {
    "cosine_similarity": "cosine_similarity",
    "distance_l2": "distance_l2",
    "orientation_disagreement_l2": "orientation_disagreement_l2",
}


class MaterializationError(ValueError):
    """Raised when a formal representation artifact is not consumable."""


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
        raise MaterializationError("formal development manifest hash changed")
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("record_set_sha256") != EXPECTED_RECORD_SET_SHA256
    ):
        raise MaterializationError("formal development record-set hash changed")
    raw_records = document.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != EXPECTED_RECORD_COUNT:
        raise MaterializationError("formal development manifest must contain 4,000 records")
    records = [row for row in raw_records if isinstance(row, dict)]
    if len(records) != EXPECTED_RECORD_COUNT:
        raise MaterializationError("formal development manifest contains a non-object record")
    records.sort(key=lambda row: str(row["normalized_variant_id"]))
    if {row.get("split") for row in records} != {"TRAIN", "VALIDATION"}:
        raise MaterializationError("formal development manifest must contain TRAIN and VALIDATION")
    ids = [str(row.get("normalized_variant_id", "")) for row in records]
    if not all(ids) or len(ids) != len(set(ids)):
        raise MaterializationError("formal development manifest IDs are not unique")
    return records


def _array(npz: Any, name: str, *, rows: int, layers: int) -> np.ndarray:
    if name not in npz:
        raise MaterializationError(f"formal representation NPZ lacks {name}")
    value = np.asarray(npz[name])
    if value.shape[0] != rows or value.shape[1] != layers:
        raise MaterializationError(
            f"{name} shape {value.shape} does not begin with ({rows}, {layers})"
        )
    if value.dtype.kind not in "fiu":
        raise MaterializationError(f"{name} has unsupported dtype {value.dtype}")
    if not np.isfinite(value).all():
        raise MaterializationError(f"{name} contains non-finite values")
    return value


def _scalar_array(npz: Any, name: str, *, rows: int, layers: int) -> np.ndarray:
    value = _array(npz, name, rows=rows, layers=layers)
    if value.ndim != 2:
        raise MaterializationError(f"{name} must have shape ({rows}, {layers})")
    return value


def materialize(
    npz_path: Path,
    output_dir: Path,
    *,
    candidate: str,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    if candidate not in EXPECTED_LAYERS:
        raise MaterializationError(f"candidate must be one of {sorted(EXPECTED_LAYERS)}")
    records = load_manifest(manifest_path)
    expected_layers = EXPECTED_LAYERS[candidate]
    npz_sha256 = sha256_file(npz_path)
    with np.load(npz_path, allow_pickle=False) as npz:
        ids = [str(value) for value in np.asarray(npz.get("variant_ids", []))]
        splits = [str(value) for value in np.asarray(npz.get("splits", []))]
        genes = [str(value) for value in np.asarray(npz.get("gene_symbols", []))]
        layers = tuple(int(value) for value in np.asarray(npz.get("layers", [])))
        if ids != [str(row["normalized_variant_id"]) for row in records]:
            raise MaterializationError(
                "NPZ variant IDs do not exactly match sorted formal manifest"
            )
        if splits != [str(row["split"]) for row in records]:
            raise MaterializationError("NPZ splits do not exactly match formal manifest")
        if genes != [str(row["gene_symbol"]) for row in records]:
            raise MaterializationError("NPZ gene symbols do not exactly match formal manifest")
        if layers != expected_layers:
            raise MaterializationError(f"NPZ layers {layers} do not match {expected_layers}")
        labels = np.asarray(npz.get("labels", []))
        expected_labels = np.asarray([int(row["label"]) for row in records], dtype=np.int8)
        if labels.shape != expected_labels.shape or not np.array_equal(labels, expected_labels):
            raise MaterializationError("NPZ labels do not match the local formal manifest")

        arrays: dict[str, np.ndarray] = {}
        for family, key in VECTOR_FAMILIES.items():
            arrays[family] = _array(npz, key, rows=len(records), layers=len(expected_layers))
        for family, key in SCALAR_FAMILIES.items():
            arrays[family] = _scalar_array(
                npz, key, rows=len(records), layers=len(expected_layers)
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files: list[dict[str, Any]] = []
    for family, array in arrays.items():
        for layer_index, layer in enumerate(expected_layers):
            layer_name = f"{layer}:{family}"
            lines: list[str] = []
            for row_index, record in enumerate(records):
                raw_values = array[row_index, layer_index]
                values = np.asarray(raw_values, dtype=np.float32).reshape(-1).tolist()
                if not values or not all(math.isfinite(float(value)) for value in values):
                    raise MaterializationError(f"non-finite feature values for {layer_name}")
                feature = make_feature_record(
                    normalized_variant_id=str(record["normalized_variant_id"]),
                    model_id=candidate,
                    layer=layer_name,
                    split=str(record["split"]),
                    values=values,
                    dtype="float32",
                    gene_symbol=str(record["gene_symbol"]),
                ).to_dict()
                feature.update(
                    {
                        "label": int(record["label"]),
                        "feature_family": family,
                        "source_npz": display_path(npz_path),
                        "source_npz_sha256": npz_sha256,
                        "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                        "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
                        "labels_attached_locally": True,
                        "locked_test_present": False,
                    }
                )
                lines.append(json.dumps(feature, sort_keys=True) + "\n")
            output_path = output_dir / f"{candidate}_layer_{layer}_{family}.jsonl"
            metadata_path = output_path.with_suffix(".metadata.json")
            if output_path.exists() or metadata_path.exists():
                raise MaterializationError(f"refusing to overwrite existing output: {output_path}")
            atomic_text(output_path, "".join(lines))
            metadata = {
                "status": "PASS_FORMAL_FEATURE_MATERIALIZATION",
                "candidate": candidate,
                "model_id": candidate,
                "layer": layer_name,
                "feature_family": family,
                "record_count": len(records),
                "train_count": sum(row["split"] == "TRAIN" for row in records),
                "validation_count": sum(row["split"] == "VALIDATION" for row in records),
                "locked_test_count": 0,
                "labels_attached_locally": True,
                "locked_test_present": False,
                "formal_manifest_path": display_path(manifest_path),
                "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
                "source_npz": display_path(npz_path),
                "source_npz_sha256": npz_sha256,
                "feature_artifact": display_path(output_path),
                "feature_artifact_sha256": sha256_file(output_path),
                "score_semantics": (
                    "representation_difference_or_distance; classifier probability is not implied"
                ),
            }
            atomic_text(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
            output_files.append(metadata)
    summary = {
        "status": "PASS_FORMAL_FEATURE_MATERIALIZATION",
        "candidate": candidate,
        "source_npz": display_path(npz_path),
        "source_npz_sha256": npz_sha256,
        "formal_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "formal_record_set_sha256": EXPECTED_RECORD_SET_SHA256,
        "record_count": len(records),
        "locked_test_count": 0,
        "output_count": len(output_files),
        "outputs": output_files,
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
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--candidate", required=True, choices=sorted(EXPECTED_LAYERS))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        summary = materialize(
            args.npz,
            args.output_dir,
            candidate=args.candidate,
            manifest_path=args.manifest,
        )
    except (MaterializationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

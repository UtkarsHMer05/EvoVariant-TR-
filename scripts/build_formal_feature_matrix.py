#!/usr/bin/env python3
"""Join verified formal feature/comparator families without imputing missing values."""

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
MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"


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


def _parse_assignments(
    values: list[str], label: str, *, required: bool = True
) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise ValueError(f"{label} must use NAME=PATH: {value}")
        parsed.append((name, Path(path).resolve()))
    if required and not parsed:
        raise ValueError(f"at least one {label} is required")
    if len({name for name, _ in parsed}) != len(parsed):
        raise ValueError(f"duplicate {label} names")
    return parsed


def _validate_row(identity: str, row: dict[str, Any]) -> tuple[str, int, str, list[float]]:
    split = str(row.get("split", ""))
    if split not in {"TRAIN", "VALIDATION"} or row.get("locked_test_present") is not False:
        raise ValueError(f"{identity} is not a proven development row")
    label = int(row["label"])
    gene = str(row["gene_symbol"])
    values_raw = row["values"]
    if label not in {0, 1} or not gene or not isinstance(values_raw, list) or not values_raw:
        raise ValueError(f"invalid feature row for {identity}")
    values = [float(value) for value in values_raw]
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"non-finite feature row for {identity}")
    record = make_feature_record(
        normalized_variant_id=identity,
        model_id=str(row["model_id"]),
        layer=str(row["layer"]),
        split=split,
        values=values,
        dtype=str(row.get("dtype", "float32")),
        gene_symbol=gene,
    )
    if record.content_sha256 != row.get("content_sha256"):
        raise ValueError(f"content hash mismatch for {identity}")
    return split, label, gene, values


def _load_feature(path: Path) -> dict[str, tuple[str, int, str, list[float]]]:
    rows: dict[str, tuple[str, int, str, list[float]]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        identity = str(raw["normalized_variant_id"])
        if identity in rows:
            raise ValueError(f"duplicate feature ID {identity} in {path}:{line_number}")
        rows[identity] = _validate_row(identity, raw)
    if not rows:
        raise ValueError(f"feature input is empty: {path}")
    return rows


def _load_comparator(
    path: Path,
    value_key: str,
) -> dict[str, tuple[str, int, str, list[float]]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    raw_rows = document.get("rows")
    if not isinstance(raw_rows, list):
        raise ValueError(f"comparator has no rows: {path}")
    rows: dict[str, tuple[str, int, str, list[float]]] = {}
    for raw in raw_rows:
        identity = str(raw["normalized_variant_id"])
        value = raw.get(value_key)
        if raw.get("status") != "AVAILABLE" or value is None:
            continue
        if identity in rows:
            raise ValueError(f"duplicate comparator ID {identity} in {path}")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"non-finite comparator value for {identity}")
        rows[identity] = ("", int(raw.get("label", 0)), "", [numeric])
    return rows


def build_matrix(
    output: Path,
    model_id: str,
    layer: str,
    feature_inputs: list[tuple[str, Path]],
    comparator_inputs: list[tuple[str, Path, str]],
) -> dict[str, Any]:
    loaded: dict[str, dict[str, tuple[str, int, str, list[float]]]] = {
        name: _load_feature(path) for name, path in feature_inputs
    }
    for name, path, key in comparator_inputs:
        loaded[name] = _load_comparator(path, key)
    identities = set.intersection(*(set(rows) for rows in loaded.values()))
    if not identities:
        raise ValueError("feature inputs have no complete common IDs")
    ordered = sorted(identities)
    base_name = next(iter(loaded))
    lines: list[str] = []
    feature_names: list[str] = []
    for name, _ in feature_inputs:
        width = len(loaded[name][ordered[0]][3])
        feature_names.extend(f"{name}[{index}]" for index in range(width))
    feature_names.extend(name for name, _, _ in comparator_inputs)
    for identity in ordered:
        base = loaded[base_name][identity]
        split, label, gene, _ = base
        values: list[float] = []
        for name, _ in feature_inputs:
            current = loaded[name][identity]
            if current[:3] != base[:3]:
                raise ValueError(f"metadata mismatch for {identity} between {base_name} and {name}")
            values.extend(current[3])
        for name, _, _ in comparator_inputs:
            current = loaded[name][identity]
            if current[0] and current[:3] != base[:3]:
                raise ValueError(f"metadata mismatch for {identity} in comparator {name}")
            values.extend(current[3])
        feature = make_feature_record(
            normalized_variant_id=identity,
            model_id=model_id,
            layer=layer,
            split=split,
            values=values,
            dtype="float64",
            gene_symbol=gene,
        ).to_dict()
        feature.update(
            {
                "label": label,
                "feature_names": feature_names,
                "formal_manifest_sha256": MANIFEST_SHA256,
                "formal_record_set_sha256": RECORD_SET_SHA256,
                "labels_attached_locally": True,
                "locked_test_present": False,
                "source_feature_artifacts": {
                    name: {
                        "path": str(path.relative_to(REPO_ROOT)),
                        "sha256": sha256_file(path),
                    }
                    for name, path in feature_inputs
                },
                "source_comparator_artifacts": {
                    name: {
                        "path": str(path.relative_to(REPO_ROOT)),
                        "sha256": sha256_file(path),
                        "value_key": key,
                    }
                    for name, path, key in comparator_inputs
                },
            }
        )
        lines.append(json.dumps(feature, sort_keys=True) + "\n")
    if output.exists():
        raise ValueError(f"refusing to overwrite {output}")
    atomic_text(output, "".join(lines))
    metadata = {
        "status": "PASS_FORMAL_FEATURE_MATRIX",
        "model_id": model_id,
        "layer": layer,
        "feature_names": feature_names,
        "record_count": len(ordered),
        "train_count": sum(loaded[base_name][i][0] == "TRAIN" for i in ordered),
        "validation_count": sum(loaded[base_name][i][0] == "VALIDATION" for i in ordered),
        "locked_test_count": 0,
        "feature_artifact": str(output.relative_to(REPO_ROOT)),
        "feature_artifact_sha256": sha256_file(output),
        "source_feature_artifacts": {
            name: {"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256_file(path)}
            for name, path in feature_inputs
        },
        "source_comparator_artifacts": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(path),
                "value_key": key,
                "available_rows": len(loaded[name]),
            }
            for name, path, key in comparator_inputs
        },
        "coverage_intersection": {name: len(rows) for name, rows in loaded.items()},
        "missingness_policy": (
            "complete-case intersection; missing comparator scores are not imputed"
        ),
    }
    atomic_text(
        output.with_suffix(".metadata.json"),
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--layer", required=True)
    parser.add_argument("--feature", action="append", default=[])
    parser.add_argument("--comparator", action="append", default=[])
    args = parser.parse_args()
    try:
        feature_inputs = _parse_assignments(args.feature, "feature")
        comparators: list[tuple[str, Path, str]] = []
        for name, assignment in _parse_assignments(
            args.comparator, "comparator", required=False
        ):
            path_text, separator, value_key = str(assignment).rpartition(":")
            if not separator or not value_key:
                raise ValueError("comparator must use NAME=PATH:VALUE_KEY")
            comparators.append((name, Path(path_text).resolve(), value_key))
        result = build_matrix(
            args.output.resolve(), args.model_id, args.layer, feature_inputs, comparators
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

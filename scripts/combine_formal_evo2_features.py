#!/usr/bin/env python3
"""Combine already-verified formal Evo2 feature families for CPU-only Phase 13."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from evovariant_tr.feature_store import make_feature_record

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNT = 4_000
EXPECTED_FAMILIES = {
    "primary": ("delta_primary", 1),
    "forward_reverse": ("delta_forward_reverse", 2),
    "orientation": ("delta_orientation_difference", 1),
}


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


def load(path: Path, family: str, width: int) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        identity = str(row["normalized_variant_id"])
        if identity in rows:
            raise ValueError(f"duplicate ID in {family}: {identity}")
        if row.get("split") == "LOCKED_TEST" or row.get("locked_test_present") is not False:
            raise ValueError(f"locked or unproven row in {family} line {line_number}")
        values = row.get("values")
        if not isinstance(values, list) or len(values) != width:
            raise ValueError(f"unexpected {family} width for {identity}")
        if not all(isinstance(value, (int, float)) for value in values):
            raise ValueError(f"non-numeric {family} value for {identity}")
        rows[identity] = row
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"{family} contains {len(rows)} rows, expected {EXPECTED_COUNT}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--forward-reverse", type=Path, required=True)
    parser.add_argument("--orientation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output_path = args.output.resolve()
    inputs = {
        "primary": args.primary.resolve(),
        "forward_reverse": args.forward_reverse.resolve(),
        "orientation": args.orientation.resolve(),
    }
    if output_path.exists():
        raise ValueError(f"refusing to overwrite {output_path}")
    loaded = {
        name: load(path, EXPECTED_FAMILIES[name][0], EXPECTED_FAMILIES[name][1])
        for name, path in inputs.items()
    }
    identities = sorted(loaded["primary"])
    if any(set(loaded[name]) != set(identities) for name in loaded):
        raise ValueError("feature-family ID sets do not match")
    lines: list[str] = []
    for identity in identities:
        rows = {name: loaded[name][identity] for name in loaded}
        base = rows["primary"]
        for name, row in rows.items():
            for key in (
                "split",
                "label",
                "gene_symbol",
                "model_id",
                "formal_manifest_sha256",
                "formal_record_set_sha256",
            ):
                if row.get(key) != base.get(key):
                    raise ValueError(f"{key} mismatch for {identity} between primary and {name}")
        values = [
            float(rows["primary"]["values"][0]),
            float(rows["forward_reverse"]["values"][0]),
            float(rows["forward_reverse"]["values"][1]),
            float(rows["orientation"]["values"][0]),
        ]
        feature = make_feature_record(
            normalized_variant_id=identity,
            model_id="evo2",
            layer="phase13_combined_evo2",
            split=str(base["split"]),
            values=values,
            dtype="float64",
            gene_symbol=str(base["gene_symbol"]),
        ).to_dict()
        feature.update(
            {
                "label": int(base["label"]),
                "feature_family": (
                    "delta_primary+delta_forward+delta_reverse+orientation_difference"
                ),
                "formal_manifest_sha256": base["formal_manifest_sha256"],
                "formal_record_set_sha256": base["formal_record_set_sha256"],
                "labels_attached_locally": True,
                "locked_test_present": False,
                "source_feature_artifacts": {
                    name: {
                        "path": str(path.relative_to(REPO_ROOT)),
                        "sha256": sha256_file(path),
                    }
                    for name, path in inputs.items()
                },
            }
        )
        lines.append(json.dumps(feature, sort_keys=True) + "\n")
    atomic_text(output_path, "".join(lines))
    metadata = {
        "status": "PASS_FORMAL_CPU_FEATURE_COMBINATION",
        "model_id": "evo2",
        "layer": "phase13_combined_evo2",
        "record_count": len(lines),
        "train_count": sum(
            loaded["primary"][identity]["split"] == "TRAIN" for identity in identities
        ),
        "validation_count": sum(
            loaded["primary"][identity]["split"] == "VALIDATION" for identity in identities
        ),
        "locked_test_count": 0,
        "feature_artifact": str(output_path.relative_to(REPO_ROOT)),
        "feature_artifact_sha256": sha256_file(output_path),
        "source_feature_artifacts": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
    }
    metadata_path = output_path.with_suffix(".metadata.json")
    atomic_text(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

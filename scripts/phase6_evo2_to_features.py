#!/usr/bin/env python3
"""Convert verified development-only Evo2 scores into local feature rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "evo2_7b"
FEATURE_LAYER = "raw_score_orientation_v1"
FEATURE_NAMES = (
    "delta_primary",
    "delta_forward",
    "delta_reverse",
    "orientation_disagreement",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_verified_rows(
    predictions_path: Path,
    source_artifact_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = json.loads(source_artifact_path.read_text(encoding="utf-8"))
    recorded_path = REPO_ROOT / str(source["outputs"]["predictions_jsonl"])
    if recorded_path.resolve() != predictions_path.resolve():
        raise ValueError("predictions path does not match the Phase 6 artifact")
    if _sha256_file(predictions_path) != source["outputs"]["predictions_sha256"]:
        raise ValueError("Phase 6 predictions hash does not match its artifact")
    if source["scientific_boundary"]["locked_test_labels_accessed"]:
        raise ValueError("Phase 6 artifact reports locked-test label access")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    lines = predictions_path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise ValueError(f"prediction line {line_number} is not an object")
        identity = str(raw.get("normalized_variant_id", ""))
        split = str(raw.get("split", ""))
        if not identity or identity in seen:
            raise ValueError(f"duplicate or empty normalized ID on line {line_number}")
        if split not in {"TRAIN", "VALIDATION"}:
            raise ValueError(f"non-development split on line {line_number}: {split!r}")
        if raw.get("coverage_status") != "COMPLETED":
            raise ValueError(f"incomplete prediction on line {line_number}")
        if not isinstance(raw.get("label"), int) or raw["label"] not in {0, 1}:
            raise ValueError(f"invalid label on line {line_number}")
        if not str(raw.get("gene_symbol") or "").strip():
            raise ValueError(f"missing gene symbol on line {line_number}")
        values = []
        for name in FEATURE_NAMES:
            value = float(raw[name])
            if not math.isfinite(value):
                raise ValueError(f"non-finite {name} on line {line_number}")
            values.append(value)
        raw["_feature_values"] = values
        seen.add(identity)
        rows.append(raw)
    if not rows:
        raise ValueError("Phase 6 predictions are empty")
    return rows, source


def _write_feature_artifact(
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    predictions_path: Path,
    source_artifact_path: Path,
    output_path: Path,
    summary_path: Path,
) -> None:
    if output_path.exists() or summary_path.exists():
        raise ValueError("feature output already exists; choose a new development run directory")
    from evovariant_tr.feature_store import make_feature_record

    records: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: str(item["normalized_variant_id"])):
        record = make_feature_record(
            normalized_variant_id=str(row["normalized_variant_id"]),
            model_id=MODEL_ID,
            layer=FEATURE_LAYER,
            split=str(row["split"]),
            values=row["_feature_values"],
            dtype="float64",
            gene_symbol=str(row["gene_symbol"]),
        )
        serialized = record.to_dict()
        # Labels are attached to the local supervised-training row only.  They
        # were never included in the Modal payload or remote response.
        serialized["label"] = int(row["label"])
        records.append(serialized)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    counts = Counter(record["split"] for record in records)
    summary = {
        "status": "COMPLETED_DEVELOPMENT_SUBSET",
        "phase": 7,
        "family": "RAW_SCORE_FEATURE_ADAPTER",
        "model_id": MODEL_ID,
        "layer": FEATURE_LAYER,
        "feature_names": list(FEATURE_NAMES),
        "feature_definition": (
            "four local features from verified Evo2 forward/reverse raw scores: "
            "primary mean delta, forward delta, reverse delta, and absolute "
            "orientation disagreement"
        ),
        "source": {
            "phase6_artifact": str(source_artifact_path.relative_to(REPO_ROOT)),
            "predictions_jsonl": str(predictions_path.relative_to(REPO_ROOT)),
            "predictions_sha256": _sha256_file(predictions_path),
            "protocol_hash": source["protocol_hash"],
            "development_manifest_sha256": source["dataset"]["development_manifest_sha256"],
        },
        "records": len(records),
        "split_counts": dict(sorted(counts.items())),
        "locked_test_evaluated": False,
        "labels_sent_to_modal": source["scientific_boundary"]["labels_sent_to_modal"],
        "feature_artifact": str(output_path.relative_to(REPO_ROOT)),
        "feature_artifact_sha256": _sha256_file(output_path),
        "selection_boundary": "local development rows only; no locked-test labels or selection",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--source-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        predictions_path = args.predictions.resolve()
        source_artifact_path = args.source_artifact.resolve()
        output_path = args.output.resolve()
        summary_path = args.summary.resolve()
        rows, source = _load_verified_rows(predictions_path, source_artifact_path)
        _write_feature_artifact(
            rows,
            source,
            predictions_path,
            source_artifact_path,
            output_path,
            summary_path,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "PASS", "output": str(output_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

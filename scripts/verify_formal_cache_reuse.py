#!/usr/bin/env python3
"""Verify the exact historical Evo2 rows eligible for formal-study reuse.

The earlier 2,848-row run was not selected as a formal sample, but its completed
shards may save remote work for the 56 IDs that happen to overlap the frozen
``ML-DEV-BUDGETED-001`` manifests. This verifier accepts those rows only when
the historical execution plan, shard integrity, model contract, raw scores, and
formal variant identity all agree. It deliberately does not treat the old run
as representative and writes no labels into the reuse artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FORMAL_MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
OLD_PREDICTIONS = REPO_ROOT / ("research/runs/phase6_development_evo2_20260921/predictions.jsonl")
OLD_PLAN = REPO_ROOT / "research/runs/phase6_development_evo2_20260921/execution_plan.json"
OLD_ARTIFACT = REPO_ROOT / "artifacts/phase6/phase6_development_evo2_20260921.json"
OLD_SHARDS = REPO_ROOT / "research/runs/phase6_development_evo2_20260921/shards"
PROTOCOL_HASHES = REPO_ROOT / "research/ml_extension/protocol_hashes.json"
OUTPUT = REPO_ROOT / "artifacts/phase6/formal_budgeted_cache_reuse_verification_20260921.json"
EXPECTED_OVERLAP = 56
EXPECTED_MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def stable_hash(value: object) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def current_protocol_hash() -> str:
    document = read_json(PROTOCOL_HASHES)
    value = document["files"]["research/ml_extension/protocol.yaml"]
    if not isinstance(value, str) or len(value) != 64:
        raise RuntimeError("current protocol hash is invalid")
    return value


def load_predictions() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with OLD_PREDICTIONS.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"historical prediction line {line_number} is not an object")
            identity = str(row.get("normalized_variant_id", ""))
            if not identity or identity in rows:
                raise RuntimeError(
                    f"historical predictions have a duplicate/missing ID: {identity}"
                )
            rows[identity] = row
    if len(rows) != 2_848:
        raise RuntimeError(f"historical predictions must contain 2,848 rows, got {len(rows)}")
    return rows


def verify_shards(
    prediction_ids: set[str],
    plan_hash: str,
) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(OLD_SHARDS.glob("shard_*.json")):
        document = read_json(path)
        if not isinstance(document, dict):
            raise RuntimeError(f"historical shard is not an object: {path}")
        payload = dict(document)
        recorded_hash = payload.pop("payload_sha256", None)
        if recorded_hash != stable_hash(payload):
            raise RuntimeError(f"historical shard payload hash mismatch: {path}")
        if payload.get("execution_plan_sha256") != plan_hash:
            raise RuntimeError(f"historical shard plan hash mismatch: {path}")
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise RuntimeError(f"historical shard rows are invalid: {path}")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"historical shard row is invalid: {path}")
            identity = str(row.get("normalized_variant_id", ""))
            if identity in prediction_ids:
                if identity in found:
                    raise RuntimeError(f"historical ID occurs in multiple shards: {identity}")
                found[identity] = {
                    "source_shard": str(path.relative_to(REPO_ROOT)),
                    "source_shard_sha256": sha256_file(path),
                    "source_payload_sha256": recorded_hash,
                    "row": row,
                }
    return found


def verify_row(identity: str, row: dict[str, Any], formal: dict[str, Any]) -> dict[str, Any]:
    if row.get("coverage_status") != "COMPLETED" or row.get("failure_reason") is not None:
        raise RuntimeError(f"historical row is not a completed cache result: {identity}")
    if row.get("normalized_variant_id") != identity or row.get("split") != formal.get("split"):
        raise RuntimeError(f"historical/formal identity metadata mismatch: {identity}")
    if row.get("gene_symbol") != formal.get("gene_symbol"):
        raise RuntimeError(f"historical/formal gene mismatch: {identity}")
    provenance = row.get("provenance")
    expected_provenance = {
        "checkpoint": "evo2_7b",
        "context_length_bp": 8192,
        "label_attached_after_remote_response": True,
        "model_id": "evo2_7b",
        "model_revision": EXPECTED_MODEL_REVISION,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
    }
    if provenance != expected_provenance:
        raise RuntimeError(f"historical provenance is incompatible: {identity}")
    raw_scores = row.get("raw_scores")
    if not isinstance(raw_scores, dict):
        raise RuntimeError(f"historical raw scores are missing: {identity}")
    names = ("reference_forward", "alternate_forward", "reference_reverse", "alternate_reverse")
    if any(name not in raw_scores for name in names):
        raise RuntimeError(f"historical raw score orientation set is incomplete: {identity}")
    values = {name: float(raw_scores[name]) for name in names}
    if not all(math.isfinite(value) for value in values.values()):
        raise RuntimeError(f"historical raw scores are non-finite: {identity}")
    forward = values["alternate_forward"] - values["reference_forward"]
    reverse = values["alternate_reverse"] - values["reference_reverse"]
    if not math.isclose(float(row.get("delta_forward")), forward, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError(f"historical forward delta mismatch: {identity}")
    if not math.isclose(float(row.get("delta_reverse")), reverse, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError(f"historical reverse delta mismatch: {identity}")
    if not math.isclose(
        float(row.get("delta_primary")), (forward + reverse) / 2, rel_tol=0, abs_tol=1e-12
    ):
        raise RuntimeError(f"historical aggregate delta mismatch: {identity}")
    return {
        "normalized_variant_id": identity,
        "split": str(row["split"]),
        "gene_symbol": row.get("gene_symbol"),
        "raw_scores": values,
        "delta_forward": forward,
        "delta_reverse": reverse,
        "delta_primary": (forward + reverse) / 2,
        "orientation_disagreement": abs(forward - reverse),
        "coverage_status": "COMPLETED",
        "cache_reuse_basis": "verified_historical_completed_shard",
    }


def main() -> int:
    formal_document = read_json(FORMAL_MANIFEST)
    formal_rows = formal_document.get("records")
    if not isinstance(formal_rows, list) or len(formal_rows) != 4_000:
        raise RuntimeError("formal manifest must contain exactly 4,000 records")
    formal_by_id = {str(row["normalized_variant_id"]): row for row in formal_rows}
    if len(formal_by_id) != len(formal_rows):
        raise RuntimeError("formal manifest contains duplicate IDs")
    predictions = load_predictions()
    overlap = sorted(set(formal_by_id) & set(predictions))
    if len(overlap) != EXPECTED_OVERLAP:
        raise RuntimeError(
            f"expected {EXPECTED_OVERLAP} formal/historical overlaps, got {len(overlap)}"
        )
    old_plan = read_json(OLD_PLAN)
    old_artifact = read_json(OLD_ARTIFACT)
    for source, key, expected in (
        (old_plan, "model_id", "evo2_7b"),
        (old_plan, "checkpoint", "evo2_7b"),
        (old_plan, "model_revision", EXPECTED_MODEL_REVISION),
        (old_plan, "gpu_type", "H100"),
        (old_plan, "context_length_bp", 8192),
        (old_plan, "orientation", "forward_and_reverse"),
        (old_plan, "score_semantics", "alternate_minus_reference_log_likelihood"),
        (old_plan, "labels_remote_transport", False),
        (old_artifact, "status", "PARTIAL_BUDGET_STOP"),
    ):
        if source.get(key) != expected:
            raise RuntimeError(f"historical contract mismatch for {key}: {source.get(key)!r}")
    plan_hash = str(old_plan.get("execution_plan_sha256"))
    if plan_hash != sha256_file(OLD_PLAN):
        # The stored plan hash is the hash of the plan without this self-referential field.
        plan_without_hash = dict(old_plan)
        plan_without_hash.pop("execution_plan_sha256", None)
        if plan_hash != stable_hash(plan_without_hash):
            raise RuntimeError("historical execution plan hash is not self-consistent")
    shard_rows = verify_shards(set(overlap), plan_hash)
    if set(shard_rows) != set(overlap):
        raise RuntimeError("not every formal overlap is present in a verified historical shard")
    verified_rows = []
    for identity in overlap:
        row = verify_row(identity, predictions[identity], formal_by_id[identity])
        row.update({key: value for key, value in shard_rows[identity].items() if key != "row"})
        verified_rows.append(row)

    output = {
        "artifact_id": "formal-budgeted-cache-reuse-verification-20260921",
        "status": "PASS_COMPATIBLE_CACHE_REUSE_56",
        "study_id": "ML-DEV-BUDGETED-001",
        "record_count": len(verified_rows),
        "formal_manifest_path": str(FORMAL_MANIFEST.relative_to(REPO_ROOT)),
        "formal_manifest_sha256": sha256_file(FORMAL_MANIFEST),
        "historical_predictions_path": str(OLD_PREDICTIONS.relative_to(REPO_ROOT)),
        "historical_predictions_sha256": sha256_file(OLD_PREDICTIONS),
        "historical_execution_plan_path": str(OLD_PLAN.relative_to(REPO_ROOT)),
        "historical_execution_plan_sha256": sha256_file(OLD_PLAN),
        "historical_artifact_path": str(OLD_ARTIFACT.relative_to(REPO_ROOT)),
        "historical_artifact_sha256": sha256_file(OLD_ARTIFACT),
        "source_protocol_hash": str(old_plan["protocol_hash"]),
        "current_protocol_hash": current_protocol_hash(),
        "model": {
            "model_id": "evo2_7b",
            "checkpoint": "evo2_7b",
            "revision": EXPECTED_MODEL_REVISION,
            "gpu": "H100",
            "context_length_bp": 8192,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
        },
        "cache_identity_boundary": {
            "status": "COMPATIBLE_HISTORICAL_SHARD_ROWS",
            "content_addressed_cache_key": None,
            "note": (
                "The historical runner recorded verified shard payloads rather than a separate "
                "content-addressed cache key. Reuse is limited to these 56 rows after exact "
                "model/provenance/identity/raw-score verification; no representativeness claim "
                "is made and no other historical row is implicitly reused."
            ),
        },
        "verified_rows": verified_rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": output["status"],
                "record_count": len(verified_rows),
                "artifact": str(OUTPUT.relative_to(REPO_ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

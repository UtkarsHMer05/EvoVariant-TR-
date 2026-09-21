#!/usr/bin/env python3
"""Validate the deterministic formal Evo2 preflight and project the full cost.

This gate is intentionally local and label-aware only after the sample artifact
has returned.  It does not make a remote request.  A full formal Evo2 run is
allowed only when the 64-row artifact is complete, provenance-safe, and its
conservative projection remains below the runner safety stop.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ARTIFACT = REPO_ROOT / "artifacts/phase6/phase6_formal_evo2_20260921_sample64.json"
COST_ESTIMATE = (
    REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921/cost_estimate.json"
)
OUTPUT = REPO_ROOT / "artifacts/phase6/formal_budgeted_preflight_gate_20260921.json"
SAMPLE_ROWS = 64
FORMAL_ROWS = 4_000
FORMAL_NEW_ROWS = 3_944
SAFETY_STOP_USD = 7.75
HARD_CAP_USD = 8.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    sample = read_json(SAMPLE_ARTIFACT)
    estimate = read_json(COST_ESTIMATE)
    errors: list[str] = []

    if sample.get("status") != "PASS_FORMAL_SAMPLE":
        errors.append("sample artifact status is not PASS_FORMAL_SAMPLE")
    dataset = sample.get("dataset")
    if not isinstance(dataset, dict):
        errors.append("sample artifact dataset is missing")
        dataset = {}
    if dataset.get("full_development_records") != FORMAL_ROWS:
        errors.append("sample artifact source cohort is not 4,000 rows")
    if dataset.get("execution_record_count") != SAMPLE_ROWS:
        errors.append("sample artifact execution count is not 64 rows")
    if dataset.get("processed_records") != SAMPLE_ROWS:
        errors.append("sample artifact processed count is not 64 rows")
    if dataset.get("remaining_records") != 0:
        errors.append("sample artifact did not complete its selected 64-row prefix")

    if sample.get("scientific_boundary", {}).get("labels_sent_to_modal") is not False:
        errors.append("sample artifact does not prove labels were excluded from Modal")
    model = sample.get("model")
    if not isinstance(model, dict) or model.get("model_revision") != (
        "4b509ec2a22d6de472659f908bcb0714265ad3a7"
    ):
        errors.append("sample artifact model revision is not the approved Evo2 revision")
    if not isinstance(model, dict) or model.get("context_length_bp") != 8192:
        errors.append("sample artifact context length is not 8192 bp")
    if not isinstance(model, dict) or model.get("orientation") != "forward_and_reverse":
        errors.append("sample artifact orientation is not forward_and_reverse")

    outputs = sample.get("outputs")
    prediction_path = None
    if isinstance(outputs, dict) and isinstance(outputs.get("predictions_jsonl"), str):
        prediction_path = REPO_ROOT / outputs["predictions_jsonl"]
        if not prediction_path.is_file():
            errors.append("sample predictions JSONL is missing")
        elif outputs.get("predictions_sha256") != sha256_file(prediction_path):
            errors.append("sample predictions JSONL hash does not match the artifact")
    else:
        errors.append("sample predictions output is not registered")

    if prediction_path is not None and prediction_path.is_file():
        rows = [
            json.loads(line)
            for line in prediction_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ids = [row.get("normalized_variant_id") for row in rows if isinstance(row, dict)]
        if len(rows) != SAMPLE_ROWS or len(set(ids)) != SAMPLE_ROWS:
            errors.append("sample predictions do not contain 64 unique rows")
        for row in rows:
            if not isinstance(row, dict):
                errors.append("sample prediction row is not an object")
                continue
            for key in ("delta_forward", "delta_reverse", "delta_primary"):
                value = row.get(key)
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    errors.append(f"sample prediction {key} is not finite")

    cache = sample.get("cache")
    historical_hits = (
        int(cache.get("historical_cache_reuse_records", 0))
        if isinstance(cache, dict)
        else 0
    )
    processed = int(dataset.get("processed_records", 0))
    remote_new_rows = processed - historical_hits
    cost = sample.get("cost")
    measured_sample_usd = (
        float(cost.get("cumulative_client_wall_rate_estimate_usd", math.nan))
        if isinstance(cost, dict)
        else math.nan
    )
    if not math.isfinite(measured_sample_usd) or measured_sample_usd < 0:
        errors.append("sample cost estimate is missing or non-finite")
    if remote_new_rows <= 0:
        errors.append("sample contains no new remote rows for a rate projection")

    estimate_evo2 = float(estimate["evo2"]["estimated_usd"])
    estimate_nt = float(
        estimate["nucleotide_transformer"]["config"].get(
            "estimated_usd", estimate["nucleotide_transformer"].get("estimated_usd", 0.0)
        )
    )
    estimate_cad = float(
        estimate["caduceus"]["config"].get(
            "estimated_usd", estimate["caduceus"].get("estimated_usd", 0.0)
        )
    )
    # The checked-in estimate is the minimum frozen planning basis.  The
    # measured sample rate can only increase the Evo2 component.
    measured_rate = measured_sample_usd / remote_new_rows if remote_new_rows > 0 else math.nan
    scaled_evo2 = measured_rate * FORMAL_NEW_ROWS if math.isfinite(measured_rate) else math.inf
    projected_evo2 = max(estimate_evo2, scaled_evo2)
    projected_total = projected_evo2 + estimate_nt + estimate_cad
    if projected_total > SAFETY_STOP_USD:
        errors.append(
            "projected cumulative additional cost exceeds safety stop: "
            f"{projected_total:.6f} > {SAFETY_STOP_USD:.2f}"
        )
    if projected_total > HARD_CAP_USD:
        errors.append(
            "projected cumulative additional cost exceeds hard cap: "
            f"{projected_total:.6f} > {HARD_CAP_USD:.2f}"
        )

    status = "PASS_FORMAL_PREFLIGHT_WITHIN_BUDGET" if not errors else "FAIL_FORMAL_PREFLIGHT"
    artifact = {
        "artifact_id": "formal-budgeted-preflight-gate-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "formal_full_launch_authorized": status == "PASS_FORMAL_PREFLIGHT_WITHIN_BUDGET",
        "sample": {
            "artifact_path": str(SAMPLE_ARTIFACT.relative_to(REPO_ROOT)),
            "artifact_sha256": sha256_file(SAMPLE_ARTIFACT),
            "status": sample.get("status"),
            "processed_records": processed,
            "historical_cache_reuse_records": historical_hits,
            "new_remote_records": remote_new_rows,
            "measured_client_wall_rate_estimate_usd": measured_sample_usd,
            "measured_usd_per_new_remote_record": measured_rate,
        },
        "projection": {
            "formal_total_records": FORMAL_ROWS,
            "formal_new_evo2_records": FORMAL_NEW_ROWS,
            "frozen_evo2_estimate_usd": estimate_evo2,
            "sample_rate_scaled_evo2_estimate_usd": scaled_evo2,
            "projected_evo2_usd": projected_evo2,
            "planned_nucleotide_transformer_usd": estimate_nt,
            "planned_caduceus_usd": estimate_cad,
            "projected_cumulative_additional_usd": projected_total,
            "runner_safety_stop_usd": SAFETY_STOP_USD,
            "hard_cap_usd": HARD_CAP_USD,
        },
        "planning_basis": {
            "cost_estimate_path": str(COST_ESTIMATE.relative_to(REPO_ROOT)),
            "cost_estimate_sha256": sha256_file(COST_ESTIMATE),
            "conservative_rule": (
                "max(frozen Evo2 estimate, measured 64-row rate scaled to 3,944 new rows) "
                "plus frozen NT/Caduceus estimates"
            ),
        },
        "errors": errors,
        "labels_sent_to_modal": False,
        "locked_test_access": "prohibited",
    }
    atomic_write(OUTPUT, artifact)
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

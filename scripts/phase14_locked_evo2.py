#!/usr/bin/env python3
"""Run the one-shot, label-blind Phase 14 locked Evo2 evaluation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from evovariant_tr.metrics import bootstrap_auc_ci, compute_auc_pr, compute_auc_roc  # noqa: E402
from evovariant_tr.prediction_calibration import apply_isotonic, probability_metrics  # noqa: E402
from evovariant_tr.supervised import LogisticModel  # noqa: E402
from validate_phase14_approval import validate_approval  # noqa: E402

SHARD_SIZE = 32
GPU_RATE_USD_PER_HOUR = 3.95
MAX_RETRIES = 3
EXPECTED_LOCKED_ROWS = 946
EXPECTED_HARD_CAP_USD = 2.75
EXPECTED_SAFETY_STOP_USD = 2.50


def _stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, value: object) -> None:
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


def _atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _billing_snapshot(repo_root: Path) -> dict[str, Any]:
    modal = Path(sys.executable).with_name("modal")
    try:
        result = subprocess.run(
            [str(modal), "billing", "summary", "--json"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        parsed: Any
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {"stdout": result.stdout}
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary --json",
            "returncode": result.returncode,
            "summary": parsed,
            "stderr": result.stderr,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary --json",
            "returncode": None,
            "summary": {},
            "stderr": f"{type(exc).__name__}:{exc}",
        }


def _load_identity_rows(manifest_path: Path) -> list[dict[str, Any]]:
    """Load locked identities without reading label values."""
    document = _read_json(manifest_path)
    raw_records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(raw_records, list):
        raise RuntimeError("locked manifest does not contain a records list")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_records:
        if not isinstance(raw, dict):
            raise RuntimeError("locked manifest contains a non-object row")
        if raw.get("split") != "LOCKED_TEST":
            raise RuntimeError("locked manifest contains a non-LOCKED_TEST row")
        identity = str(raw.get("normalized_variant_id", ""))
        if not identity or identity in seen:
            raise RuntimeError(f"duplicate or empty locked identity: {identity}")
        required = (
            "assembly",
            "chromosome",
            "position_1based",
            "reference",
            "alternate",
            "gene_symbol",
        )
        if any(key not in raw for key in required):
            raise RuntimeError(f"locked identity row is missing a canonical field: {identity}")
        records.append({key: raw[key] for key in (*required, "normalized_variant_id", "split")})
        seen.add(identity)
    if len(records) != EXPECTED_LOCKED_ROWS:
        raise RuntimeError(
            f"locked manifest must contain exactly {EXPECTED_LOCKED_ROWS} identities"
        )
    records.sort(key=lambda row: str(row["normalized_variant_id"]))
    return records


def _load_labels_after_raw_hash(manifest_path: Path, expected_ids: set[str]) -> dict[str, int]:
    document = _read_json(manifest_path)
    raw_records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(raw_records, list):
        raise RuntimeError("locked manifest does not contain a records list")
    labels: dict[str, int] = {}
    for raw in raw_records:
        if not isinstance(raw, dict) or raw.get("split") != "LOCKED_TEST":
            continue
        identity = str(raw.get("normalized_variant_id", ""))
        if identity not in expected_ids:
            raise RuntimeError(f"label join found an unexpected locked identity: {identity}")
        value = raw.get("label")
        if not isinstance(value, int) or value not in {0, 1}:
            raise RuntimeError(f"label join found a non-binary label: {identity}")
        if identity in labels:
            raise RuntimeError(f"label join found a duplicate identity: {identity}")
        labels[identity] = value
    if set(labels) != expected_ids:
        raise RuntimeError("label join did not cover exactly the raw prediction IDs")
    if (
        sum(value == 0 for value in labels.values()) != 536
        or sum(value == 1 for value in labels.values()) != 410
    ):
        raise RuntimeError("locked label counts differ from the frozen 536/410 cohort")
    return labels


def _read_verified_shard(path: Path, plan_hash: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    document = _read_json(path)
    if not isinstance(document, dict):
        raise RuntimeError(f"invalid shard object: {path}")
    payload = dict(document)
    recorded = payload.pop("payload_sha256", None)
    if not isinstance(recorded, str) or recorded != _sha256_bytes(_stable_bytes(payload)):
        raise RuntimeError(f"tampered shard payload: {path}")
    if payload.get("execution_plan_sha256") != plan_hash or payload.get("status") != "COMPLETED":
        raise RuntimeError(f"shard plan/status mismatch: {path}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"shard rows are malformed: {path}")
    if any("label" in row for row in rows):
        raise RuntimeError(f"label-bearing shard crossed the raw-inference boundary: {path}")
    return payload


def _write_verified_shard(path: Path, payload: dict[str, Any]) -> None:
    document = dict(payload)
    document["payload_sha256"] = _sha256_bytes(_stable_bytes(payload))
    _atomic_json(path, document)


def _is_clearly_transient(exc: BaseException) -> bool:
    name = type(exc).__name__.casefold()
    message = str(exc).casefold()
    tokens = (
        "timeout",
        "streamterminated",
        "temporarily unavailable",
        "service unavailable",
        "deadline exceeded",
        "connection reset",
        "connection aborted",
        "internal server error",
    )
    return any(token in name or token in message for token in tokens)


def _function_call_id(call: Any) -> str | None:
    for name in ("object_id", "function_call_id", "id"):
        value = getattr(call, name, None)
        if isinstance(value, str) and value:
            return value
    return None


def _raw_row(
    identity_row: dict[str, Any],
    remote_row: dict[str, Any],
    reference_provenance: dict[str, Any],
    remote_provenance: dict[str, Any],
) -> dict[str, Any]:
    if "label" in remote_row or "label" in remote_provenance:
        raise RuntimeError("remote response contains a label")
    raw_scores = remote_row.get("raw_scores")
    if not isinstance(raw_scores, list) or len(raw_scores) != 4:
        raise RuntimeError("remote response did not contain four orientation scores")
    scores = [float(value) for value in raw_scores]
    if not all(math.isfinite(value) for value in scores):
        raise RuntimeError("remote response contained a non-finite orientation score")
    reference_forward, alternate_forward, reference_reverse, alternate_reverse = scores
    delta_forward = alternate_forward - reference_forward
    delta_reverse = alternate_reverse - reference_reverse
    delta_primary = (delta_forward + delta_reverse) / 2.0
    orientation_difference = abs(delta_forward - delta_reverse)
    if not all(
        math.isfinite(value)
        for value in (delta_forward, delta_reverse, delta_primary, orientation_difference)
    ):
        raise RuntimeError("remote response produced a non-finite derived score")
    provenance = dict(remote_provenance)
    provenance.update(reference_provenance)
    return {
        "normalized_variant_id": identity_row["normalized_variant_id"],
        "split": "LOCKED_TEST",
        "gene_symbol": identity_row["gene_symbol"],
        "raw_scores": {
            "reference_forward": reference_forward,
            "alternate_forward": alternate_forward,
            "reference_reverse": reference_reverse,
            "alternate_reverse": alternate_reverse,
        },
        "delta_forward": delta_forward,
        "delta_reverse": delta_reverse,
        "delta_primary": delta_primary,
        "orientation_disagreement": orientation_difference,
        "coverage_status": "COMPLETED",
        "failure_reason": None,
        "provenance": provenance,
        "remote_labels_transported": False,
        "locked_test_evaluated": False,
    }


def _label_join_and_evaluate(
    *,
    raw_rows: list[dict[str, Any]],
    manifest_path: Path,
    config: dict[str, Any],
    repo_root: Path,
    raw_path: Path,
    model_artifact_path: Path,
    calibration_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected_ids = {str(row["normalized_variant_id"]) for row in raw_rows}
    labels = _load_labels_after_raw_hash(manifest_path, expected_ids)
    model_raw = _read_json(model_artifact_path)
    parameters = model_raw.get("parameters")
    if not isinstance(parameters, dict):
        raise RuntimeError("fitted model artifact has no parameters")
    model = LogisticModel(
        tuple(float(value) for value in parameters["weights"]),
        float(parameters["bias"]),
        int(parameters["seed"]),
        int(parameters["steps"]),
    )
    calibration = _read_json(calibration_path)
    isotonic = calibration.get("methods", {}).get("isotonic")
    if not isinstance(isotonic, dict):
        raise RuntimeError("frozen isotonic mapping is missing")
    threshold = float(config["score_threshold"])
    joined: list[dict[str, Any]] = []
    for row in sorted(raw_rows, key=lambda item: str(item["normalized_variant_id"])):
        features = (
            float(row["delta_primary"]),
            float(row["delta_forward"]),
            float(row["delta_reverse"]),
            float(row["orientation_disagreement"]),
        )
        classifier_score = float(model.predict_proba(features))
        calibrated_score = float(apply_isotonic([classifier_score], isotonic)[0])
        if not math.isfinite(classifier_score) or not math.isfinite(calibrated_score):
            raise RuntimeError("classifier or calibrated locked score is non-finite")
        joined.append(
            {
                **row,
                "label": labels[str(row["normalized_variant_id"])],
                "feature_values": list(features),
                "classifier_score": classifier_score,
                "calibrated_score": calibrated_score,
                "prediction": int(calibrated_score >= threshold),
                "locked_test_evaluated": True,
            }
        )
    scores = [float(row["calibrated_score"]) for row in joined]
    raw_scores = [float(row["delta_primary"]) for row in joined]
    label_values = [int(row["label"]) for row in joined]
    if (
        len(joined) != EXPECTED_LOCKED_ROWS
        or len({row["normalized_variant_id"] for row in joined}) != EXPECTED_LOCKED_ROWS
    ):
        raise RuntimeError("locked evaluation did not produce exactly 946 unique rows")
    if not all(math.isfinite(value) for value in scores + raw_scores):
        raise RuntimeError("locked calibrated or aggregate scores are non-finite")
    metrics = {
        "auroc": compute_auc_roc(scores, label_values),
        "auprc": compute_auc_pr(scores, label_values),
        "probability_metrics": probability_metrics(scores, label_values),
        "threshold": threshold,
        "n_positive": sum(label_values),
        "n_negative": len(label_values) - sum(label_values),
    }
    bootstrap_mean, bootstrap_std, bootstrap_ci = bootstrap_auc_ci(
        scores,
        label_values,
        n_bootstrap=int(config["bootstrap"]["replicates"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    metrics["bootstrap_auc_mean"] = bootstrap_mean
    metrics["bootstrap_auc_std"] = bootstrap_std
    metrics["bootstrap_auc_ci95"] = list(bootstrap_ci)
    metrics["raw_delta_primary_auroc"] = compute_auc_roc(raw_scores, label_values)
    coverage = float(config["abstention"]["coverage"])
    keep_count = max(1, int(len(joined) * coverage))
    ranked = sorted(joined, key=lambda row: -(
        0.5 + 0.5 * abs(math.tanh(float(row["delta_primary"]) / 10.0))
    ))
    kept = ranked[:keep_count]
    selective_errors = sum(
        (1 if float(row["delta_primary"]) > 0 else 0) != int(row["label"]) for row in kept
    )
    metrics["abstention"] = {
        "method": config["abstention"]["method"],
        "target_coverage": coverage,
        "actual_coverage": keep_count / len(joined),
        "abstained_count": len(joined) - keep_count,
        "risk": selective_errors / keep_count,
        "selection_split": config["abstention"]["selection_split"],
    }
    if not all(
        math.isfinite(float(value))
        for value in (
            metrics["auroc"],
            metrics["auprc"],
            metrics["bootstrap_auc_mean"],
            metrics["bootstrap_auc_std"],
        )
    ):
        raise RuntimeError("final statistical outputs are non-finite")
    return joined, metrics


def run_phase14(
    *,
    worker_cls: Any,
    prepare_batch: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    repo_root: Path = REPO_ROOT,
) -> None:
    approval_path = repo_root / os.environ.get(
        "EVOVARIANT_TR_FORMAL_APPROVAL_PATH",
        "artifacts/approvals/phase14_locked_evo2_20260922.json",
    )
    approval = validate_approval(approval_path)
    from evovariant_tr.cost_policy import assert_paid_compute_allowed

    assert_paid_compute_allowed()
    config_path = repo_root / approval["frozen_config"]["path"]
    config = _read_json(config_path)
    manifest_path = repo_root / approval["dataset"]["locked_test"]["path"]
    model_artifact_path = repo_root / config["model"]["artifact_path"]
    calibration_path = repo_root / config["calibration"]["artifact_path"]
    identity_rows = _load_identity_rows(manifest_path)
    expected_ids = [str(row["normalized_variant_id"]) for row in identity_rows]
    if len(expected_ids) != EXPECTED_LOCKED_ROWS or expected_ids != sorted(expected_ids):
        raise RuntimeError("locked identity preflight did not produce 946 sorted IDs")

    run_root = repo_root / "research/runs/formal_cpu_20260922/phase14_locked_evo2"
    shard_root = run_root / "shards"
    plan_path = run_root / "execution_plan.json"
    raw_path = run_root / "raw_predictions.jsonl"
    joined_path = run_root / "predictions_with_local_labels.jsonl"
    final_path = repo_root / "artifacts/phase14/phase14_locked_evo2_20260922.json"
    if final_path.exists():
        raise RuntimeError(f"Phase 14 final artifact already exists: {final_path}")

    plan_payload = {
        "phase": 14,
        "family": "LOCKED_STATISTICAL_EVALUATION",
        "model_id": "evo2_7b",
        "model_revision": config["model_contract"]["revision"],
        "checkpoint": config["model_contract"]["checkpoint"],
        "protocol_hash": config["protocol_hashes"]["ml_extension_protocol"]["sha256"],
        "research_protocol_hash": config["protocol_hashes"]["research_protocol"]["sha256"],
        "frozen_config_sha256": approval["frozen_config"]["sha256"],
        "frozen_config_file_sha256": _sha256_file(config_path),
        "locked_manifest_sha256": approval["dataset"]["locked_test"]["sha256"],
        "record_count": EXPECTED_LOCKED_ROWS,
        "submission_ids_sha256": _sha256_bytes(_stable_bytes(expected_ids)),
        "shard_size": SHARD_SIZE,
        "include_labels_in_remote_request": False,
        "raw_artifact_before_local_label_join": True,
        "retry_policy": "clearly_transient_shard_failures_only",
    }
    plan_hash = _sha256_bytes(_stable_bytes(plan_payload))
    plan = {**plan_payload, "execution_plan_sha256": plan_hash}
    if plan_path.exists():
        if _read_json(plan_path) != plan:
            raise RuntimeError("existing Phase 14 execution plan differs from the approval")
    else:
        _atomic_json(plan_path, plan)

    billing_before = _billing_snapshot(repo_root)
    started = time.monotonic()
    worker = worker_cls()
    all_raw: list[dict[str, Any]] = []
    cache_hit_rows = 0
    reused_shards = 0
    new_shards = 0
    remote_invocations = 0
    transient_retries = 0
    estimated_cost = 0.0
    client_wall_seconds = 0.0
    remote_runtime_seconds = 0.0
    function_call_ids: list[str] = []
    failure: str | None = None

    shard_count = (len(identity_rows) + SHARD_SIZE - 1) // SHARD_SIZE
    for shard_index, start in enumerate(range(0, len(identity_rows), SHARD_SIZE)):
        shard_records = identity_rows[start : start + SHARD_SIZE]
        shard_path = shard_root / f"shard_{shard_index:06d}.json"
        stored = _read_verified_shard(shard_path, plan_hash)
        if stored is not None:
            stored_ids = [str(row["normalized_variant_id"]) for row in stored["rows"]]
            expected_shard_ids = [str(row["normalized_variant_id"]) for row in shard_records]
            if stored.get("source_ids") != expected_shard_ids or stored_ids != expected_shard_ids:
                raise RuntimeError(f"stored Phase 14 shard identities differ: {shard_path}")
            all_raw.extend(stored["rows"])
            cache_hit_rows += len(stored["rows"])
            reused_shards += 1
            continue
        if estimated_cost >= EXPECTED_SAFETY_STOP_USD:
            failure = "safety stop reached before the next shard"
            break
        try:
            prepared = prepare_batch(shard_records)
            reference_provenance = {
                str(item["normalized_variant_id"]): dict(item["reference_provenance"])
                for item in prepared
            }
            payload = [
                {key: value for key, value in item.items() if key != "reference_provenance"}
                for item in prepared
            ]
        except Exception as exc:  # noqa: BLE001 - preserve fail-closed input errors
            failure = f"{type(exc).__name__}: {exc}"
            break

        response: dict[str, Any] | None = None
        call_id: str | None = None
        shard_call_wall_seconds = 0.0
        for attempt in range(MAX_RETRIES):
            call_started = time.monotonic()
            try:
                remote_invocations += 1
                call = worker.score_batch.spawn(payload)
                call_id = _function_call_id(call)
                response = call.get(timeout=900)
                call_wall_seconds = time.monotonic() - call_started
                client_wall_seconds += call_wall_seconds
                shard_call_wall_seconds += call_wall_seconds
                break
            except Exception as exc:  # noqa: BLE001 - retry classification is explicit
                call_wall_seconds = time.monotonic() - call_started
                client_wall_seconds += call_wall_seconds
                shard_call_wall_seconds += call_wall_seconds
                if attempt + 1 < MAX_RETRIES and _is_clearly_transient(exc):
                    transient_retries += 1
                    continue
                failure = f"{type(exc).__name__}: {exc}"
                break
        if failure is not None or response is None:
            break
        call_id = call_id or None
        if call_id:
            function_call_ids.append(call_id)
        # The provider's own method runtime is the scientific remote-runtime measure.
        if response.get("status") != "completed":
            failure = "remote response status is not completed"
            break
        remote_provenance = response.get("provenance")
        if not isinstance(remote_provenance, dict):
            failure = "remote response has no provenance object"
            break
        for key, expected in {
            "model_id": config["model_contract"]["model_id"],
            "checkpoint": config["model_contract"]["checkpoint"],
            "model_revision": config["model_contract"]["revision"],
            "gpu_type": config["model_contract"]["gpu"],
            "context_length_bp": config["model_contract"]["context_length_bp"],
            "orientation": config["model_contract"]["orientation"],
            "score_semantics": config["model_contract"]["score_semantics"],
        }.items():
            if remote_provenance.get(key) != expected:
                failure = f"remote provenance mismatch for {key}"
                break
        if failure is not None:
            break
        method_seconds = float(remote_provenance.get("remote_method_seconds", 0.0))
        if not math.isfinite(method_seconds) or method_seconds < 0:
            failure = "remote runtime provenance is non-finite"
            break
        remote_runtime_seconds += method_seconds
        estimated_cost += shard_call_wall_seconds / 3600.0 * GPU_RATE_USD_PER_HOUR
        if estimated_cost > EXPECTED_HARD_CAP_USD:
            failure = "hard approval cap exceeded by the runner estimate"
            break
        remote_rows = response.get("results")
        if not isinstance(remote_rows, list) or len(remote_rows) != len(shard_records):
            failure = "remote response shard length mismatch"
            break
        by_id: dict[str, dict[str, Any]] = {}
        for remote_row in remote_rows:
            if not isinstance(remote_row, dict):
                failure = "remote response contains a non-object row"
                break
            identity = str(remote_row.get("normalized_variant_id", ""))
            if identity in by_id:
                failure = "remote response contains duplicate IDs"
                break
            by_id[identity] = remote_row
        if failure is not None:
            break
        expected_shard_ids = {str(row["normalized_variant_id"]) for row in shard_records}
        if set(by_id) != expected_shard_ids:
            failure = "remote response contains missing or unexpected IDs"
            break
        raw_rows = [
            _raw_row(
                row,
                by_id[str(row["normalized_variant_id"])],
                reference_provenance[str(row["normalized_variant_id"])],
                remote_provenance,
            )
            for row in shard_records
        ]
        shard_payload = {
            "execution_plan_sha256": plan_hash,
            "shard_index": shard_index,
            "source_ids": [str(row["normalized_variant_id"]) for row in shard_records],
            "rows": raw_rows,
            "status": "COMPLETED",
            "remote_invocations": remote_invocations,
            "transient_retries": transient_retries,
            "function_call_id": call_id,
            "remote_method_seconds": method_seconds,
        }
        _write_verified_shard(shard_path, shard_payload)
        all_raw.extend(raw_rows)
        new_shards += 1

    all_raw.sort(key=lambda row: str(row["normalized_variant_id"]))
    expected_ids_set = set(expected_ids)
    actual_ids = [str(row["normalized_variant_id"]) for row in all_raw]
    complete = (
        failure is None
        and len(all_raw) == EXPECTED_LOCKED_ROWS
        and actual_ids == expected_ids
        and len(set(actual_ids)) == EXPECTED_LOCKED_ROWS
        and reused_shards + new_shards == shard_count
    )
    if not complete:
        raise RuntimeError(
            failure
            or f"Phase 14 stopped incomplete: {len(all_raw)}/{EXPECTED_LOCKED_ROWS} raw rows"
        )
    if any("label" in row for row in all_raw):
        raise RuntimeError("raw Phase 14 artifact contains labels")
    _atomic_jsonl(raw_path, all_raw)
    raw_hash = _sha256_file(raw_path)

    joined, metrics = _label_join_and_evaluate(
        raw_rows=all_raw,
        manifest_path=manifest_path,
        config=config,
        repo_root=repo_root,
        raw_path=raw_path,
        model_artifact_path=model_artifact_path,
        calibration_path=calibration_path,
    )
    _atomic_jsonl(joined_path, joined)
    joined_hash = _sha256_file(joined_path)
    billing_after = _billing_snapshot(repo_root)
    total_wall_seconds = time.monotonic() - started
    final_artifact = {
        "artifact_id": "phase14-locked-evo2-20260922",
        "status": "PASS_PHASE14_LOCKED_EVALUATION",
        "phase": 14,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "git": {
            "commit": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        },
        "approval": {
            "path": str(approval_path.relative_to(repo_root)),
            "sha256": _sha256_file(approval_path),
            "hard_cap_usd": approval["budget_control"]["hard_cap_usd"],
            "safety_stop_usd": approval["budget_control"]["safety_stop_usd"],
        },
        "frozen_config": {
            "path": str(config_path.relative_to(repo_root)),
            "sha256": approval["frozen_config"]["sha256"],
            "file_sha256": _sha256_file(config_path),
            "model_artifact_sha256": _sha256_file(model_artifact_path),
            "calibration_artifact_sha256": _sha256_file(calibration_path),
        },
        "locked_cohort": {
            "manifest_path": str(manifest_path.relative_to(repo_root)),
            "manifest_sha256": _sha256_file(manifest_path),
            "expected_rows": EXPECTED_LOCKED_ROWS,
            "completed_rows": len(joined),
            "benign_or_likely_benign": sum(row["label"] == 0 for row in joined),
            "pathogenic_or_likely_pathogenic": sum(row["label"] == 1 for row in joined),
            "duplicate_ids": len(joined) - len({row["normalized_variant_id"] for row in joined}),
            "unexpected_ids": len(
                set(row["normalized_variant_id"] for row in joined) - expected_ids_set
            ),
        },
        "submission": {
            "submitted_rows": len(all_raw),
            "submitted_ids_sha256": _sha256_bytes(_stable_bytes(actual_ids)),
            "expected_ids_sha256": _sha256_bytes(_stable_bytes(expected_ids)),
            "exact_id_order": actual_ids == expected_ids,
        },
        "outputs": {
            "raw_predictions_path": str(raw_path.relative_to(repo_root)),
            "raw_predictions_sha256": raw_hash,
            "raw_predictions_contain_labels": False,
            "local_label_join_path": str(joined_path.relative_to(repo_root)),
            "local_label_join_sha256": joined_hash,
            "labels_joined_only_after_raw_hash": True,
        },
        "cache": {
            "shard_count": shard_count,
            "reused_shards": reused_shards,
            "new_shards": new_shards,
            "cache_hit_rows": cache_hit_rows,
            "newly_scored_rows": len(all_raw) - cache_hit_rows,
            "zero_recomputation_of_verified_shards": True,
            "transient_retries": transient_retries,
            "remote_invocations": remote_invocations,
        },
        "runtime": {
            "remote_runtime_seconds": remote_runtime_seconds,
            "client_wall_seconds": client_wall_seconds,
            "total_wall_seconds": total_wall_seconds,
            "function_call_ids": sorted(set(function_call_ids)),
        },
        "cost": {
            "estimated_run_cost_usd": estimated_cost,
            "gpu_rate_usd_per_hour": GPU_RATE_USD_PER_HOUR,
            "billing_before": billing_before,
            "billing_after": billing_after,
        },
        "model_contract": config["model_contract"],
        "metrics": metrics,
        "integrity_gates": {
            "exact_946_rows": len(joined) == EXPECTED_LOCKED_ROWS,
            "exact_submission_id_set": actual_ids == expected_ids,
            "zero_duplicates": len(joined) == len({row["normalized_variant_id"] for row in joined}),
            "zero_unexpected_ids": not (
                set(row["normalized_variant_id"] for row in joined) - expected_ids_set
            ),
            "zero_reference_mismatches": True,
            "finite_forward_scores": all(
                math.isfinite(float(row["delta_forward"])) for row in joined
            ),
            "finite_reverse_scores": all(
                math.isfinite(float(row["delta_reverse"])) for row in joined
            ),
            "finite_aggregate_scores": all(
                math.isfinite(float(row["delta_primary"])) for row in joined
            ),
            "finite_calibrated_scores": all(
                math.isfinite(float(row["calibrated_score"])) for row in joined
            ),
            "no_labels_remote_transport": all(
                not bool(row.get("remote_labels_transported")) for row in joined
            ),
            "no_locked_labels_before_raw_hash": True,
            "selection_closed": True,
            "post_test_tuning_prohibited": config.get("post_test_tuning_allowed") is False,
            "comparators_not_required": True,
        },
        "scientific_boundary": {
            "locked_inference_only_after_materialized_freeze": True,
            "remote_tracks": ["evo2"],
            "nt_caduceus_started": False,
            "fine_tuning_started": False,
            "final_statistics_one_shot": True,
        },
    }
    if not all(final_artifact["integrity_gates"].values()):
        raise RuntimeError("Phase 14 integrity gate failed")
    _atomic_json(final_path, final_artifact)
    print(json.dumps(final_artifact, indent=2, sort_keys=True))

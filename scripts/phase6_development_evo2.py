#!/usr/bin/env python3
"""Run the bounded, resumable Phase 6 Evo2 development workload.

The full TRAIN/VALIDATION cohort is intentionally not treated as affordable
under a five-dollar authorization.  This runner therefore processes a
deterministic prefix of the development cohort, in verified 32-variant
shards, and stops before its rate-based additional-cost estimate reaches the
approval cap.  It never reads labels into a Modal request and never selects a
LOCKED_TEST row.

The remote worker receives locally constructed frozen GRCh38 sequence views:

    reference_forward, alternate_forward,
    reference_reverse, alternate_reverse

The local side computes the canonical alternate-minus-reference deltas,
attaches development labels only after the remote response returns, and
writes an immutable-per-shard cache that can be resumed without recomputing a
verified completed shard.

Run only with both explicit paid-compute acknowledgement and the fresh
development approval artifact:

    EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS \
        .venv/bin/modal run scripts/phase6_development_evo2.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.cost_policy import (  # noqa: E402
    assert_paid_compute_allowed,
)
from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import generate_reference_window  # noqa: E402

SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from development_approval import validate_development_approval  # noqa: E402

APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase6_phase7_development_20260921.json"
DEVELOPMENT_MANIFEST_PATH = REPO_ROOT / "data/derived/ml_extension/phase3/split_manifest.json"
LOCKED_MANIFEST_PATH = (
    REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
)
REFERENCE_MANIFEST_PATH = REPO_ROOT / "data/manifests/grch38.json"
FASTA_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
FAI_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
RUN_ROOT = REPO_ROOT / "research/runs/phase6_development_evo2_20260921"
SHARDS_ROOT = RUN_ROOT / "shards"
PLAN_PATH = RUN_ROOT / "execution_plan.json"
PREDICTIONS_PATH = RUN_ROOT / "predictions.jsonl"
ARTIFACT_PATH = REPO_ROOT / "artifacts/phase6/phase6_development_evo2_20260921.json"
LEDGER_PATH = REPO_ROOT / "research/runs/cost_ledger.jsonl"

PROTOCOL_HASH = "39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3"
MODEL_ID = "evo2_7b"
MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
CONTEXT_LENGTH_BP = 8192
GPU_TYPE = "H100"
GPU_RATE_USD_PER_HOUR = 3.95
MODEL_SEQUENCE_BATCH_SIZE = 8
SHARD_SIZE = 32
MAX_APPROVAL_BUDGET_USD = 5.0
MAX_RATE_ESTIMATE_USD = MAX_APPROVAL_BUDGET_USD - 0.25
MAX_MODAL_BATCH_SECONDS = 900

BASE_IMAGE = modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
EVO2_IMAGE = (
    BASE_IMAGE.apt_install(
        [
            "build-essential",
            "cmake",
            "ninja-build",
            "git",
            "gcc",
            "g++",
            "clang",
            "libclang-dev",
        ]
    )
    .run_commands(
        "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
        "git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git evo2 "
        f"&& cd evo2 && git checkout {MODEL_REVISION} "
        "&& git submodule update --init --recursive && pip install .",
    )
    .run_commands(
        "pip uninstall -y transformer-engine transformer_engine",
        "pip install 'transformer_engine[pytorch]==1.13' --no-build-isolation",
        "pip install --force-reinstall --no-deps "
        "https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/"
        "flash_attn-2.6.3%2Bcu123torch2.4cxx11abiFALSE-cp312-cp312-linux_x86_64.whl",
    )
    .add_local_dir("scripts", "/opt/scripts", copy=True)
    .add_local_dir("src", "/opt/evovariant_tr", copy=True)
    .env({"PYTHONPATH": "/opt/evovariant_tr"})
    .run_commands("python3 /opt/scripts/patch_vortex.py")
)

app = modal.App("evovariant-tr", image=EVO2_IMAGE)
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


def _stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _billing_snapshot() -> dict[str, Any]:
    """Capture workspace billing without interpreting it as per-run spend."""
    try:
        result = subprocess.run(
            [str(Path(sys.executable).with_name("modal")), "billing", "summary"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary",
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}:{exc}",
        }


def _atomic_write(path: Path, value: object) -> None:
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


def _load_development_records() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    document = json.loads(DEVELOPMENT_MANIFEST_PATH.read_text(encoding="utf-8"))
    raw_records = document.get("records")
    if not isinstance(raw_records, list):
        raise RuntimeError("development manifest does not contain a records list")
    if _sha256_file(DEVELOPMENT_MANIFEST_PATH) != (
        "96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72"
    ):
        raise RuntimeError("development manifest hash changed after approval validation")
    locked_document = json.loads(LOCKED_MANIFEST_PATH.read_text(encoding="utf-8"))
    locked_ids = {
        str(row["normalized_variant_id"])
        for row in locked_document.get("records", [])
        if isinstance(row, dict) and "normalized_variant_id" in row
    }
    records = [cast(dict[str, Any], row) for row in raw_records if isinstance(row, dict)]
    if not records:
        raise RuntimeError("development manifest is empty")
    if any(str(row["normalized_variant_id"]) in locked_ids for row in records):
        raise RuntimeError("development manifest overlaps the locked-test record set")
    if any(str(row.get("split")) not in {"TRAIN", "VALIDATION"} for row in records):
        raise RuntimeError("development manifest contains a non-development split")
    records.sort(
        key=lambda row: hashlib.sha256(
            str(row["normalized_variant_id"]).encode("utf-8")
        ).hexdigest()
    )
    counts = {
        "total": len(records),
        "TRAIN": sum(row["split"] == "TRAIN" for row in records),
        "VALIDATION": sum(row["split"] == "VALIDATION" for row in records),
    }
    return records, {
        "development_manifest_path": str(DEVELOPMENT_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "development_manifest_sha256": _sha256_file(DEVELOPMENT_MANIFEST_PATH),
        "locked_manifest_path": str(LOCKED_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "locked_manifest_sha256": _sha256_file(LOCKED_MANIFEST_PATH),
        "locked_ids_excluded": True,
        "ordering": "ascending SHA-256 of normalized_variant_id",
        "counts": counts,
    }


def _prepare_batch(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create label-free remote rows from the frozen local GRCh38 reference."""
    payload: list[dict[str, Any]] = []
    for row in records:
        chromosome = str(row["chromosome"])
        window = None
        for candidate in (chromosome, f"chr{chromosome}"):
            try:
                window = generate_reference_window(
                    FASTA_PATH,
                    FAI_PATH,
                    candidate,
                    int(row["position_1based"]),
                )
                break
            except ValueError:
                continue
        if window is None:
            raise RuntimeError(
                f"could not load reference window for {row['normalized_variant_id']}"
            )
        if len(window.ref_sequence) != CONTEXT_LENGTH_BP:
            raise RuntimeError("reference window is not the frozen 8192-bp context")
        if window.ref_sequence[window.variant_offset] != str(row["reference"]):
            raise RuntimeError(f"reference allele mismatch for {row['normalized_variant_id']}")
        alternate = (
            window.ref_sequence[: window.variant_offset]
            + str(row["alternate"])
            + window.ref_sequence[window.variant_offset + 1 :]
        )
        sequences = [
            window.ref_sequence,
            alternate,
            reverse_complement(window.ref_sequence),
            reverse_complement(alternate),
        ]
        if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
            raise RuntimeError("sequence construction did not preserve the 8192-bp context")
        payload.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "sequences": sequences,
            }
        )
    return payload


@app.cls(
    gpu=GPU_TYPE,
    volumes={"/root/.cache/huggingface": hf_cache},  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=MAX_MODAL_BATCH_SECONDS,
)
class DevelopmentEvo2Worker:
    """Warm H100 worker using the already qualified Evo2 model contract."""

    @modal.enter()
    def load_model(self) -> None:
        import _codecs

        import torch
        from evo2 import Evo2

        try:
            torch.serialization.add_safe_globals([_codecs.encode])
        except Exception:
            pass
        started = time.perf_counter()
        self.model = Evo2(MODEL_ID)
        torch.cuda.synchronize()
        self.model_load_seconds = time.perf_counter() - started
        self.invocation_count = 0
        self.gpu_name = torch.cuda.get_device_name(0)
        self.gpu_total_memory_bytes = int(torch.cuda.get_device_properties(0).total_memory)

    @modal.method()
    def score_batch(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        import torch

        if not rows or len(rows) > SHARD_SIZE:
            raise ValueError(f"remote development batch must contain 1..{SHARD_SIZE} rows")
        sequences: list[str] = []
        ids: list[str] = []
        for row in rows:
            row_id = row.get("normalized_variant_id")
            row_sequences = row.get("sequences")
            if not isinstance(row_id, str) or not isinstance(row_sequences, list):
                raise ValueError("remote development rows require an ID and sequence list")
            if len(row_sequences) != 4 or any(
                not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP
                for sequence in row_sequences
            ):
                raise ValueError("each remote row must contain four 8192-bp sequence views")
            ids.append(row_id)
            sequences.extend(row_sequences)

        self.invocation_count += 1
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        scores: list[float] = []
        with torch.inference_mode():
            for start in range(0, len(sequences), MODEL_SEQUENCE_BATCH_SIZE):
                batch = sequences[start : start + MODEL_SEQUENCE_BATCH_SIZE]
                raw = self.model.score_sequences(batch)
                values = list(raw)
                if len(values) != len(batch):
                    raise RuntimeError("Evo2 returned an incomplete sequence batch")
                for value in values:
                    scalar = float(value.item() if hasattr(value, "item") else value)
                    if not math.isfinite(scalar):
                        raise RuntimeError("Evo2 returned a non-finite score")
                    scores.append(scalar)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        score_groups = [scores[index : index + 4] for index in range(0, len(scores), 4)]
        return {
            "status": "completed",
            "results": [
                {
                    "normalized_variant_id": row_id,
                    "raw_scores": group,
                }
                for row_id, group in zip(ids, score_groups, strict=True)
            ],
            "provenance": {
                "model_id": MODEL_ID,
                "checkpoint": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "gpu_type": GPU_TYPE,
                "gpu_name": self.gpu_name,
                "context_length_bp": CONTEXT_LENGTH_BP,
                "orientation": "forward_and_reverse",
                "score_semantics": "alternate_minus_reference_log_likelihood",
                "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
                "remote_method_seconds": round(elapsed, 6),
                "variants_per_second": round(len(rows) / elapsed, 6),
                "model_load_seconds": round(float(self.model_load_seconds), 6),
                "container_invocation_index": self.invocation_count,
                "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
                "gpu_total_memory_bytes": self.gpu_total_memory_bytes,
                "peak_container_rss_bytes": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                ),
                "all_scores_finite": True,
            },
        }


def _score_row(record: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    raw_scores = remote.get("raw_scores")
    if not isinstance(raw_scores, list) or len(raw_scores) != 4:
        raise RuntimeError("remote response did not contain four raw orientation scores")
    scores = [float(value) for value in raw_scores]
    if not all(math.isfinite(value) for value in scores):
        raise RuntimeError("remote response contained a non-finite score")
    forward_ref, forward_alt, reverse_ref, reverse_alt = scores
    delta_forward = forward_alt - forward_ref
    delta_reverse = reverse_alt - reverse_ref
    delta_primary = (delta_forward + delta_reverse) / 2.0
    return {
        "normalized_variant_id": record["normalized_variant_id"],
        "split": record["split"],
        "gene_symbol": record.get("gene_symbol"),
        "label": int(record["label"]),
        "raw_scores": {
            "reference_forward": forward_ref,
            "alternate_forward": forward_alt,
            "reference_reverse": reverse_ref,
            "alternate_reverse": reverse_alt,
        },
        "delta_forward": delta_forward,
        "delta_reverse": delta_reverse,
        "delta_primary": delta_primary,
        "orientation_disagreement": abs(delta_forward - delta_reverse),
        "coverage_status": "COMPLETED",
        "failure_reason": None,
        "provenance": {
            "model_id": MODEL_ID,
            "checkpoint": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "label_attached_after_remote_response": True,
        },
    }


def _read_verified_shard(path: Path, plan_hash: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"invalid shard artifact: {path}")
    payload = dict(document)
    recorded_hash = payload.pop("payload_sha256", None)
    if recorded_hash != _sha256_bytes(_stable_bytes(payload)):
        raise RuntimeError(f"tampered shard artifact: {path}")
    if payload.get("execution_plan_sha256") != plan_hash or payload.get("status") != "COMPLETED":
        raise RuntimeError(f"shard plan or status mismatch: {path}")
    return document


def _write_shard(path: Path, payload: dict[str, Any]) -> None:
    document = dict(payload)
    document["payload_sha256"] = _sha256_bytes(_stable_bytes(payload))
    _atomic_write(path, document)


def _build_plan(approval: Any, manifest_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": "phase6-development-evo2-20260921",
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "protocol_hash": PROTOCOL_HASH,
        "development_manifest_sha256": manifest_metadata["development_manifest_sha256"],
        "locked_manifest_sha256": manifest_metadata["locked_manifest_sha256"],
        "model_id": MODEL_ID,
        "checkpoint": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "gpu_type": GPU_TYPE,
        "context_length_bp": CONTEXT_LENGTH_BP,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
        "sequence_construction": "local frozen GRCh38 FASTA + deterministic SNV mutation",
        "cohort_splits": ["TRAIN", "VALIDATION"],
        "shard_size": SHARD_SIZE,
        "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
        "approval_max_budget_usd": approval["max_budget_usd"],
        "rate_estimate_stop_usd": MAX_RATE_ESTIMATE_USD,
        "labels_remote_transport": False,
    }


def _append_ledger(entry: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


@app.local_entrypoint()
def main() -> None:
    assert_paid_compute_allowed()
    approval = validate_development_approval(APPROVAL_PATH, REPO_ROOT)
    required_files = (
        DEVELOPMENT_MANIFEST_PATH,
        LOCKED_MANIFEST_PATH,
        REFERENCE_MANIFEST_PATH,
        FASTA_PATH,
        FAI_PATH,
    )
    for path in required_files:
        if not path.is_file():
            raise FileNotFoundError(f"missing approved Phase 6 input: {path}")

    records, manifest_metadata = _load_development_records()
    plan = _build_plan(approval, manifest_metadata)
    plan_hash = _sha256_bytes(_stable_bytes(plan))
    if PLAN_PATH.is_file():
        existing_plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        if existing_plan != {**plan, "execution_plan_sha256": plan_hash}:
            raise RuntimeError("existing Phase 6 execution plan differs from the approved plan")
    else:
        _atomic_write(PLAN_PATH, {**plan, "execution_plan_sha256": plan_hash})

    billing_before = _billing_snapshot()
    started = time.monotonic()
    worker = DevelopmentEvo2Worker()
    all_rows: list[dict[str, Any]] = []
    completed_shards = 0
    cache_hits = 0
    new_shards = 0
    estimated_usd = 0.0
    rate_samples: list[float] = []
    stop_reason = "full development cohort completed"
    failure: str | None = None

    for shard_index, start in enumerate(range(0, len(records), SHARD_SIZE)):
        shard_records = records[start : start + SHARD_SIZE]
        shard_path = SHARDS_ROOT / f"shard_{shard_index:06d}.json"
        stored = _read_verified_shard(shard_path, plan_hash)
        if stored is not None:
            stored_rows = stored.get("rows")
            if not isinstance(stored_rows, list) or len(stored_rows) != len(shard_records):
                raise RuntimeError(f"verified shard row count mismatch: {shard_path}")
            all_rows.extend(cast(list[dict[str, Any]], stored_rows))
            completed_shards += 1
            cache_hits += len(stored_rows)
            estimated_usd += float(stored.get("client_wall_rate_estimate_usd", 0.0))
            continue

        if estimated_usd >= MAX_RATE_ESTIMATE_USD:
            stop_reason = "rate-based additional-cost estimate reached the approval safety reserve"
            break
        if rate_samples:
            predicted_next = max(rate_samples[-3:])
            if estimated_usd + predicted_next > MAX_RATE_ESTIMATE_USD:
                stop_reason = "next shard would exceed the approval safety reserve"
                break

        payload = _prepare_batch(shard_records)
        call_started = time.monotonic()
        try:
            response = cast(dict[str, Any], worker.score_batch.remote(payload))
        except Exception as exc:  # noqa: BLE001 - preserve external failure evidence
            failure = f"{type(exc).__name__}: {exc}"
            stop_reason = "remote execution failed; no automatic retry was attempted"
            break
        client_seconds = time.monotonic() - call_started
        client_estimate = client_seconds / 3600.0 * GPU_RATE_USD_PER_HOUR
        estimated_usd += client_estimate
        rate_samples.append(client_estimate)
        if estimated_usd > MAX_APPROVAL_BUDGET_USD:
            failure = "post-call rate estimate exceeded the hard approval cap"
            stop_reason = "hard approval cap exceeded; output was not accepted"
            break
        if response.get("status") != "completed":
            failure = "remote worker returned a non-completed status"
            stop_reason = "remote worker status was not completed"
            break
        remote_rows = response.get("results")
        if not isinstance(remote_rows, list) or len(remote_rows) != len(shard_records):
            failure = "remote worker returned an incomplete shard"
            stop_reason = "remote worker returned an incomplete shard"
            break
        by_id = {
            str(row["normalized_variant_id"]): row
            for row in remote_rows
            if isinstance(row, dict) and "normalized_variant_id" in row
        }
        if set(by_id) != {str(row["normalized_variant_id"]) for row in shard_records}:
            failure = "remote worker returned unknown or missing variant IDs"
            stop_reason = "remote worker identity validation failed"
            break
        scored_rows = [
            _score_row(record, by_id[str(record["normalized_variant_id"])])
            for record in shard_records
        ]
        shard_payload = {
            "execution_plan_sha256": plan_hash,
            "shard_index": shard_index,
            "source_ids": [str(row["normalized_variant_id"]) for row in shard_records],
            "rows": scored_rows,
            "status": "COMPLETED",
            "client_wall_seconds": round(client_seconds, 6),
            "client_wall_rate_estimate_usd": round(client_estimate, 6),
            "remote_provenance": response.get("provenance", {}),
        }
        _write_shard(shard_path, shard_payload)
        all_rows.extend(scored_rows)
        completed_shards += 1
        new_shards += 1

    if completed_shards == 0 and failure is not None:
        status = "FAILED"
    elif completed_shards == len((len(records) + SHARD_SIZE - 1) // SHARD_SIZE):
        status = "PASS_FULL_DEVELOPMENT_COHORT"
    else:
        status = "PARTIAL_BUDGET_STOP" if failure is None else "PARTIAL_REMOTE_FAILURE"

    all_rows.sort(key=lambda row: str(row["normalized_variant_id"]))
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS_PATH.open("w", encoding="utf-8") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    split_counts = {
        split: sum(row.get("split") == split for row in all_rows)
        for split in ("TRAIN", "VALIDATION")
    }
    billing_after = _billing_snapshot()
    artifact = {
        "artifact_id": "phase6-development-evo2-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "protocol_hash": PROTOCOL_HASH,
        "git": {
            "commit": _git_value("rev-parse", "HEAD"),
            "dirty": bool(_git_value("status", "--porcelain=v1")),
        },
        "dataset": {
            **manifest_metadata,
            "full_development_records": len(records),
            "processed_records": len(all_rows),
            "remaining_records": len(records) - len(all_rows),
            "processed_split_counts": split_counts,
        },
        "model": {
            "model_id": MODEL_ID,
            "checkpoint": MODEL_ID,
            "revision": MODEL_REVISION,
            "gpu": GPU_TYPE,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
        },
        "cache": {
            "cache_root": str(SHARDS_ROOT.relative_to(REPO_ROOT)),
            "completed_shards": completed_shards,
            "new_shards": new_shards,
            "cache_hit_records": cache_hits,
            "resume_policy": "verified completed shards are skipped; tampering fails closed",
        },
        "cost": {
            "approval_max_budget_usd": approval["max_budget_usd"],
            "rate_estimate_stop_usd": MAX_RATE_ESTIMATE_USD,
            "cumulative_client_wall_rate_estimate_usd": round(estimated_usd, 6),
            "gpu_rate_usd_per_hour": GPU_RATE_USD_PER_HOUR,
            "pricing_source": "https://modal.com/pricing",
            "measured_invoice_usd": None,
            "interpretation": (
                "rate-based wall-time estimate; Modal CLI billing is workspace-level, "
                "not a per-run invoice"
            ),
        },
        "runtime": {
            "elapsed_local_seconds": round(time.monotonic() - started, 6),
            "failure": failure,
            "stop_reason": stop_reason,
        },
        "outputs": {
            "predictions_jsonl": str(PREDICTIONS_PATH.relative_to(REPO_ROOT)),
            "predictions_sha256": _sha256_file(PREDICTIONS_PATH),
            "execution_plan": str(PLAN_PATH.relative_to(REPO_ROOT)),
            "execution_plan_sha256": plan_hash,
        },
        "modal_billing": {
            "before": billing_before,
            "after": billing_after,
        },
        "scientific_boundary": {
            "labels_sent_to_modal": False,
            "locked_test_labels_accessed": False,
            "full_development_cohort_complete": status == "PASS_FULL_DEVELOPMENT_COHORT",
            "metrics_claimed": False,
            "phase14_started": False,
            "training_hpo_finetuning_started": False,
        },
    }
    _atomic_write(ARTIFACT_PATH, artifact)
    _append_ledger(
        {
            "run_id": "phase6-development-evo2-20260921",
            "timestamp": datetime.now(UTC).isoformat(),
            "workload": "evo2_modal_phase6_development_bounded",
            "backend": "modal",
            "gpu_type": GPU_TYPE,
            "gpu_count": 1,
            "estimated_seconds": round(
                sum(rate / GPU_RATE_USD_PER_HOUR * 3600 for rate in rate_samples),
                6,
            ),
            "measured_seconds": None,
            "estimated_usd": round(estimated_usd, 6),
            "measured_usd": None,
            "cache_hit": cache_hits > 0 and new_shards == 0,
            "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
            "status": (
                "COMPLETED"
                if status in {"PASS_FULL_DEVELOPMENT_COHORT", "PARTIAL_BUDGET_STOP"}
                else "FAILED"
            ),
            "notes": (
                "Development-only Evo2 raw scoring; deterministic TRAIN/VALIDATION prefix, "
                "no LOCKED_TEST access, no remote labels, no Phase 14 evaluation."
            ),
        }
    )
    print(json.dumps({"artifact": str(ARTIFACT_PATH), "status": status}, sort_keys=True))


if __name__ == "__main__":
    main()

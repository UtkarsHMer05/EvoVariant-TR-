"""Bounded one/eight-row label-blind Evo2 development diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.cost_policy import assert_paid_compute_allowed  # noqa: E402
from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import generate_reference_window  # noqa: E402

APP_NAME = "evovariant-tr-modal-evo2-development-diagnostic"
MODEL_NAME = "evo2_7b"
MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
FORMAL_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
FORMAL_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
CONTEXT_LENGTH_BP = 8192
GPU_TYPE = "H100"
GPU_RATE_USD_PER_HOUR = 3.95
HF_CACHE_PATH = "/root/.cache/huggingface"
FORMAL_MANIFEST_PATH = (
    REPO_ROOT
    / "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
LOCKED_MANIFEST_PATH = (
    REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
)
FASTA_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
FAI_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/modal_h100_jsonsafe_retry_20260921.json"

ROW_COUNT = int(os.environ.get("EVOVARIANT_TR_DIAGNOSTIC_ROWS", "1"))
if ROW_COUNT not in {1, 8}:
    raise RuntimeError("EVOVARIANT_TR_DIAGNOSTIC_ROWS must be 1 or 8")
RESUME_MODE = os.environ.get("EVOVARIANT_TR_DIAGNOSTIC_RESUME") == "1"
ARTIFACT_PATH = REPO_ROOT / (
    f"artifacts/modal_diagnostics/evo2_development_{ROW_COUNT}_20260921"
    f"{'_resume' if RESUME_MODE else ''}.json"
)
SHARD_PATH = REPO_ROOT / (
    f"artifacts/modal_diagnostics/evo2_development_shard_{ROW_COUNT}_20260921.json"
)

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

app = modal.App(APP_NAME)
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _plain(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_plain(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _plain(item) for key, item in value.items())
    return False


def _billing_snapshot() -> dict[str, Any]:
    binary = Path(sys.executable).with_name("modal")
    result = subprocess.run(
        [str(binary), "billing", "summary"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal billing summary",
        "returncode": int(result.returncode),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _validate_approval() -> dict[str, Any]:
    approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    current_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    if approval["git"]["commit"] != current_head:
        raise RuntimeError("diagnostic approval is not bound to the current HEAD")
    if approval["budget_control"]["hard_cap_usd"] != 0.5:
        raise RuntimeError("diagnostic approval hard cap is not $0.50")
    if approval["budget_control"]["runner_safety_stop_usd"] != 0.45:
        raise RuntimeError("diagnostic approval safety stop is not $0.45")
    if approval["formal_retry_authorized"] is not False:
        raise RuntimeError("formal 64-row retry is not allowed by this approval")
    return approval


def _select_label_blind_records() -> list[dict[str, Any]]:
    if _sha256_file(FORMAL_MANIFEST_PATH) != FORMAL_MANIFEST_SHA256:
        raise RuntimeError("formal development manifest hash changed")
    if _sha256_file(LOCKED_MANIFEST_PATH) != LOCKED_MANIFEST_SHA256:
        raise RuntimeError("locked-test manifest hash changed")
    document = json.loads(FORMAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    if document.get("record_set_sha256") != FORMAL_RECORD_SET_SHA256:
        raise RuntimeError("formal record-set hash changed")
    rows = [
        row
        for row in document.get("records", [])
        if isinstance(row, dict) and row.get("split") in {"TRAIN", "VALIDATION"}
    ]
    rows.sort(key=lambda row: str(row["normalized_variant_id"]))
    locked = json.loads(LOCKED_MANIFEST_PATH.read_text(encoding="utf-8"))
    locked_ids = {
        str(row["normalized_variant_id"])
        for row in locked.get("records", [])
        if isinstance(row, dict) and "normalized_variant_id" in row
    }
    selected: list[dict[str, Any]] = []
    for row in rows[:ROW_COUNT]:
        identity = str(row["normalized_variant_id"])
        if identity in locked_ids:
            raise RuntimeError("selected development row overlaps LOCKED_TEST")
        selected.append(
            {
                "normalized_variant_id": identity,
                "split": str(row["split"]),
                "chromosome": str(row["chromosome"]),
                "position_1based": int(row["position_1based"]),
                "reference": str(row["reference"]),
                "alternate": str(row["alternate"]),
            }
        )
    if len(selected) != ROW_COUNT:
        raise RuntimeError("formal development manifest did not provide enough records")
    return selected


def _prepare_payload(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload: list[dict[str, Any]] = []
    local_checks: list[dict[str, Any]] = []
    for row in records:
        chromosome = row["chromosome"]
        if chromosome in {"MT", "M"}:
            candidates = (chromosome, f"chr{chromosome}", "chrM")
        elif chromosome == "chrM":
            candidates = (chromosome,)
        else:
            candidates = (chromosome, f"chr{chromosome}")
        window = None
        for candidate in candidates:
            try:
                window = generate_reference_window(
                    FASTA_PATH,
                    FAI_PATH,
                    candidate,
                    row["position_1based"],
                )
                break
            except ValueError:
                continue
        if window is None:
            raise RuntimeError(
                f"could not load reference window for {row['normalized_variant_id']}"
            )
        if len(window.ref_sequence) != CONTEXT_LENGTH_BP:
            raise RuntimeError("reference window is not 8192 bp")
        reference_match = window.ref_sequence[window.variant_offset] == row["reference"]
        if not reference_match:
            raise RuntimeError(f"reference allele mismatch for {row['normalized_variant_id']}")
        alternate = (
            window.ref_sequence[: window.variant_offset]
            + row["alternate"]
            + window.ref_sequence[window.variant_offset + 1 :]
        )
        sequences = [
            window.ref_sequence,
            alternate,
            reverse_complement(window.ref_sequence),
            reverse_complement(alternate),
        ]
        if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
            raise RuntimeError("sequence construction changed the 8192-bp context")
        payload.append(
            {"normalized_variant_id": row["normalized_variant_id"], "sequences": sequences}
        )
        local_checks.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "split": row["split"],
                "reference_match": True,
                "context_length_bp": CONTEXT_LENGTH_BP,
                "orientation": "forward_and_reverse",
                "sequence_lengths": [len(sequence) for sequence in sequences],
            }
        )
    return payload, local_checks


def _score_rows(remote_rows: Any, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(remote_rows, list) or len(remote_rows) != len(records):
        raise RuntimeError("remote response row count does not match the requested batch")
    output: list[dict[str, Any]] = []
    expected_ids = [row["normalized_variant_id"] for row in records]
    actual_ids = [row.get("normalized_variant_id") for row in remote_rows if isinstance(row, dict)]
    if actual_ids != expected_ids:
        raise RuntimeError("remote response IDs or order do not match the deterministic request")
    for record, remote in zip(records, remote_rows, strict=True):
        raw_scores = remote.get("raw_scores")
        if not isinstance(raw_scores, list) or len(raw_scores) != 4:
            raise RuntimeError("remote response did not contain four orientation scores")
        scores = [float(value) for value in raw_scores]
        if not all(math.isfinite(value) for value in scores):
            raise RuntimeError("remote response contained a non-finite raw score")
        reference_forward, alternate_forward, reference_reverse, alternate_reverse = scores
        delta_forward = alternate_forward - reference_forward
        delta_reverse = alternate_reverse - reference_reverse
        aggregate = (delta_forward + delta_reverse) / 2.0
        if not math.isfinite(aggregate):
            raise RuntimeError("aggregate score is non-finite")
        output.append(
            {
                "normalized_variant_id": record["normalized_variant_id"],
                "split": record["split"],
                "raw_scores": {
                    "reference_forward": reference_forward,
                    "alternate_forward": alternate_forward,
                    "reference_reverse": reference_reverse,
                    "alternate_reverse": alternate_reverse,
                },
                "delta_forward": delta_forward,
                "delta_reverse": delta_reverse,
                "aggregate_score": aggregate,
                "finite": True,
            }
        )
    return output


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_shard(rows: list[dict[str, Any]], call_id: str, provenance: dict[str, Any]) -> None:
    payload = {
        "artifact_id": f"modal-evo2-development-shard-{ROW_COUNT}-20260921",
        "status": "COMPLETED",
        "row_count": ROW_COUNT,
        "source_ids": [row["normalized_variant_id"] for row in rows],
        "rows": rows,
        "remote_function_call_id": call_id,
        "remote_provenance": provenance,
    }
    payload_hash = hashlib.sha256(_stable_bytes(payload)).hexdigest()
    _write_json(SHARD_PATH, {**payload, "payload_sha256": payload_hash})


def _read_shard() -> dict[str, Any]:
    document = json.loads(SHARD_PATH.read_text(encoding="utf-8"))
    recorded = document.pop("payload_sha256", None)
    expected = hashlib.sha256(_stable_bytes(document)).hexdigest()
    if recorded != expected:
        raise RuntimeError("development shard payload hash mismatch")
    if document.get("status") != "COMPLETED" or document.get("row_count") != ROW_COUNT:
        raise RuntimeError("development shard is not a completed matching shard")
    if not isinstance(document.get("rows"), list) or len(document["rows"]) != ROW_COUNT:
        raise RuntimeError("development shard row count mismatch")
    return document


def _call_id(call: modal.FunctionCall[Any]) -> str:
    call.hydrate()
    object_id = call.object_id
    if not object_id:
        raise RuntimeError("Modal did not return a FunctionCall object ID")
    return object_id


@app.function(
    image=EVO2_IMAGE,
    gpu=GPU_TYPE,
    volumes={HF_CACHE_PATH: hf_cache},
    timeout=1200,
    startup_timeout=1200,
    retries=0,
)
def score_batch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Load the pinned model and score only the supplied label-free rows."""

    if not rows or len(rows) not in {1, 8}:
        raise ValueError("diagnostic batch must contain exactly one or eight rows")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import _codecs

    import torch
    from evo2 import Evo2

    from modal import current_function_call_id

    try:
        torch.serialization.add_safe_globals([_codecs.encode])
    except Exception:
        pass
    for row in rows:
        if set(row) != {"normalized_variant_id", "sequences"}:
            raise ValueError("remote payload contains an unexpected field or label")
        if not isinstance(row["normalized_variant_id"], str):
            raise ValueError("remote row ID must be a string")
        sequences = row["sequences"]
        if not isinstance(sequences, list) or len(sequences) != 4:
            raise ValueError("remote row must contain four sequence orientations")
        if any(
            not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP
            for sequence in sequences
        ):
            raise ValueError("remote sequence is not the frozen 8192-bp context")

    cache_root = Path(HF_CACHE_PATH) / "hub" / "models--arcinstitute--evo2_7b"
    cache_hit = bool(cache_root.is_dir() and any((cache_root / "snapshots").iterdir()))
    model_started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    model = Evo2(MODEL_NAME)
    torch.cuda.synchronize()
    model_load_seconds = time.perf_counter() - model_started
    sequences = [sequence for row in rows for sequence in row["sequences"]]
    started = time.perf_counter()
    scores: list[float] = []
    with torch.inference_mode():
        for start in range(0, len(sequences), 8):
            values = list(model.score_sequences(sequences[start : start + 8]))
            if len(values) != len(sequences[start : start + 8]):
                raise RuntimeError("Evo2 returned an incomplete sequence batch")
            scores.extend(
                float(value.item() if hasattr(value, "item") else value)
                for value in values
            )
    torch.cuda.synchronize()
    score_seconds = time.perf_counter() - started
    grouped = [scores[index : index + 4] for index in range(0, len(scores), 4)]
    return {
        "status": "completed",
        "results": [
            {"normalized_variant_id": row["normalized_variant_id"], "raw_scores": group}
            for row, group in zip(rows, grouped, strict=True)
        ],
        "provenance": {
            "function_call_id": str(current_function_call_id()),
            "container_id": os.environ.get("MODAL_CONTAINER_ID"),
            "model_id": MODEL_NAME,
            "model_revision": MODEL_REVISION,
            "gpu_type": GPU_TYPE,
            "gpu_name": str(torch.cuda.get_device_name(0)),
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "cache_hit": bool(cache_hit),
            "model_load_seconds": float(model_load_seconds),
            "score_seconds": float(score_seconds),
            "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "all_scores_finite": bool(all(math.isfinite(value) for value in scores)),
        },
    }


@app.local_entrypoint()
def main() -> None:
    assert_paid_compute_allowed()
    approval = _validate_approval()
    billing_before = _billing_snapshot()
    started = time.perf_counter()
    selected = _select_label_blind_records()
    payload, local_checks = _prepare_payload(selected)
    ids = [row["normalized_variant_id"] for row in selected]
    remote_invocations = 0
    run_kind = "RESUME_REUSE" if SHARD_PATH.is_file() else "REMOTE_BATCH"
    call_id = None
    remote_provenance: dict[str, Any] = {}
    if SHARD_PATH.is_file():
        shard = _read_shard()
        if shard["source_ids"] != ids:
            raise RuntimeError("existing development shard IDs differ from selected rows")
        scored_rows = shard["rows"]
        call_id = shard.get("remote_function_call_id")
        remote_provenance = shard.get("remote_provenance", {})
    else:
        call = score_batch.spawn(payload)
        call_id = _call_id(call)
        remote_response = call.get(timeout=1200)
        detached_response = modal.FunctionCall.from_id(call_id).get(timeout=1200)
        if not _plain(remote_response) or detached_response != remote_response:
            raise RuntimeError("remote response was not plain JSON-safe data")
        if remote_response.get("status") != "completed":
            raise RuntimeError("remote development batch did not complete")
        remote_provenance = remote_response.get("provenance", {})
        if remote_provenance.get("model_revision") != MODEL_REVISION:
            raise RuntimeError("remote model revision does not match the approved revision")
        if remote_provenance.get("cache_hit") is not True:
            raise RuntimeError("remote scoring did not observe a cache hit")
        scored_rows = _score_rows(remote_response.get("results"), selected)
        _write_shard(scored_rows, call_id, remote_provenance)
        remote_invocations = 1

    if len(scored_rows) != ROW_COUNT or [
        row["normalized_variant_id"] for row in scored_rows
    ] != ids:
        raise RuntimeError("persisted development shard failed deterministic ID/order validation")
    if not all(row.get("finite") is True for row in scored_rows):
        raise RuntimeError("persisted development shard contains a non-finite score")
    cache_artifact = REPO_ROOT / "artifacts/modal_diagnostics/hf_cache_read_20260921.json"
    cache_persistence = bool(cache_artifact.is_file())
    billing_after = _billing_snapshot()
    elapsed = time.perf_counter() - started
    artifact = {
        "artifact_id": f"modal-evo2-development-{ROW_COUNT}-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS",
        "run_kind": run_kind,
        "row_count": ROW_COUNT,
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "approval_head": approval["git"]["commit"],
        "protocol_sha256": PROTOCOL_HASH,
        "formal_manifest_sha256": FORMAL_MANIFEST_SHA256,
        "formal_record_set_sha256": FORMAL_RECORD_SET_SHA256,
        "selection": {
            "basis": "ascending normalized_variant_id among TRAIN and VALIDATION only",
            "label_blind": True,
            "selected_ids": ids,
            "splits": [row["split"] for row in selected],
            "locked_test_accessed": False,
        },
        "contract": {
            "assembly": "GRCh38",
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "model_name": MODEL_NAME,
            "model_revision": MODEL_REVISION,
            "gpu": GPU_TYPE,
        },
        "local_checks": local_checks,
        "remote_payload": {
            "labels_sent": False,
            "payload_keys": ["normalized_variant_id", "sequences"],
            "row_count": len(payload),
        },
        "rows": scored_rows,
        "remote": {
            "invocations": remote_invocations,
            "function_call_id": call_id,
            "provenance": remote_provenance,
            "durable_retrieval_verified": True if call_id else False,
        },
        "persistence": {
            "shard_path": str(SHARD_PATH.relative_to(REPO_ROOT)),
            "shard_exists": SHARD_PATH.is_file(),
            "shard_verified": True,
            "resume_behavior": (
                "PASS_NO_REMOTE_RECOMPUTATION"
                if run_kind == "RESUME_REUSE"
                else "READY_FOR_RESUME_CHECK"
            ),
            "cache_probe_artifact": str(cache_artifact.relative_to(REPO_ROOT)),
            "cache_persistence_artifact_present": cache_persistence,
            "duplicate_recomputation": False if run_kind == "RESUME_REUSE" else None,
        },
        "runtime": {
            "local_elapsed_seconds": float(elapsed),
            "estimated_wall_rate_cost_usd": float(elapsed / 3600.0 * GPU_RATE_USD_PER_HOUR)
            if remote_invocations
            else 0.0,
            "gpu_rate_usd_per_hour": GPU_RATE_USD_PER_HOUR,
        },
        "modal_billing": {"before": billing_before, "after": billing_after},
        "scientific_boundary": {
            "formal_64_row_preflight": False,
            "full_4000_row_run": False,
            "locked_test_accessed": False,
            "labels_sent_to_modal": False,
            "training_hpo_finetuning": False,
            "phase14": False,
        },
    }
    _write_json(ARTIFACT_PATH, artifact)
    print(
        json.dumps(
            {"artifact": str(ARTIFACT_PATH), "status": artifact["status"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

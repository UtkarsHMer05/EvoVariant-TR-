#!/usr/bin/env python3
"""Extract the predeclared formal NT/Caduceus representation matrix.

The local side constructs and verifies the exact 8,192-bp GRCh38 reference,
alternate, reverse-complement reference, and reverse-complement alternate
views. The Modal workers receive only those label-free views, return pooled
hidden states for all predeclared layers in one forward pass, and never see the
ClinVar labels. Verified shards are atomic and resumable; labels are joined
locally only while materializing the feature matrix.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import (  # noqa: E402
    generate_reference_window_with_par_alias,
)

NARROW_REPRESENTATION_MODE = (
    os.environ.get("EVOVARIANT_TR_FORMAL_REPRESENTATION_MODE") == "1"
)
OVERNIGHT_MODE = os.environ.get("EVOVARIANT_TR_OVERNIGHT_MODE") == "1"

FORMAL_MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
)
FORMAL_COST = REPO_ROOT / (
    "research/ml_extension/splits/formal_budgeted_20260921/cost_estimate.json"
)
FORMAL_EVO2_ARTIFACT = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_EVO2_ARTIFACT",
    "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json",
)
OUTPUT_ARTIFACT = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_REPRESENTATION_OUTPUT_PATH",
    (
        "artifacts/phase7/formal_budgeted_representation_20260922.json"
        if NARROW_REPRESENTATION_MODE
        else "artifacts/phase7/formal_budgeted_representation_20260921.json"
    ),
)
RUN_ROOT = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_REPRESENTATION_RUN_ROOT",
    (
        "research/runs/phase7_formal_budgeted_20260922"
        if NARROW_REPRESENTATION_MODE
        else "research/runs/phase7_formal_budgeted_20260921"
    ),
)
APPROVAL_PATH = REPO_ROOT / os.environ.get(
    "EVOVARIANT_TR_FORMAL_APPROVAL_PATH",
    (
        "artifacts/approvals/formal_phase7_representation_20260922.json"
        if NARROW_REPRESENTATION_MODE
        else (
            "artifacts/approvals/overnight_completion_20260922.json"
            if OVERNIGHT_MODE
            else "artifacts/approvals/ml_dev_budgeted_001_compute_20260921.json"
        )
    ),
)
REFERENCE_MANIFEST = REPO_ROOT / "data/manifests/grch38.json"
FASTA = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
FAI = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
LEDGER = REPO_ROOT / "research/runs/cost_ledger.jsonl"

PROTOCOL_HASH = "bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec"
FORMAL_MANIFEST_SHA256 = "f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782"
FORMAL_RECORD_SET_SHA256 = "b4559171706dcab13fdb075b38631ebda62f1f88667723fe3f27c5022283df44"
GPU_TYPE = "H100"
GPU_RATE_USD_PER_HOUR = 3.95
HARD_CAP_USD = 14.0 if OVERNIGHT_MODE else 8.0
SAFETY_STOP_USD = 13.5 if OVERNIGHT_MODE else 7.75
LOCKED_RESERVE_USD = 2.5 if OVERNIGHT_MODE else 0.0
if NARROW_REPRESENTATION_MODE:
    HARD_CAP_USD = 1.0
    SAFETY_STOP_USD = 0.85
    LOCKED_RESERVE_USD = 0.0
CONTEXT_LENGTH_BP = 8192
SHARD_SIZE = 8
VARIANT_BATCH_SIZE = 1
VIEWS_PER_VARIANT = 4
MAX_MODAL_BATCH_SECONDS = 900
FORMAL_PAR_ALIAS_IDS = frozenset(
    {
        "GRCh38:Y:1286043:T>C",
        "GRCh38:Y:1309674:G>T",
    }
)
NT_MODEL = "InstaDeepAI/nucleotide-transformer-v2-500m-multi-species"
NT_REVISION = "06615c1660c892fc199840c18123f8385b3542a8"
CADUCEUS_MODEL = "kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16"
CADUCEUS_REVISION = "b0477522ac5d044ad03578aa724ec8e4bdbd405b"
LAYERS: dict[str, tuple[int, ...]] = {
    "nucleotide_transformer": (8, 16, 24),
    "caduceus": (4, 8, 16),
}

BASE_IMAGE = modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
TORCH_IMAGE = BASE_IMAGE.run_commands(
    "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
)
TRANSFORMERS_IMAGE = TORCH_IMAGE.pip_install(
    "transformers==4.38.1",
    "safetensors==0.4.3",
    "numpy",
).add_local_dir("src", "/opt/evovariant_tr", copy=True).env(
    {"PYTHONPATH": "/opt/evovariant_tr"}
)
CADUCEUS_IMAGE = TRANSFORMERS_IMAGE.run_commands(
    "pip install --no-build-isolation 'mamba-ssm==2.2.4'",
)
app = modal.App("evovariant-tr")
HF_CACHE = modal.Volume.from_name("hf_cache", create_if_missing=False)
VOLUMES = {"/root/.cache/huggingface": HF_CACHE}


def stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def stable_hash(value: object) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def pack_array(array: np.ndarray) -> dict[str, Any]:
    contiguous = np.asarray(array, dtype=np.float32, order="C")
    encoded = zlib.compress(contiguous.tobytes(order="C"), level=3)
    return {
        "encoding": "zlib+base64",
        "dtype": "float32",
        "shape": list(contiguous.shape),
        "sha256": hashlib.sha256(contiguous.tobytes(order="C")).hexdigest(),
        "data": base64.b64encode(encoded).decode("ascii"),
    }


def unpack_array(payload: object) -> np.ndarray:
    if not isinstance(payload, dict):
        raise ValueError("packed representation is not an object")
    if payload.get("encoding") != "zlib+base64" or payload.get("dtype") != "float32":
        raise ValueError("packed representation encoding or dtype is invalid")
    raw = zlib.decompress(base64.b64decode(str(payload["data"])))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != payload.get("sha256"):
        raise ValueError("packed representation hash mismatch")
    array = np.frombuffer(raw, dtype=np.float32).copy()
    return array.reshape(tuple(int(value) for value in payload["shape"]))


def _sequence_payload(row: dict[str, Any]) -> dict[str, Any]:
    chromosome = str(row["chromosome"])
    if chromosome in {"MT", "M"}:
        candidates = (chromosome, f"chr{chromosome}", "chrM")
    else:
        candidates = (chromosome, f"chr{chromosome}")
    window = None
    used = None
    reference_provenance: dict[str, Any] | None = None
    last_error: ValueError | None = None
    for candidate in candidates:
        try:
            window, reference_provenance = generate_reference_window_with_par_alias(
                FASTA,
                FAI,
                candidate,
                int(row["position_1based"]),
                str(row["reference"]),
                allow_par_alias=str(row["normalized_variant_id"]) in FORMAL_PAR_ALIAS_IDS,
            )
            used = window.chrom
            break
        except ValueError as exc:
            last_error = exc
            continue
    if window is None or used is None:
        if last_error is not None:
            raise last_error
        raise RuntimeError(
            f"could not load formal reference window: {row['normalized_variant_id']}"
        )
    reference = window.ref_sequence
    if len(reference) != CONTEXT_LENGTH_BP:
        raise RuntimeError("formal representation reference window is not 8192 bp")
    if reference[window.variant_offset] != str(row["reference"]):
        raise RuntimeError(
            f"formal representation reference allele mismatch: {row['normalized_variant_id']}"
        )
    alternate = (
        reference[: window.variant_offset]
        + str(row["alternate"])
        + reference[window.variant_offset + 1 :]
    )
    sequences = [reference, alternate, reverse_complement(reference), reverse_complement(alternate)]
    if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
        raise RuntimeError("formal representation view length changed")
    if reference_provenance is None:
        raise RuntimeError("formal representation extraction did not return provenance")
    reference_provenance["reference_asset"] = (
        "data/reference/Homo_sapiens_assembly38.fasta"
    )
    return {
        "normalized_variant_id": row["normalized_variant_id"],
        "sequences": sequences,
        "sequence_sha256": hashlib.sha256(
            json.dumps(sequences, separators=(",", ":")).encode()
        ).hexdigest(),
        "reference_chromosome_used": used,
        "window_start_1based": window.start,
        "window_stop_1based": window.stop,
        "variant_offset_0based": window.variant_offset,
        "reference_provenance": reference_provenance,
    }


def load_records() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    document = json.loads(FORMAL_MANIFEST.read_text(encoding="utf-8"))
    rows = document.get("records")
    if not isinstance(rows, list) or len(rows) != 4_000:
        raise RuntimeError("formal representation manifest must contain 4,000 records")
    if sha256_file(FORMAL_MANIFEST) != FORMAL_MANIFEST_SHA256:
        raise RuntimeError("formal representation manifest hash changed")
    if document.get("record_set_sha256") != FORMAL_RECORD_SET_SHA256:
        raise RuntimeError("formal representation record-set hash changed")
    records = [cast(dict[str, Any], row) for row in rows]
    records.sort(key=lambda row: str(row["normalized_variant_id"]))
    return records, document


class _RepresentationWorker:
    candidate: str
    model_id: str
    revision: str
    layers: tuple[int, ...]
    max_length: int
    image_context: str

    def _load_model(self) -> None:
        import torch
        from transformers import AutoModelForMaskedLM, AutoTokenizer

        started = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            trust_remote_code=True,
            cache_dir="/root/.cache/huggingface",
        )
        self.model = AutoModelForMaskedLM.from_pretrained(
            self.model_id,
            revision=self.revision,
            trust_remote_code=True,
            cache_dir="/root/.cache/huggingface",
            torch_dtype=torch.float32,
        )
        self.model.to(torch.device("cuda"))
        self.model.eval()
        torch.cuda.synchronize()
        self.model_load_seconds = time.perf_counter() - started
        self.invocation_count = 0
        self.gpu_name = torch.cuda.get_device_name(0)
        self.gpu_total_memory_bytes = int(torch.cuda.get_device_properties(0).total_memory)
        self.parameter_count = int(sum(parameter.numel() for parameter in self.model.parameters()))

    @modal.method()
    def extract_batch(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        import torch

        if not rows or len(rows) > SHARD_SIZE:
            raise ValueError(f"formal representation batch must contain 1..{SHARD_SIZE} rows")
        sequences: list[str] = []
        ids: list[str] = []
        for row in rows:
            identity = row.get("normalized_variant_id")
            row_sequences = row.get("sequences")
            if not isinstance(identity, str) or not isinstance(row_sequences, list):
                raise ValueError("representation request row requires an ID and sequences")
            if len(row_sequences) != VIEWS_PER_VARIANT or any(
                not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP
                for sequence in row_sequences
            ):
                raise ValueError("representation request must contain four 8192-bp views")
            ids.append(identity)
            sequences.extend(row_sequences)

        self.invocation_count += 1
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        row_layers: list[dict[str, dict[str, Any]]] = [{} for _ in rows]
        token_shapes: list[list[int]] = []
        with torch.inference_mode():
            for start in range(0, len(rows), VARIANT_BATCH_SIZE):
                chunk_rows = rows[start : start + VARIANT_BATCH_SIZE]
                chunk_sequences = [sequence for row in chunk_rows for sequence in row["sequences"]]
                encoded = self.tokenizer(
                    chunk_sequences,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                )
                token_shapes.append(list(encoded["input_ids"].shape))
                encoded = {key: value.to("cuda") for key, value in encoded.items()}
                model_inputs: dict[str, Any] = {"input_ids": encoded["input_ids"]}
                if self.candidate != "caduceus":
                    model_inputs = encoded
                outputs = self.model(**model_inputs, output_hidden_states=True, return_dict=True)
                hidden_states = getattr(outputs, "hidden_states", None)
                if hidden_states is None:
                    raise RuntimeError("checkpoint did not expose hidden states")
                attention_mask = encoded.get("attention_mask")
                if attention_mask is None:
                    attention_mask = torch.ones(
                        hidden_states[0].shape[:2], device=hidden_states[0].device, dtype=torch.bool
                    )
                mask = attention_mask.to(dtype=hidden_states[0].dtype).unsqueeze(-1)
                pooled: dict[int, torch.Tensor] = {}
                for layer in self.layers:
                    if layer >= len(hidden_states):
                        raise RuntimeError(
                            f"requested layer {layer} is unavailable; "
                            f"checkpoint exposed {len(hidden_states)} states"
                        )
                    hidden = hidden_states[layer]
                    pooled[layer] = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
                for local_index in range(len(chunk_rows)):
                    for layer in self.layers:
                        view_start = local_index * VIEWS_PER_VARIANT
                        vectors = pooled[layer][view_start : view_start + VIEWS_PER_VARIANT]
                        row_layers[start + local_index][str(layer)] = pack_array(
                            vectors.detach().float().cpu().numpy()
                        )
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        return {
            "status": "completed",
            "results": [
                {
                    "normalized_variant_id": identity,
                    "layers": layers,
                    "token_shapes": token_shapes,
                    "pooling": "mean_tokens",
                    "dtype": "float32",
                }
                for identity, layers in zip(ids, row_layers, strict=True)
            ],
            "provenance": {
                "candidate": self.candidate,
                "model_id": self.model_id,
                "model_revision": self.revision,
                "gpu_type": GPU_TYPE,
                "gpu_name": self.gpu_name,
                "context_length_bp": CONTEXT_LENGTH_BP,
                "tokenizer_max_length": self.max_length,
                "truncation_enabled": True,
                "orientation": "forward_and_reverse",
                "view_order": [
                    "reference_forward",
                    "alternate_forward",
                    "reference_reverse",
                    "alternate_reverse",
                ],
                "layers": list(self.layers),
                "pooling": "mean_tokens",
                "dtype": "float32",
                "model_load_seconds": round(float(self.model_load_seconds), 6),
                "remote_method_seconds": round(elapsed, 6),
                "variants_per_second": round(len(rows) / elapsed, 6),
                "container_invocation_index": self.invocation_count,
                "parameter_count": self.parameter_count,
                "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
                "gpu_total_memory_bytes": self.gpu_total_memory_bytes,
                "peak_container_rss_bytes": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                ),
                "all_features_finite": True,
            },
        }


@app.cls(
    image=TRANSFORMERS_IMAGE,
    gpu=GPU_TYPE,
    volumes=VOLUMES,  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=900,
)
class NucleotideTransformerFormalWorker(_RepresentationWorker):
    candidate = "nucleotide_transformer"
    model_id = NT_MODEL
    revision = NT_REVISION
    layers = LAYERS["nucleotide_transformer"]
    max_length = 2048
    image_context = "transformers-4.38.1"

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()


@app.cls(
    image=CADUCEUS_IMAGE,
    gpu=GPU_TYPE,
    volumes=VOLUMES,  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=900,
)
class CaduceusFormalWorker(_RepresentationWorker):
    candidate = "caduceus"
    model_id = CADUCEUS_MODEL
    revision = CADUCEUS_REVISION
    layers = LAYERS["caduceus"]
    max_length = CONTEXT_LENGTH_BP
    image_context = "transformers-4.38.1+mamba-ssm-2.2.4"

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()


def _verify_shard(path: Path, plan_hash: str, expected_ids: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"representation shard is not an object: {path}")
    payload = dict(document)
    recorded = payload.pop("payload_sha256", None)
    if recorded != stable_hash(payload):
        raise RuntimeError(f"representation shard hash mismatch: {path}")
    if payload.get("execution_plan_sha256") != plan_hash or payload.get("status") != "COMPLETED":
        raise RuntimeError(f"representation shard plan/status mismatch: {path}")
    if payload.get("source_ids") != expected_ids:
        raise RuntimeError(f"representation shard IDs differ from the frozen plan: {path}")
    return document


def _write_shard(path: Path, payload: dict[str, Any]) -> None:
    document = dict(payload)
    document["payload_sha256"] = stable_hash(payload)
    atomic_json(path, document)


def _function_call_id(function_call: modal.FunctionCall[Any]) -> str:
    function_call.hydrate()
    object_id = function_call.object_id
    if not object_id:
        raise RuntimeError("Modal did not return a durable FunctionCall ID")
    return str(object_id)


def _features_from_results(
    records: list[dict[str, Any]],
    results_by_id: dict[str, dict[str, Any]],
    layers: tuple[int, ...],
) -> dict[str, np.ndarray]:
    reference: list[np.ndarray] = []
    alternate: list[np.ndarray] = []
    reference_reverse: list[np.ndarray] = []
    alternate_reverse: list[np.ndarray] = []
    for record in records:
        identity = str(record["normalized_variant_id"])
        result = results_by_id[identity]
        layer_payload = result.get("layers")
        if not isinstance(layer_payload, dict):
            raise RuntimeError(f"representation result has no layers: {identity}")
        for layer in layers:
            if str(layer) not in layer_payload:
                raise RuntimeError(f"representation result misses layer {layer}: {identity}")
        for layer in layers:
            packed = unpack_array(layer_payload[str(layer)])
            if packed.ndim != 2 or packed.shape[0] != VIEWS_PER_VARIANT:
                raise RuntimeError(f"representation layer shape is not [4, dimension]: {identity}")
            reference.append(packed[0])
            alternate.append(packed[1])
            reference_reverse.append(packed[2])
            alternate_reverse.append(packed[3])

    n = len(records)
    if n == 0:
        raise RuntimeError("cannot materialize an empty formal representation matrix")
    dimension = int(reference[0].shape[0])
    ref = np.asarray(reference, dtype=np.float32).reshape(n, len(layers), dimension)
    alt = np.asarray(alternate, dtype=np.float32).reshape(n, len(layers), dimension)
    ref_rc = np.asarray(reference_reverse, dtype=np.float32).reshape(n, len(layers), dimension)
    alt_rc = np.asarray(alternate_reverse, dtype=np.float32).reshape(n, len(layers), dimension)
    ref_aggregate = (ref + ref_rc) / 2.0
    alt_aggregate = (alt + alt_rc) / 2.0
    forward_delta = alt - ref
    reverse_delta = alt_rc - ref_rc
    aggregate_delta = (forward_delta + reverse_delta) / 2.0
    abs_delta = np.abs(aggregate_delta)
    dot = np.sum(ref_aggregate * alt_aggregate, axis=2)
    denominator = np.linalg.norm(ref_aggregate, axis=2) * np.linalg.norm(alt_aggregate, axis=2)
    cosine = np.divide(dot, denominator, out=np.zeros_like(dot), where=denominator != 0)
    distance = np.linalg.norm(aggregate_delta, axis=2)
    orientation_disagreement = np.linalg.norm(forward_delta - reverse_delta, axis=2)
    arrays = {
        "reference_forward": ref,
        "alternate_forward": alt,
        "reference_reverse": ref_rc,
        "alternate_reverse": alt_rc,
        "reference_aggregate": ref_aggregate,
        "alternate_aggregate": alt_aggregate,
        "forward_delta": forward_delta,
        "reverse_delta": reverse_delta,
        "alt_minus_ref_aggregate": aggregate_delta,
        "abs_alt_minus_ref_aggregate": abs_delta,
        "cosine_similarity": cosine,
        "distance_l2": distance,
        "orientation_disagreement_l2": orientation_disagreement,
        "labels": np.asarray([int(record["label"]) for record in records], dtype=np.int8),
        "variant_ids": np.asarray([str(record["normalized_variant_id"]) for record in records]),
        "splits": np.asarray([str(record["split"]) for record in records]),
        "gene_symbols": np.asarray([str(record.get("gene_symbol", "")) for record in records]),
        "layers": np.asarray(layers, dtype=np.int32),
    }
    if not all(
        np.isfinite(value).all() for key, value in arrays.items() if value.dtype.kind in "fc"
    ):
        raise RuntimeError("formal representation matrix contains non-finite values")
    return arrays


def _billing_snapshot() -> dict[str, Any]:
    binary = str(Path(sys.executable).with_name("modal"))
    try:
        result = subprocess.run(
            [binary, "billing", "summary"],
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
            "interpretation": "workspace-level provider summary, not a per-run invoice",
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}:{exc}"}


def _append_ledger(entry: dict[str, Any]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _run_candidate(
    candidate: str,
    worker_class: Any,
    records: list[dict[str, Any]],
    manifest_document: dict[str, Any],
    approval: dict[str, Any],
    base_spend_usd: float,
    planned_remaining_usd: float,
) -> dict[str, Any]:
    candidate_root = RUN_ROOT / candidate
    shard_root = candidate_root / "shards"
    plan_path = candidate_root / "execution_plan.json"
    feature_path = candidate_root / "features.npz"
    plan = {
        "study_id": "ML-DEV-BUDGETED-001",
        "candidate": candidate,
        "model_id": NT_MODEL if candidate == "nucleotide_transformer" else CADUCEUS_MODEL,
        "model_revision": NT_REVISION
        if candidate == "nucleotide_transformer"
        else CADUCEUS_REVISION,
        "layers": list(LAYERS[candidate]),
        "protocol_hash": PROTOCOL_HASH,
        "formal_manifest_sha256": FORMAL_MANIFEST_SHA256,
        "formal_record_set_sha256": FORMAL_RECORD_SET_SHA256,
        "record_count": len(records),
        "shard_size": SHARD_SIZE,
        "variant_batch_size": VARIANT_BATCH_SIZE,
        "context_length_bp": CONTEXT_LENGTH_BP,
        "views_per_variant": VIEWS_PER_VARIANT,
        "orientation": "forward_and_reverse",
        "labels_remote_transport": False,
        "pooling": "mean_tokens",
        "dtype": "float32",
        "preprocessing": (
            "8192-bp frozen GRCh38 views; Nucleotide Transformer tokenizer truncates/pads to "
            "2048 tokens; Caduceus tokenizer truncates/pads to 8192 tokens"
        ),
    }
    plan_hash = stable_hash(plan)
    expected_plan = {**plan, "execution_plan_sha256": plan_hash}
    if plan_path.is_file() and json.loads(plan_path.read_text(encoding="utf-8")) != expected_plan:
        raise RuntimeError(f"existing formal representation plan differs: {plan_path}")
    if not plan_path.is_file():
        atomic_json(plan_path, expected_plan)

    worker = worker_class()
    all_results: dict[str, dict[str, Any]] = {}
    completed_shards = 0
    new_shards = 0
    estimated_usd = 0.0
    rate_samples: list[float] = []
    started = time.monotonic()
    for shard_index, start in enumerate(range(0, len(records), SHARD_SIZE)):
        shard_records = records[start : start + SHARD_SIZE]
        source_ids = [str(row["normalized_variant_id"]) for row in shard_records]
        shard_path = shard_root / f"shard_{shard_index:05d}.json"
        pending_path = shard_root / f"shard_{shard_index:05d}.pending.json"
        stored = _verify_shard(shard_path, plan_hash, source_ids)
        if stored is not None:
            if pending_path.is_file():
                pending_path.unlink()
            for result in stored["results"]:
                all_results[str(result["normalized_variant_id"])] = result
            completed_shards += 1
            stored_rate = float(stored.get("client_wall_rate_estimate_usd", 0.0))
            estimated_usd += stored_rate
            if stored_rate > 0:
                rate_samples.append(stored_rate)
            continue

        payload = [_sequence_payload(row) for row in shard_records]
        pending: dict[str, Any] | None = None
        if pending_path.is_file():
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            if not isinstance(pending, dict):
                raise RuntimeError(f"pending representation call is not an object: {pending_path}")
            if (
                pending.get("execution_plan_sha256") != plan_hash
                or pending.get("source_ids") != source_ids
                or pending.get("payload_sha256") != stable_hash(payload)
                or not isinstance(pending.get("function_call_id"), str)
            ):
                raise RuntimeError(
                    "pending representation call does not match the frozen shard: "
                    f"{pending_path}"
                )
            function_call_id = str(pending["function_call_id"])
        else:
            if (
                base_spend_usd
                + estimated_usd
                + planned_remaining_usd
                + LOCKED_RESERVE_USD
                > SAFETY_STOP_USD
            ):
                raise RuntimeError(
                    "formal representation projected total exceeds the "
                    f"${SAFETY_STOP_USD:.2f} safety stop after preserving the "
                    f"${LOCKED_RESERVE_USD:.2f} locked-test reserve "
                    f"before {candidate} shard {shard_index}"
                )
            if (
                rate_samples
                and base_spend_usd
                + estimated_usd
                + max(rate_samples[-3:])
                + planned_remaining_usd
                + LOCKED_RESERVE_USD
                > SAFETY_STOP_USD
            ):
                raise RuntimeError(
                    "formal representation next-shard projection exceeds the safety stop"
                )
            call = worker.extract_batch.spawn(payload)
            function_call_id = _function_call_id(call)
            _write_shard(
                pending_path,
                {
                    "execution_plan_sha256": plan_hash,
                    "shard_index": shard_index,
                    "source_ids": source_ids,
                    "payload_sha256": stable_hash(payload),
                    "function_call_id": function_call_id,
                    "status": "SUBMITTED",
                    "submitted_at_utc": datetime.now(UTC).isoformat(),
                },
            )

        call_started = time.monotonic()
        response = cast(
            dict[str, Any],
            modal.FunctionCall.from_id(function_call_id).get(timeout=MAX_MODAL_BATCH_SECONDS),
        )
        client_seconds = time.monotonic() - call_started
        client_estimate = client_seconds / 3600.0 * GPU_RATE_USD_PER_HOUR
        estimated_usd += client_estimate
        rate_samples.append(client_estimate)
        if (
            base_spend_usd
            + estimated_usd
            + planned_remaining_usd
            + LOCKED_RESERVE_USD
            > HARD_CAP_USD
        ):
            raise RuntimeError("formal representation call exceeded the hard budget projection")
        if response.get("status") != "completed":
            raise RuntimeError("formal representation worker did not complete the shard")
        results = response.get("results")
        if not isinstance(results, list) or len(results) != len(shard_records):
            raise RuntimeError("formal representation worker returned an incomplete shard")
        by_id = {
            str(result["normalized_variant_id"]): result
            for result in results
            if isinstance(result, dict) and "normalized_variant_id" in result
        }
        if set(by_id) != set(source_ids):
            raise RuntimeError("formal representation worker returned unexpected IDs")
        for row, result in zip(payload, results, strict=True):
            if result.get("normalized_variant_id") != row["normalized_variant_id"]:
                raise RuntimeError("formal representation response order/identity mismatch")
            result["sequence_sha256"] = row["sequence_sha256"]
            result["sequence_construction"] = {
                key: row[key]
                for key in (
                    "reference_chromosome_used",
                    "window_start_1based",
                    "window_stop_1based",
                    "variant_offset_0based",
                )
            }
        shard_payload = {
            "execution_plan_sha256": plan_hash,
            "shard_index": shard_index,
            "source_ids": source_ids,
            "results": results,
            "status": "COMPLETED",
            "client_wall_seconds": round(client_seconds, 6),
            "client_wall_rate_estimate_usd": round(client_estimate, 6),
            "remote_provenance": response.get("provenance", {}),
            "function_call_id": function_call_id,
        }
        _write_shard(shard_path, shard_payload)
        pending_path.unlink(missing_ok=True)
        for result in results:
            all_results[str(result["normalized_variant_id"])] = result
        completed_shards += 1
        new_shards += 1

    if len(all_results) != len(records):
        raise RuntimeError(
            f"formal representation completed {len(all_results)} of {len(records)} records"
        )
    arrays = _features_from_results(records, all_results, LAYERS[candidate])
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(feature_path, **arrays)
    metadata = {
        "candidate": candidate,
        "model_id": plan["model_id"],
        "model_revision": plan["model_revision"],
        "checkpoint": plan["model_id"],
        "protocol_hash": PROTOCOL_HASH,
        "formal_manifest_path": str(FORMAL_MANIFEST.relative_to(REPO_ROOT)),
        "formal_manifest_sha256": FORMAL_MANIFEST_SHA256,
        "formal_record_set_sha256": FORMAL_RECORD_SET_SHA256,
        "record_count": len(records),
        "layers": list(LAYERS[candidate]),
        "pooling": "mean_tokens",
        "dtype": "float32",
        "context_length_bp": CONTEXT_LENGTH_BP,
        "orientation": "forward_and_reverse",
        "views": [
            "reference_forward",
            "alternate_forward",
            "reference_reverse",
            "alternate_reverse",
        ],
        "labels_remote_transport": False,
        "labels_attached_locally": True,
        "feature_keys": sorted(arrays),
        "feature_shapes": {key: list(value.shape) for key, value in arrays.items()},
        "feature_artifact": str(feature_path.relative_to(REPO_ROOT)),
        "feature_artifact_sha256": sha256_file(feature_path),
        "execution_plan": str(plan_path.relative_to(REPO_ROOT)),
        "execution_plan_sha256": sha256_file(plan_path),
        "completed_shards": completed_shards,
        "new_shards": new_shards,
        "cost": {
            "gpu_type": GPU_TYPE,
            "gpu_rate_usd_per_hour": GPU_RATE_USD_PER_HOUR,
            "estimated_client_wall_rate_usd": round(estimated_usd, 6),
            "measured_invoice_usd": None,
            "interpretation": "client wall-time rate estimate, not a per-run invoice",
        },
        "runtime_seconds": round(time.monotonic() - started, 6),
        "status": "PASS_FORMAL_REPRESENTATION_MATRIX",
    }
    atomic_json(candidate_root / "metadata.json", metadata)
    return metadata


@app.local_entrypoint()
def main() -> None:
    global HARD_CAP_USD, SAFETY_STOP_USD, LOCKED_RESERVE_USD

    if os.environ.get("EVOVARIANT_TR_PAID_COMPUTE_ACK") != "I_ACCEPT_COSTS":
        raise RuntimeError(
            "set EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS for formal representation work"
        )
    if NARROW_REPRESENTATION_MODE:
        from validate_formal_representation_approval import validate_approval
    elif OVERNIGHT_MODE:
        from validate_overnight_completion_approval import validate_approval
    else:
        from validate_ml_dev_budgeted_approval import validate_approval

    approval = validate_approval(APPROVAL_PATH)
    if NARROW_REPRESENTATION_MODE or OVERNIGHT_MODE:
        budget = approval["budget_control"]
        HARD_CAP_USD = float(budget["hard_cap_usd"])
        SAFETY_STOP_USD = float(budget["runner_safety_stop_usd"])
        LOCKED_RESERVE_USD = float(budget.get("locked_test_reserve_min_usd", 0.0))
    for path in (
        FORMAL_MANIFEST,
        FORMAL_COST,
        FORMAL_EVO2_ARTIFACT,
        REFERENCE_MANIFEST,
        FASTA,
        FAI,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"formal representation input is missing: {path}")
    records, manifest_document = load_records()
    evo2_artifact = json.loads(FORMAL_EVO2_ARTIFACT.read_text(encoding="utf-8"))
    if evo2_artifact.get("status") != "PASS_FULL_DEVELOPMENT_COHORT":
        raise RuntimeError("formal Evo2 scoring must PASS before representation extraction")
    evo2_prior_estimate_usd = float(
        evo2_artifact["cost"]["cumulative_client_wall_rate_estimate_usd"]
    )
    # The narrow approval caps only new representation spend. The completed
    # Evo2 estimate remains provenance, not spend against this approval.
    budget_baseline_usd = 0.0 if NARROW_REPRESENTATION_MODE else evo2_prior_estimate_usd
    cost_plan = json.loads(FORMAL_COST.read_text(encoding="utf-8"))
    candidate_plan = {
        "nucleotide_transformer": float(cost_plan["nucleotide_transformer"]["estimated_usd"]),
        "caduceus": float(cost_plan["caduceus"]["estimated_usd"]),
    }
    planned_total = budget_baseline_usd + sum(candidate_plan.values())
    if planned_total + LOCKED_RESERVE_USD > SAFETY_STOP_USD:
        raise RuntimeError(
            f"formal representation plan exceeds the ${SAFETY_STOP_USD:.2f} safety stop "
            f"after preserving the ${LOCKED_RESERVE_USD:.2f} locked-test reserve"
        )

    billing_before = _billing_snapshot()
    outputs: dict[str, Any] = {}
    remaining = sum(candidate_plan.values())
    base_spend_usd = budget_baseline_usd
    for candidate, worker_class in (
        ("nucleotide_transformer", NucleotideTransformerFormalWorker),
        ("caduceus", CaduceusFormalWorker),
    ):
        remaining -= candidate_plan[candidate]
        outputs[candidate] = _run_candidate(
            candidate,
            worker_class,
            records,
            manifest_document,
            approval,
            base_spend_usd,
            candidate_plan[candidate] + remaining,
        )
        base_spend_usd += float(outputs[candidate]["cost"]["estimated_client_wall_rate_usd"])

    billing_after = _billing_snapshot()
    budgeted_total = base_spend_usd
    representation_estimated = budgeted_total - budget_baseline_usd
    if budgeted_total + LOCKED_RESERVE_USD > HARD_CAP_USD:
        raise RuntimeError("formal representation total exceeded the hard cap")
    combined_estimated = evo2_prior_estimate_usd + representation_estimated
    artifact = {
        "artifact_id": (
            "formal-budgeted-representation-20260922"
            if NARROW_REPRESENTATION_MODE
            else (
                "formal-budgeted-representation-overnight-20260922"
                if OVERNIGHT_MODE
                else "formal-budgeted-representation-20260921"
            )
        ),
        "status": "PASS_FORMAL_REPRESENTATION_MATRIX",
        "study_id": "ML-DEV-BUDGETED-001",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "protocol_hash": PROTOCOL_HASH,
        "formal_manifest_sha256": FORMAL_MANIFEST_SHA256,
        "formal_record_set_sha256": FORMAL_RECORD_SET_SHA256,
        "formal_total": len(records),
        "model_tracks": outputs,
        "cost": {
            "evo2_prior_artifact": str(FORMAL_EVO2_ARTIFACT.relative_to(REPO_ROOT)),
            "evo2_estimated_usd": evo2_prior_estimate_usd,
            "representation_estimated_usd": round(representation_estimated, 6),
            "combined_estimated_usd": round(combined_estimated, 6),
            "hard_cap_usd": HARD_CAP_USD,
            "runner_safety_stop_usd": SAFETY_STOP_USD,
            "locked_test_reserve_min_usd": LOCKED_RESERVE_USD,
            "measured_invoice_usd": None,
        },
        "billing": {"before": billing_before, "after": billing_after},
        "scientific_boundary": {
            "labels_sent_to_modal": False,
            "labels_attached_locally": True,
            "locked_test_scored": False,
            "phase14_started": False,
            "fine_tuning_started": False,
        },
    }
    atomic_json(OUTPUT_ARTIFACT, artifact)
    _append_ledger(
        {
            "run_id": (
                "phase7-formal-budgeted-representations-20260922"
                if NARROW_REPRESENTATION_MODE
                else (
                    "phase7-formal-budgeted-representations-overnight-20260922"
                    if OVERNIGHT_MODE
                    else "phase7-formal-budgeted-representations-20260921"
                )
            ),
            "timestamp": datetime.now(UTC).isoformat(),
            "workload": "nt_caduceus_modal_formal_budgeted_representations",
            "backend": "modal",
            "gpu_type": GPU_TYPE,
            "gpu_count": 1,
            "estimated_usd": round(representation_estimated, 6),
            "measured_usd": None,
            "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
            "status": "COMPLETED",
            "notes": (
                "Formal 4,000-row label-free NT/Caduceus hidden-state extraction; "
                "labels joined locally only."
            ),
        }
    )
    print(
        json.dumps(
            {
                "status": artifact["status"],
                "artifact": str(OUTPUT_ARTIFACT.relative_to(REPO_ROOT)),
                "combined_estimated_usd": round(combined_estimated, 6),
                "representation_estimated_usd": round(representation_estimated, 6),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())

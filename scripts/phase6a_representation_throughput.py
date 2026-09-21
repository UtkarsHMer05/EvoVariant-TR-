#!/usr/bin/env python3
"""Run a very small, unlabeled representation-throughput study on Modal.

This is the post-Evo2 Phase6A smoke authorized by the current approval.  It
uses four deterministic variants from the frozen GRCh38 manifest, sends only
reference/alternate sequence views to Modal, and measures pooled hidden-state
throughput for the already verified Nucleotide Transformer and Caduceus
checkpoints.  It does not create a feature cache, read labels on Modal, or
claim a raw variant-score contract.

Run only after the bounded Evo2 Phase6A throughput artifact exists:

    .venv/bin/modal run scripts/phase6a_representation_throughput.py
"""

from __future__ import annotations

import hashlib
import json
import resource
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import generate_reference_window  # noqa: E402

APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase6a_throughput_20260921.json"
MANIFEST_PATH = REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
REFERENCE_MANIFEST_PATH = REPO_ROOT / "data/manifests/grch38.json"
FASTA_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
FAI_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
EVO2_ARTIFACT_PATH = REPO_ROOT / "artifacts/phase6a/phase6a_evo2_throughput_20260921.json"
OUTPUT_PATH = REPO_ROOT / "artifacts/phase6a/phase6a_representation_throughput_20260921.json"
LEDGER_PATH = REPO_ROOT / "research/runs/cost_ledger.jsonl"

EXPECTED_PROTOCOL_HASH = "39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3"
LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
LOCKED_RECORD_SET_SHA256 = "ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0"
NT_MODEL = "InstaDeepAI/nucleotide-transformer-v2-500m-multi-species"
NT_REVISION = "06615c1660c892fc199840c18123f8385b3542a8"
CADUCEUS_MODEL = "kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16"
CADUCEUS_REVISION = "b0477522ac5d044ad03578aa724ec8e4bdbd405b"
H100_RATE_USD_PER_HOUR = 3.95
GPU_TYPE = "H100"
GPU_PRICING_SOURCE = "https://modal.com/pricing"
AUTHORIZATION_CAP_USD = 1.50
REPRESENTATION_RATE_SAFETY_MARGIN_USD = 0.60
SAMPLE_SIZES = (2, 4)
VARIANT_BATCH_SIZES = (1, 2)
VIEWS_PER_VARIANT = 4
CONTEXT_LENGTH_BP = 8192

BASE_IMAGE = modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
TORCH_IMAGE = BASE_IMAGE.run_commands(
    "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
)
TRANSFORMERS_IMAGE = TORCH_IMAGE.pip_install(
    "transformers==4.38.1",
    "safetensors==0.4.3",
).add_local_dir("src", "/opt/evovariant_tr", copy=True).env(
    {"PYTHONPATH": "/opt/evovariant_tr"}
)
CADUCEUS_IMAGE = TRANSFORMERS_IMAGE.run_commands(
    "pip install --no-build-isolation 'mamba-ssm==2.2.4'",
)

app = modal.App("evovariant-tr")
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)
VOLUMES = {"/root/.cache/huggingface": hf_cache}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _billing_snapshot() -> dict[str, Any]:
    """Capture the provider workspace summary without treating it as an invoice."""
    modal_binary = shutil.which("modal") or str(Path(sys.executable).with_name("modal"))
    try:
        result = subprocess.run(
            [modal_binary, "billing", "summary"],
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


def _load_approval() -> dict[str, Any]:
    approval_value = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    if not isinstance(approval_value, dict):
        raise ValueError("Phase6A approval artifact must be a JSON object")
    approval = cast(dict[str, Any], approval_value)
    if approval.get("protocol_hash") != EXPECTED_PROTOCOL_HASH:
        raise RuntimeError("Phase6A approval protocol hash does not match the current protocol")
    if float(approval.get("max_budget_usd", 0)) != AUTHORIZATION_CAP_USD:
        raise RuntimeError("Phase6A approval cap must be exactly the user-authorized 1.50 USD")
    scope = str(approval.get("representation_scope", ""))
    if "very small unlabeled" not in scope or "do not perform full feature extraction" not in scope:
        raise RuntimeError("approval does not authorize the bounded representation smoke")
    return approval


def _load_sample() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = manifest.get("records")
    if not isinstance(rows, list) or len(rows) != 946:
        raise ValueError("authoritative locked manifest must contain exactly 946 records")
    if _sha256_file(MANIFEST_PATH) != LOCKED_MANIFEST_SHA256:
        raise ValueError("locked manifest SHA-256 changed before representation throughput")
    if _canonical_hash(rows) != LOCKED_RECORD_SET_SHA256:
        raise ValueError("locked record-set SHA-256 changed before representation throughput")

    ranked = sorted(
        (row for row in rows if isinstance(row, dict)),
        key=lambda row: hashlib.sha256(str(row["normalized_variant_id"]).encode()).hexdigest(),
    )
    selected = ranked[:4]
    payload: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    for row in selected:
        chromosome = str(row["chromosome"])
        window = None
        lookup_chromosome = chromosome
        for candidate in (chromosome, f"chr{chromosome}"):
            try:
                window = generate_reference_window(
                    FASTA_PATH,
                    FAI_PATH,
                    candidate,
                    int(row["position_1based"]),
                )
                lookup_chromosome = candidate
                break
            except ValueError:
                continue
        if window is None:
            raise ValueError(f"could not load reference window for {row['normalized_variant_id']}")
        if len(window.ref_sequence) != CONTEXT_LENGTH_BP:
            raise ValueError("representation sample is not the frozen 8192-bp context")
        if window.ref_sequence[window.variant_offset] != str(row["reference"]):
            raise ValueError(f"reference base mismatch for {row['normalized_variant_id']}")
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
            raise ValueError("representation sample contains a non-8192-bp sequence")
        payload.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "sequences": sequences,
            }
        )
        metadata_rows.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "reference_chromosome_used": lookup_chromosome,
                "window_start_1based": window.start,
                "window_stop_1based": window.stop,
                "variant_offset_0based": window.variant_offset,
                "sequence_sha256": hashlib.sha256(
                    json.dumps(sequences, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        )
    return payload, {
        "sampling_rule": (
            "SHA-256 rank of normalized_variant_id, ascending; labels are not read or "
            "sent to Modal"
        ),
        "sample_size_max": len(payload),
        "views_per_variant": VIEWS_PER_VARIANT,
        "view_order": [
            "reference_forward",
            "alternate_forward",
            "reference_reverse",
            "alternate_reverse",
        ],
        "selected_rows": metadata_rows,
        "reference_manifest_path": str(REFERENCE_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "reference_manifest_sha256": _sha256_file(REFERENCE_MANIFEST_PATH),
        "fasta_sha256": _sha256_file(FASTA_PATH),
        "fai_sha256": _sha256_file(FAI_PATH),
    }


class _RepresentationBase:
    """Shared implementation kept undecorated for Modal class wrappers."""

    candidate: str
    model_id: str
    revision: str
    source: str
    license_name: str
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
        self.gpu_memory_at_load_bytes = int(torch.cuda.memory_allocated())
        self.parameter_count = int(sum(parameter.numel() for parameter in self.model.parameters()))

    def _run_config(self, sample: list[dict[str, Any]], variant_batch_size: int) -> dict[str, Any]:
        import torch

        if variant_batch_size not in VARIANT_BATCH_SIZES:
            raise ValueError(f"unsupported variant batch size: {variant_batch_size}")
        if not sample or len(sample) > 4:
            raise ValueError("representation sample must contain between 1 and 4 variants")
        sequences: list[str] = []
        for row in sample:
            row_sequences = row.get("sequences")
            if not isinstance(row_sequences, list) or len(row_sequences) != VIEWS_PER_VARIANT:
                raise ValueError("each sample row must contain four sequence views")
            if any(
                not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP
                for sequence in row_sequences
            ):
                raise ValueError("all representation inputs must be exact 8192-bp strings")
            sequences.extend(row_sequences)

        self.invocation_count += 1
        cold_container = self.invocation_count == 1
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        pooled_chunks: list[torch.Tensor] = []
        token_shapes: list[list[int]] = []
        with torch.inference_mode():
            for start in range(0, len(sample), variant_batch_size):
                chunk_rows = sample[start : start + variant_batch_size]
                chunk_sequences = [
                    sequence
                    for row in chunk_rows
                    for sequence in row["sequences"]
                ]
                encoded = self.tokenizer(
                    chunk_sequences,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                )
                token_shapes.append(list(encoded["input_ids"].shape))
                encoded = {key: value.to("cuda") for key, value in encoded.items()}
                model_inputs: dict[str, Any]
                if self.candidate == "caduceus":
                    model_inputs = {"input_ids": encoded["input_ids"]}
                else:
                    model_inputs = encoded
                outputs = self.model(**model_inputs, output_hidden_states=True, return_dict=True)
                hidden_states = getattr(outputs, "hidden_states", None)
                hidden = (
                    hidden_states[-1]
                    if hidden_states
                    else getattr(outputs, "last_hidden_state", None)
                )
                if hidden is None:
                    raise RuntimeError("checkpoint output did not expose hidden states")
                attention_mask = encoded.get("attention_mask")
                if attention_mask is None:
                    attention_mask = torch.ones(
                        hidden.shape[:2], device=hidden.device, dtype=torch.bool
                    )
                mask = attention_mask.to(dtype=hidden.dtype).unsqueeze(-1)
                pooled_chunks.append((hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1))
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        pooled = torch.cat(pooled_chunks, dim=0)
        pooled_cpu = pooled.detach().float().cpu()
        pooled_hash = hashlib.sha256(pooled_cpu.numpy().tobytes()).hexdigest()
        memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        return {
            "status": "PASS",
            "candidate": self.candidate,
            "model_id": self.model_id,
            "model_revision": self.revision,
            "source": self.source,
            "license": self.license_name,
            "gpu_type": GPU_TYPE,
            "gpu_name": self.gpu_name,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "input_provenance": "locked_GRCh38_reference_alternate_sequence_views_unlabeled",
            "views_per_variant": VIEWS_PER_VARIANT,
            "view_order": [
                "reference_forward",
                "alternate_forward",
                "reference_reverse",
                "alternate_reverse",
            ],
            "sample_variants": len(sample),
            "sequence_count": len(sequences),
            "variant_batch_size": variant_batch_size,
            "sequence_batches": (len(sample) + variant_batch_size - 1) // variant_batch_size,
            "cold_container": cold_container,
            "container_invocation_index": self.invocation_count,
            "model_load_seconds": round(float(self.model_load_seconds), 6),
            "remote_method_seconds": round(elapsed, 6),
            "variants_per_second": round(len(sample) / elapsed, 6),
            "seconds_per_variant": round(elapsed / len(sample), 6),
            "parameter_count": self.parameter_count,
            "token_shapes": token_shapes,
            "pooled_embedding_shape": list(pooled.shape),
            "pooled_embedding_dtype": str(pooled.dtype),
            "hidden_finite": bool(torch.isfinite(pooled).all().item()),
            "pooled_embedding_sha256": pooled_hash,
            "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "gpu_memory_at_model_load_bytes": int(self.gpu_memory_at_load_bytes),
            "gpu_total_memory_bytes": int(self.gpu_total_memory_bytes),
            "gpu_memory_margin_bytes": int(
                self.gpu_total_memory_bytes - torch.cuda.max_memory_reserved()
            ),
            "peak_container_rss_bytes": int(memory),
            "estimated_gpu_rate_cost_usd": round(elapsed / 3600.0 * H100_RATE_USD_PER_HOUR, 6),
            "pricing_source": GPU_PRICING_SOURCE,
            "gpu_rate_usd_per_hour": H100_RATE_USD_PER_HOUR,
            "raw_variant_score": False,
            "feature_cache_written": False,
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
class NucleotideTransformerThroughput(_RepresentationBase):
    """Bounded Nucleotide Transformer embedding worker."""

    candidate = "nucleotide_transformer"
    model_id = NT_MODEL
    revision = NT_REVISION
    source = "https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species"
    license_name = "CC-BY-NC-SA-4.0"
    max_length = 2048
    image_context = "transformers-4.38.1"

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()

    @modal.method()
    def run_config(self, sample: list[dict[str, Any]], variant_batch_size: int) -> dict[str, Any]:
        return self._run_config(sample, variant_batch_size)


@app.cls(
    image=CADUCEUS_IMAGE,
    gpu=GPU_TYPE,
    volumes=VOLUMES,  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=900,
)
class CaduceusThroughput(_RepresentationBase):
    """Bounded Caduceus embedding worker."""

    candidate = "caduceus"
    model_id = CADUCEUS_MODEL
    revision = CADUCEUS_REVISION
    source = "https://huggingface.co/kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16"
    license_name = "Apache-2.0"
    max_length = CONTEXT_LENGTH_BP
    image_context = "transformers-4.38.1+mamba-ssm-2.2.4"

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()

    @modal.method()
    def run_config(self, sample: list[dict[str, Any]], variant_batch_size: int) -> dict[str, Any]:
        return self._run_config(sample, variant_batch_size)


def _append_ledger(entry: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


@app.local_entrypoint()
def main() -> None:
    """Run the tiny representation matrix and persist evidence."""
    approval = _load_approval()
    if not EVO2_ARTIFACT_PATH.is_file():
        raise FileNotFoundError("run the bounded Evo2 Phase6A artifact before this smoke")
    evo2_artifact = json.loads(EVO2_ARTIFACT_PATH.read_text(encoding="utf-8"))
    evo2_estimate = float(
        evo2_artifact["authorization"]["cumulative_client_wall_rate_estimate_usd"]
    )
    if str(evo2_artifact.get("status", "")).startswith("PASS") is False:
        raise RuntimeError("Evo2 Phase6A artifact is not a completed bounded study")
    for required in (MANIFEST_PATH, REFERENCE_MANIFEST_PATH, FASTA_PATH, FAI_PATH):
        if not required.is_file():
            raise FileNotFoundError(f"missing Phase6A representation input: {required}")

    sample, sample_metadata = _load_sample()
    billing_before = _billing_snapshot()
    started_study = time.monotonic()
    results: list[dict[str, Any]] = []
    cumulative_estimate = 0.0
    stop_reason = "all approved tiny representation configurations completed"
    services: tuple[tuple[str, Any], ...] = (
        ("nucleotide_transformer", NucleotideTransformerThroughput()),
        ("caduceus", CaduceusThroughput()),
    )
    for candidate, service in services:
        for sample_size in SAMPLE_SIZES:
            for batch_size in VARIANT_BATCH_SIZES:
                if evo2_estimate + cumulative_estimate >= REPRESENTATION_RATE_SAFETY_MARGIN_USD:
                    stop_reason = (
                        "stopped before the combined Phase6A rate estimate exceeded its "
                        "safety margin"
                    )
                    break
                call_started = time.monotonic()
                try:
                    result = dict(service.run_config.remote(sample[:sample_size], batch_size))
                    result["client_wall_seconds"] = round(time.monotonic() - call_started, 6)
                    result["client_wall_rate_estimate_usd"] = round(
                        result["client_wall_seconds"] / 3600.0 * H100_RATE_USD_PER_HOUR,
                        6,
                    )
                    cumulative_estimate += float(result["client_wall_rate_estimate_usd"])
                except Exception as exc:  # noqa: BLE001 - preserve candidate-specific evidence
                    client_seconds = time.monotonic() - call_started
                    estimate = client_seconds / 3600.0 * H100_RATE_USD_PER_HOUR
                    cumulative_estimate += estimate
                    result = {
                        "status": "FAILED_CONFIG",
                        "candidate": candidate,
                        "gpu_type": GPU_TYPE,
                        "sample_variants": sample_size,
                        "variant_batch_size": batch_size,
                        "client_wall_seconds": round(client_seconds, 6),
                        "client_wall_rate_estimate_usd": round(estimate, 6),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                results.append(result)
                print(json.dumps(result, sort_keys=True))
            if evo2_estimate + cumulative_estimate >= REPRESENTATION_RATE_SAFETY_MARGIN_USD:
                break
        if evo2_estimate + cumulative_estimate >= REPRESENTATION_RATE_SAFETY_MARGIN_USD:
            break

    billing_after = _billing_snapshot()
    completed = [row for row in results if row.get("status") == "PASS"]
    artifact = {
        "artifact_id": "phase6a-representation-throughput-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": (
            "PASS_BOUNDED_REPRESENTATION_THROUGHPUT"
            if completed
            else "FAILED_ALL_REPRESENTATION_CONFIGS"
        ),
        "protocol_hash": EXPECTED_PROTOCOL_HASH,
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "approval_scope": approval["representation_scope"],
        "locked_cohort": {
            "manifest": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "manifest_sha256": LOCKED_MANIFEST_SHA256,
            "record_set_sha256": LOCKED_RECORD_SET_SHA256,
            "total_records": 946,
            "inference_target_records": 0,
            "sample_is_unlabeled": True,
            "sample_metadata": sample_metadata,
        },
        "models": {
            "nucleotide_transformer": {"model": NT_MODEL, "revision": NT_REVISION},
            "caduceus": {"model": CADUCEUS_MODEL, "revision": CADUCEUS_REVISION},
        },
        "authorization": {
            "max_budget_usd": AUTHORIZATION_CAP_USD,
            "prior_evo2_client_wall_rate_estimate_usd": round(evo2_estimate, 6),
            "representation_rate_safety_margin_usd": REPRESENTATION_RATE_SAFETY_MARGIN_USD,
            "representation_cumulative_client_wall_rate_estimate_usd": round(
                cumulative_estimate, 6
            ),
            "combined_client_wall_rate_estimate_usd": round(evo2_estimate + cumulative_estimate, 6),
            "stop_reason": stop_reason,
        },
        "results": results,
        "summary": {
            "completed_configurations": len(completed),
            "failed_configurations": len(results) - len(completed),
            "full_feature_extraction_started": False,
            "feature_cache_written": False,
            "raw_variant_scores_generated": False,
            "interpretation": (
                "This is a tiny throughput and finite-pooled-hidden-state check on actual "
                "GRCh38 sequence views. It does not establish a raw REF-vs-ALT likelihood "
                "contract, a training feature set, or a full-cohort extraction plan."
            ),
        },
        "modal_billing": {
            "before": billing_before,
            "after": billing_after,
            "billed_cost_interpretation": (
                "The CLI summary is workspace-level and may include deployed apps, volumes, "
                "image/container activity, and prior work; no per-request billed USD is "
                "asserted unless the provider exposes it."
            ),
        },
        "prior_phase6a_attempts": [
            {
                "run_url": "https://modal.com/apps/utkarshmer05/main/ap-Cqgu50y0KRq95f3vyyYwxB",
                "status": "ABORTED_BEFORE_MODEL_LOAD",
                "failure": (
                    "representation worker image omitted the local evovariant_tr sequence "
                    "helper package"
                ),
                "inference_started": False,
            }
        ],
        "phase_boundary": {
            "phase6_started": False,
            "phase7_started": False,
            "full_locked_test_evaluation": False,
            "training_hpo_finetuning": False,
            "full_feature_extraction": False,
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _append_ledger(
        {
            "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
            "backend": "modal",
            "cache_hit": False,
            "estimated_seconds": round(time.monotonic() - started_study, 6),
            "estimated_usd": round(cumulative_estimate, 6),
            "gpu_count": 1,
            "gpu_type": GPU_TYPE,
            "measured_seconds": None,
            "measured_usd": None,
            "notes": (
                "Phase6A tiny unlabeled representation throughput only; no full feature "
                "extraction, raw scoring, labels, training, HPO, fine-tuning, or locked evaluation."
            ),
            "run_id": "phase6a-representation-throughput-20260921",
            "status": "COMPLETED" if completed else "FAILED",
            "timestamp": datetime.now(UTC).isoformat(),
            "workload": "nt_caduceus_modal_phase6a_representation_throughput",
        }
    )
    print(json.dumps({"artifact": str(OUTPUT_PATH), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()

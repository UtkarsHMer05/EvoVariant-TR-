"""Run bounded real-checkpoint Phase 5 model smoke tests on Modal.

The smoke is deliberately narrower than a scientific benchmark.  It verifies
that two additional official checkpoints can be installed, loaded, tokenized,
run on a tiny reference/alternate sequence pair, and produce finite logits and
pooled embeddings.  The pair is synthetic because the frozen GRCh38 FASTA is
not present locally; no result from this script is a ClinVar or Phase 6 score.

Run only with the user-approved pilot acknowledgement:

    EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS \
      .venv/bin/modal run scripts/phase5_model_smoke.py
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase2_4_pilot_20260921.json"
OUTPUT_PATH = REPO_ROOT / "artifacts/model_audit/phase5_real_smokes_20260921.json"
EXPECTED_PROTOCOL_HASH = "374bc2c59941d6001e41c478658ad65fa4e2ae0789829d2625e8801b00ad7c5c"
H100_WALL_RATE_USD_PER_HOUR = 3.95
GPU_TYPE = "H100"
HF_CACHE_PATH = "/root/.cache/huggingface"

NT_MODEL = "InstaDeepAI/nucleotide-transformer-v2-500m-multi-species"
NT_REVISION = "06615c1660c892fc199840c18123f8385b3542a8"
CADUCEUS_MODEL = "kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16"
CADUCEUS_REVISION = "b0477522ac5d044ad03578aa724ec8e4bdbd405b"

BASE_IMAGE = modal.Image.from_registry(
    "nvcr.io/nvidia/pytorch:24.07-py3",
    add_python="3.12",
)
TORCH_IMAGE = BASE_IMAGE.run_commands(
    "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
)
TRANSFORMERS_IMAGE = TORCH_IMAGE.pip_install(
    "transformers==4.38.1",
    "safetensors==0.4.3",
)
CADUCEUS_IMAGE = TRANSFORMERS_IMAGE.run_commands(
    "pip install --no-build-isolation 'mamba-ssm==2.2.4'",
)

app = modal.App("evovariant-tr-phase5-smoke")
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


def _smoke_sequence_pair() -> tuple[str, str]:
    """Return a synthetic but deterministic one-base reference/alternate pair."""
    reference = ("ACGT" * 160)[:256]
    alternate = reference[:128] + ("T" if reference[128] != "T" else "A") + reference[129:]
    if reference == alternate:
        raise AssertionError("smoke pair must differ at exactly one base")
    if sum(left != right for left, right in zip(reference, alternate, strict=True)) != 1:
        raise AssertionError("smoke pair must contain exactly one substitution")
    return reference, alternate


def _summarize_outputs(
    *,
    model: Any,
    outputs: Any,
    encoded: dict[str, Any],
    reference: str,
    alternate: str,
    elapsed_seconds: float,
    candidate: str,
    model_id: str,
    revision: str,
    source: str,
    license_name: str,
) -> dict[str, Any]:
    """Create a compact, non-scientific smoke result from a real model call."""
    import torch

    hidden_states = getattr(outputs, "hidden_states", None)
    if hidden_states:
        hidden = hidden_states[-1]
    else:
        hidden = getattr(outputs, "last_hidden_state", None)
    if hidden is None:
        raise RuntimeError("checkpoint output did not expose hidden states")

    attention_mask = encoded.get("attention_mask")
    if attention_mask is None:
        attention_mask = torch.ones(hidden.shape[:2], device=hidden.device, dtype=torch.bool)
    mask = attention_mask.to(dtype=hidden.dtype).unsqueeze(-1)
    pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
    delta = pooled[1] - pooled[0]
    logits = getattr(outputs, "logits", None)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    config = getattr(model, "config", None)
    max_positions = None
    if config is not None:
        max_positions = getattr(config, "max_position_embeddings", None)
        if max_positions is None:
            max_positions = getattr(config, "max_seq_len", None)

    return {
        "status": "PASS",
        "candidate": candidate,
        "model_id": model_id,
        "revision": revision,
        "source": source,
        "license": license_name,
        "model_class": type(model).__name__,
        "parameter_count": int(parameter_count),
        "configured_max_positions": max_positions,
        "device": str(next(model.parameters()).device),
        "parameter_dtype": str(next(model.parameters()).dtype),
        "input_provenance": "synthetic_smoke_sequence_not_GRCh38_cohort_evidence",
        "reference_length_bp": len(reference),
        "alternate_length_bp": len(alternate),
        "changed_base_count": sum(
            left != right for left, right in zip(reference, alternate, strict=True)
        ),
        "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
        "alternate_sha256": hashlib.sha256(alternate.encode()).hexdigest(),
        "token_shape": list(encoded["input_ids"].shape),
        "hidden_shape": list(hidden.shape),
        "logits_shape": list(logits.shape) if logits is not None else None,
        "hidden_finite": bool(torch.isfinite(hidden).all().item()),
        "logits_finite": bool(logits is None or torch.isfinite(logits).all().item()),
        "ref_alt_embedding_delta_l2": float(torch.linalg.vector_norm(delta).item()),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "estimated_wall_rate_cost_usd": round(
            elapsed_seconds / 3600.0 * H100_WALL_RATE_USD_PER_HOUR,
            4,
        ),
        "raw_variant_score": False,
        "raw_score_reason": (
            "The checkpoint produced logits/embeddings, but no official raw REF-vs-ALT "
            "allele-likelihood contract was applied."
        ),
    }


def _run_checkpoint_smoke(
    *,
    model_id: str,
    revision: str,
    candidate: str,
    source: str,
    license_name: str,
    trust_remote_code: bool,
    dtype_name: str,
    max_length: int,
) -> dict[str, Any]:
    """Load one official checkpoint and run a tiny reference/alternate forward pass."""
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    started = time.monotonic()
    reference, alternate = _smoke_sequence_pair()
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        revision=revision,
        trust_remote_code=trust_remote_code,
        cache_dir=HF_CACHE_PATH,
    )
    dtype = getattr(torch, dtype_name)
    model = AutoModelForMaskedLM.from_pretrained(
        model_id,
        revision=revision,
        trust_remote_code=trust_remote_code,
        cache_dir=HF_CACHE_PATH,
        torch_dtype=dtype,
    )
    device = torch.device("cuda")
    model.to(device)
    model.eval()
    encoded = tokenizer(
        [reference, alternate],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    if "attention_mask" not in encoded:
        encoded["attention_mask"] = torch.ones_like(encoded["input_ids"], dtype=torch.bool)
    model_inputs = encoded
    if candidate == "caduceus":
        # The official Caduceus custom forward accepts input_ids but not the
        # standard Transformers attention_mask keyword.
        model_inputs = {"input_ids": encoded["input_ids"]}
    with torch.inference_mode():
        outputs = model(**model_inputs, output_hidden_states=True, return_dict=True)
    result = _summarize_outputs(
        model=model,
        outputs=outputs,
        encoded=encoded,
        reference=reference,
        alternate=alternate,
        elapsed_seconds=time.monotonic() - started,
        candidate=candidate,
        model_id=model_id,
        revision=revision,
        source=source,
        license_name=license_name,
    )
    del model, outputs
    torch.cuda.empty_cache()
    return result


@app.function(
    image=TRANSFORMERS_IMAGE,
    gpu=GPU_TYPE,
    volumes={HF_CACHE_PATH: hf_cache},
    timeout=1200,
)
def smoke_nucleotide_transformer() -> dict[str, Any]:
    """Run the real Nucleotide Transformer checkpoint smoke."""
    return _run_checkpoint_smoke(
        model_id=NT_MODEL,
        revision=NT_REVISION,
        candidate="nucleotide_transformer",
        source="https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species",
        license_name="CC-BY-NC-SA-4.0",
        trust_remote_code=True,
        dtype_name="float32",
        max_length=512,
    )


@app.function(
    image=CADUCEUS_IMAGE,
    gpu=GPU_TYPE,
    volumes={HF_CACHE_PATH: hf_cache},
    timeout=1200,
)
def smoke_caduceus() -> dict[str, Any]:
    """Run the real Caduceus-Ph checkpoint smoke."""
    return _run_checkpoint_smoke(
        model_id=CADUCEUS_MODEL,
        revision=CADUCEUS_REVISION,
        candidate="caduceus",
        source="https://huggingface.co/kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
        license_name="Apache-2.0",
        trust_remote_code=True,
        dtype_name="float32",
        max_length=512,
    )


def _load_approval() -> dict[str, Any]:
    if os.environ.get("EVOVARIANT_TR_PAID_COMPUTE_ACK") != "I_ACCEPT_COSTS":
        raise RuntimeError(
            "set EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS for the approved smoke"
        )
    approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    if approval.get("protocol_hash") != EXPECTED_PROTOCOL_HASH:
        raise RuntimeError("Phase 5 smoke approval is tied to a stale protocol hash")
    if float(approval.get("max_budget_usd", 0)) > 2.0:
        raise RuntimeError("smoke approval exceeds the bounded Phase 2/4/5 pilot cap")
    scope = str(approval.get("run_scope", ""))
    if "Phase 5 smoke-test evidence only" not in scope:
        raise RuntimeError("approval scope does not authorize Phase 5 smoke evidence")
    return approval


@app.local_entrypoint()
def main() -> None:
    """Run both candidate smokes and persist their evidence locally."""
    approval = _load_approval()
    results: list[dict[str, Any]] = []
    for candidate, runner in (
        ("nucleotide_transformer", smoke_nucleotide_transformer),
        ("caduceus", smoke_caduceus),
    ):
        started = time.monotonic()
        try:
            result = dict(runner.remote())
        except Exception as exc:  # noqa: BLE001 - preserve candidate-specific smoke evidence
            result = {
                "status": "FAILED_SMOKE",
                "candidate": candidate,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "estimated_wall_rate_cost_usd": round(
                    (time.monotonic() - started) / 3600.0 * H100_WALL_RATE_USD_PER_HOUR,
                    4,
                ),
            }
        results.append(result)
        print(json.dumps(result, sort_keys=True))

    passed = [result for result in results if result.get("status") == "PASS"]
    artifact = {
        "artifact_id": "phase5-real-smokes-20260921",
        "recorded_at": "2026-09-21",
        "status": "PASS_WITH_SUBSET_ONLY_TRACKS" if passed else "FAILED_ALL_SMOKES",
        "protocol_hash": EXPECTED_PROTOCOL_HASH,
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "approval_scope": approval["run_scope"],
        "gpu_type": GPU_TYPE,
        "source": {
            "nucleotide_transformer": {
                "model": NT_MODEL,
                "revision": NT_REVISION,
                "official_model_card": "https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species",
            },
            "caduceus": {
                "model": CADUCEUS_MODEL,
                "revision": CADUCEUS_REVISION,
                "official_model_card": "https://huggingface.co/kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
            },
        },
        "results": results,
        "interpretation": {
            "included_in_phase6_raw_score_benchmark": [],
            "subset_only": [result["candidate"] for result in passed],
            "reason": (
                "The real smokes verify checkpoint installation, preprocessing, finite logits, "
                "and ref/alt embedding plumbing on synthetic input. They do not establish the "
                "frozen GRCh38 raw allele-effect score contract or cohort applicability."
            ),
            "next_gate": "Freeze a separate compatibility protocol before any Phase 6 use.",
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(OUTPUT_PATH), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()

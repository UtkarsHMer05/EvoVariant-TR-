#!/usr/bin/env python
"""Run the mandatory Caduceus load/gradient/checkpoint smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint, save_checkpoint
from evovariant_tr.adaptation.models import (
    MODEL_IDS,
    MODEL_REVISIONS,
    PairedClassifier,
    finite_tensor,
    load_backbone,
    tokenize_sequences,
)
from evovariant_tr.adaptation.state import record_stage
from evovariant_tr.sequence_mutate import reverse_complement


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/adaptation/caduceus_smoke.json")
    parser.add_argument("--checkpoint")
    parser.add_argument("--cache-dir")
    parser.add_argument("--state")
    parser.add_argument("--root", default=".")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.device.startswith("cuda"):
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("Caduceus smoke requires an available CUDA device")
    import torch

    random.seed(42)
    torch.manual_seed(42)
    started = time.monotonic()
    if args.device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size)
    sequence = "ACGT" * 32
    reference = tokenize_sequences(
        tokenizer, [sequence], max_length=len(sequence), device=args.device
    )
    alternate = tokenize_sequences(
        tokenizer,
        ["ACGT" * 16 + "TCGT" * 16],
        max_length=len(sequence),
        device=args.device,
    )
    reference_rc = tokenize_sequences(
        tokenizer, [reverse_complement(sequence)], max_length=len(sequence), device=args.device
    )
    alternate_rc = tokenize_sequences(
        tokenizer,
        [reverse_complement("ACGT" * 16 + "TCGT" * 16)],
        max_length=len(sequence),
        device=args.device,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    model.train()
    logits = model(reference, alternate, reference_rc, alternate_rc)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, torch.ones_like(logits))
    if not finite_tensor(logits) or not finite_tensor(loss):
        raise SystemExit("non-finite Caduceus smoke output")
    loss.backward()
    gradient_values = [
        parameter.grad.detach().abs().max()
        for parameter in model.parameters()
        if parameter.grad is not None
    ]
    if not gradient_values or not all(torch.isfinite(value) for value in gradient_values):
        raise SystemExit("non-finite Caduceus smoke gradient")
    optimizer.step()
    checkpoint = Path(args.checkpoint) if args.checkpoint else Path(args.output).with_suffix(".pt")
    save_checkpoint(
        checkpoint,
        model=model,
        optimizer=optimizer,
        epoch=0,
        metrics={"smoke_loss": float(loss.detach().cpu())},
        protocol_hash="07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c",
    )
    load_checkpoint(
        checkpoint,
        model=model,
        optimizer=optimizer,
        expected_protocol_hash="07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c",
        map_location=args.device,
    )
    model.eval()
    with torch.no_grad():
        expected = model(reference, alternate, reference_rc, alternate_rc)
    load_checkpoint(
        checkpoint,
        model=model,
        expected_protocol_hash="07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c",
        map_location=args.device,
    )
    model.eval()
    with torch.no_grad():
        actual = model(reference, alternate, reference_rc, alternate_rc)
    reload_compatible = bool(torch.allclose(expected, actual, rtol=1e-5, atol=1e-6))
    if not reload_compatible:
        raise SystemExit("checkpoint reload changed the prediction")
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    report = {
        "status": "PASS",
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "device": args.device,
        "hidden_size": hidden_size,
        "sequence_length": len(sequence),
        "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
        "trainable_parameters": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "logit_finite": math.isfinite(float(logits.detach().cpu().item())),
        "loss_finite": math.isfinite(float(loss.detach().cpu().item())),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": digest,
        "checkpoint_reload_prediction_compatible": reload_compatible,
        "runtime_seconds": time.monotonic() - started,
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated())
        if args.device.startswith("cuda")
        else None,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    if args.state:
        record_stage(
            args.state,
            project_root=args.root,
            stage="CADUCEUS_SMOKE_PASS",
            artifacts=(output, checkpoint),
            details=report,
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

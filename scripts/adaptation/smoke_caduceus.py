#!/usr/bin/env python
"""Run the mandatory Caduceus load/gradient/checkpoint smoke test."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint, save_checkpoint
from evovariant_tr.adaptation.models import MODEL_IDS, MODEL_REVISIONS, PairedClassifier, finite_tensor, load_backbone, tokenize_sequences


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/adaptation/caduceus_smoke.json")
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.device.startswith("cuda"):
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("Caduceus smoke requires an available CUDA device")
    import torch

    random.seed(42)
    torch.manual_seed(42)
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size)
    sequence = "ACGT" * 32
    reference = tokenize_sequences(tokenizer, [sequence], max_length=len(sequence), device=args.device)
    alternate = tokenize_sequences(
        tokenizer, ["ACGT" * 16 + "TCGT" * 16],
        max_length=len(sequence),
        device=args.device,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    model.train()
    logits = model(reference, alternate)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, torch.ones_like(logits)
    )
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
    checkpoint = Path(args.output).with_suffix(".pt")
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
    report = {
        "status": "PASS",
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "device": args.device,
        "hidden_size": hidden_size,
        "sequence_length": len(sequence),
        "logit_finite": math.isfinite(float(logits.detach().cpu().item())),
        "loss_finite": math.isfinite(float(loss.detach().cpu().item())),
        "checkpoint": str(checkpoint),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


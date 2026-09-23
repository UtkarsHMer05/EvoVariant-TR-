# Evidence snapshot from the incomplete adaptation branch.
# Source: research/posthoc-foundation-adaptation
# Snapshot commit: 196393636b069dfeaa8dbd43f41b543d0b20d91a
# Purpose: experimental fine-tuning evidence; not part of frozen baseline inference

#!/usr/bin/env python3
"""Prove that a partial Caduceus step changes an encoder parameter."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

from evovariant_tr.adaptation.data import (
    EXPECTED_MANIFEST_SHA256,
    load_train_rows,
    paired_sequences,
    sha256_file,
)
from evovariant_tr.adaptation.models import (
    MODEL_IDS,
    MODEL_REVISIONS,
    PairedClassifier,
    configure_trainable,
    load_backbone,
    tokenize_sequences,
)
from evovariant_tr.adaptation.state import record_stage

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def _digest(value) -> str:
    return hashlib.sha256(value.detach().float().cpu().numpy().tobytes()).hexdigest()


def _blocks(names: list[str]) -> list[int]:
    return sorted(
        {
            int(match.group(1))
            for name in names
            if (match := re.search(r"(?:^|\.)(?:layers|blocks)\.(\d+)(?:\.|$)", name))
        }
    )


def _gradient_norm(parameters) -> float:
    import torch

    values = [parameter.grad.detach().float().pow(2).sum() for parameter in parameters
              if parameter.grad is not None]
    return math.sqrt(float(torch.stack(values).sum())) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--output", required=True)
    parser.add_argument("--state")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import torch
    from pyfaidx import Fasta

    if not args.device.startswith("cuda") or not torch.cuda.is_available():
        raise SystemExit("encoder-update proof requires an eligible CUDA runtime")
    if args.batch_size < 1:
        raise SystemExit("batch size must be positive")

    torch.manual_seed(args.seed)
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    state_path = (
        Path(args.state).resolve() if args.state else output.parent / "adaptation_state.json"
    )
    rows = load_train_rows(root)[:args.batch_size]
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size, dropout=0.1)
    total_parameters, trainable_parameters = configure_trainable(model, "partial_small")
    trainable_backbone_names = [
        name for name, parameter in model.backbone.named_parameters() if parameter.requires_grad
    ]
    frozen_backbone_names = [
        name for name, parameter in model.backbone.named_parameters() if not parameter.requires_grad
    ]
    encoder_parameters = [
        (name, parameter) for name, parameter in model.named_parameters()
        if name.startswith("backbone.") and parameter.requires_grad
    ]
    frozen_controls = [
        (name, parameter) for name, parameter in model.named_parameters()
        if name.startswith("backbone.") and not parameter.requires_grad
    ]
    if not encoder_parameters or not frozen_controls:
        raise RuntimeError(
            "partial_small did not produce both trainable and frozen encoder parameters"
        )
    chosen_name, chosen_parameter = encoder_parameters[0]
    control_name, control_parameter = frozen_controls[0]
    before = chosen_parameter.detach().float().cpu().clone()
    control_before = control_parameter.detach().float().cpu().clone()
    pairs = [paired_sequences(fasta, row, args.max_length) for row in rows]
    inputs = tuple(
        tokenize_sequences(
            tokenizer,
            [getattr(pair, field) for pair in pairs],
            max_length=args.max_length,
            device=args.device,
        )
        for field in ("reference", "alternate", "reference_rc", "alternate_rc")
    )
    labels = torch.tensor([row.label for row in rows], dtype=torch.float32, device=args.device)
    optimizer = torch.optim.AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=2e-5,
        weight_decay=0.01,
    )
    optimizer.zero_grad(set_to_none=True)
    logits = model(*inputs)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, labels)
    if not torch.isfinite(loss):
        raise RuntimeError("encoder-update proof loss is not finite")
    loss.backward()
    encoder_gradient_norm = _gradient_norm(parameter for _, parameter in encoder_parameters)
    head_gradient_norm = _gradient_norm(
        parameter for name, parameter in model.named_parameters() if name.startswith("classifier.")
    )
    if encoder_gradient_norm <= 0 or head_gradient_norm <= 0:
        raise RuntimeError("encoder-update proof produced no encoder or classifier gradient")
    optimizer.step()
    after = chosen_parameter.detach().float().cpu()
    control_after = control_parameter.detach().float().cpu()
    encoder_delta_norm = float(torch.linalg.vector_norm(after - before))
    frozen_control_delta_norm = float(torch.linalg.vector_norm(control_after - control_before))
    status = "PASS" if encoder_delta_norm > 0 and frozen_control_delta_norm == 0 else "FAIL"
    report = {
        "status": status,
        "model_id": MODEL_IDS["caduceus"],
        "model_revision": MODEL_REVISIONS["caduceus"],
        "protocol_sha256": PROTOCOL_HASH,
        "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
        "reference_sha256": sha256_file(args.reference),
        "rows_used": len(rows),
        "total_params": total_parameters,
        "trainable_params": trainable_parameters,
        "trainable_percent": 100 * trainable_parameters / total_parameters,
        "trainable_backbone_blocks": _blocks(trainable_backbone_names),
        "frozen_backbone_blocks": _blocks(frozen_backbone_names),
        "encoder_gradient_norm": encoder_gradient_norm,
        "head_gradient_norm": head_gradient_norm,
        "chosen_encoder_parameter": chosen_name,
        "frozen_control_parameter": control_name,
        "before_checksum": _digest(before),
        "after_checksum": _digest(after),
        "before_value_sample": before.reshape(-1)[:8].tolist(),
        "after_value_sample": after.reshape(-1)[:8].tolist(),
        "encoder_delta_norm": encoder_delta_norm,
        "frozen_control_delta_norm": frozen_control_delta_norm,
        "loss": float(loss.detach().cpu()),
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "runtime_seconds": time.monotonic() - started,
    }
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    record_stage(
        state_path,
        project_root=root,
        stage="CADUCEUS_ENCODER_UPDATE_PROOF",
        artifacts=(output,),
        details=report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if status != "PASS":
        raise SystemExit("encoder-update proof failed")


if __name__ == "__main__":
    main()

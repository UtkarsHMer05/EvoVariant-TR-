#!/usr/bin/env python
"""Train the Caduceus paired head on TRAIN only, with atomic checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

from evovariant_tr.adaptation import selection_seed_allowed
from evovariant_tr.adaptation.checkpointing import load_checkpoint, save_checkpoint
from evovariant_tr.adaptation.data import (
    EXPECTED_MANIFEST_SHA256,
    load_train_rows,
    sha256_file,
)
from evovariant_tr.adaptation.models import (
    MODEL_IDS,
    MODEL_REVISIONS,
    PairedClassifier,
    configure_trainable,
    load_backbone,
    trainable_parameter_manifest,
)
from evovariant_tr.adaptation.state import record_stage
from evovariant_tr.adaptation.training import TrainConfig, train_epoch

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--stage",
        choices=("frozen_head_only", "partial_small", "partial_large", "full_if_feasible", "full"),
        default="frozen_head_only",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--effective-batch-size", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume")
    parser.add_argument("--selection-lock")
    parser.add_argument("--fixed-seed-robustness", action="store_true")
    parser.add_argument("--state")
    args = parser.parse_args()
    if args.epochs < 1:
        raise SystemExit("epochs must be positive")
    random.seed(args.seed)
    import torch
    from pyfaidx import Fasta

    torch.manual_seed(args.seed)
    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = (
        Path(args.state).resolve()
        if args.state
        else output_dir.resolve().parent.parent / "state" / "adaptation_state.json"
    )
    train_rows = load_train_rows(root)
    reference_sha256 = sha256_file(args.reference)
    data_report = {
        "train_record_count": len(train_rows),
        "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
        "reference_sha256": reference_sha256,
    }
    config_record = {
        "stage": args.stage,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "effective_batch_size": args.effective_batch_size,
        "dropout": args.dropout,
        "max_length": args.max_length,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "seed": args.seed,
        "reference_sha256": reference_sha256,
    }
    if args.selection_lock:
        selection = json.loads(Path(args.selection_lock).read_text(encoding="utf-8"))
        selected = selection.get("selected_params", {})
        if (
            selection.get("status") != "SELECTION_CLOSED"
            or selection.get("protocol_sha256") != PROTOCOL_HASH
            or selection.get("train_manifest_sha256")
            != EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"]
            or selection.get("reference_sha256") != reference_sha256
            or args.epochs != selection.get("final_epochs")
            or not selection_seed_allowed(
                args.seed, selection.get("seed"), args.fixed_seed_robustness
            )
            or args.stage != selected.get("regime")
            or args.learning_rate != selected.get("learning_rate")
            or args.weight_decay != selected.get("weight_decay")
            or args.dropout != selected.get("dropout")
            or args.effective_batch_size != selected.get("effective_batch_size")
        ):
            raise SystemExit("final training config does not match the closed TRAIN-only selection")
        config_record["fixed_seed_robustness"] = args.fixed_seed_robustness
        config_record["selection_lock_sha256"] = hashlib.sha256(
            Path(args.selection_lock).read_bytes()
        ).hexdigest()
    config_hash = hashlib.sha256(json.dumps(config_record, sort_keys=True).encode()).hexdigest()
    checkpoint_metadata = {
        "config_sha256": config_hash,
        "model_revision": MODEL_REVISIONS["caduceus"],
        "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
        "reference_sha256": reference_sha256,
    }
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    if args.device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size, dropout=args.dropout)
    regime = "full" if args.stage == "full_if_feasible" else args.stage
    total_parameters, trainable_parameters = configure_trainable(model, regime)
    parameter_manifest_path = output_dir / "trainable_parameter_manifest.json"
    parameter_manifest = trainable_parameter_manifest(model)
    manifest_tmp = parameter_manifest_path.with_name(parameter_manifest_path.name + ".tmp")
    manifest_tmp.write_text(json.dumps(parameter_manifest, indent=2, sort_keys=True) + "\n")
    os.replace(manifest_tmp, parameter_manifest_path)
    optimizer = torch.optim.AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    start_epoch = 0
    if args.resume:
        payload = load_checkpoint(
            args.resume,
            model=model,
            optimizer=optimizer,
            expected_protocol_hash=PROTOCOL_HASH,
            expected_metadata=checkpoint_metadata,
            map_location=args.device,
        )
        start_epoch = int(payload["epoch"]) + 1
    config = TrainConfig(
        batch_size=args.batch_size,
        gradient_accumulation_steps=max(1, args.effective_batch_size // args.batch_size),
        max_length=args.max_length,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        amp=args.device.startswith("cuda"),
    )
    for epoch in range(start_epoch, args.epochs):
        loss = train_epoch(
            model, tokenizer, fasta, train_rows, optimizer, config=config, device=args.device
        )
        save_checkpoint(
            output_dir / "latest.pt",
            model=model,
            optimizer=optimizer,
            epoch=epoch,
            metrics={"loss": loss},
            protocol_hash=PROTOCOL_HASH,
            metadata=checkpoint_metadata,
        )
        latest = output_dir / "latest.json"
        temporary = latest.with_name(latest.name + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "status": "TRAIN_ONLY_PROGRESS",
                    "config_sha256": config_hash,
                    "stage": args.stage,
                    "epoch": epoch,
                    "loss": loss,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(latest)
        record_stage(
            state_path,
            project_root=root,
            stage=f"CADUCEUS_{args.stage.upper()}_TRAIN_PROGRESS",
            artifacts=(output_dir / "latest.pt", latest),
            details={"epoch": epoch, "loss": loss},
        )
        print(json.dumps({"epoch": epoch, "loss": loss}, sort_keys=True))
    report = {
        "status": "PASS",
        "stage": args.stage,
        "selection_scope": "TRAIN_ONLY",
        "holdout_evaluated": False,
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "config": config_record,
        "config_sha256": config_hash,
        "total_parameters": total_parameters,
        "trainable_parameters": trainable_parameters,
        "trainable_parameter_manifest": str(parameter_manifest_path),
        "trainable_parameter_manifest_sha256": sha256_file(parameter_manifest_path),
        "protocol_sha256": PROTOCOL_HASH,
        "data": data_report,
        "checkpoint": str(output_dir / "latest.pt"),
        "seed": args.seed,
        "seed_mode": "fixed_seed_robustness" if args.fixed_seed_robustness else "primary",
        "epochs": args.epochs,
        "runtime_seconds": time.monotonic() - started,
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated())
        if args.device.startswith("cuda")
        else None,
        "checkpoint_bytes": (output_dir / "latest.pt").stat().st_size,
        "checkpoint_sha256": sha256_file(output_dir / "latest.pt"),
    }
    report_path = output_dir / "run.json"
    temporary = report_path.with_name(report_path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(report_path)
    record_stage(
        state_path,
        project_root=root,
        stage="CADUCEUS_FINAL_TRAINED"
        if args.selection_lock
        else f"CADUCEUS_{args.stage.upper()}_DONE",
        artifacts=(report_path, output_dir / "latest.pt"),
        details=report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

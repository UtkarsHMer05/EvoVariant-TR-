#!/usr/bin/env python
"""Train the Caduceus paired head on TRAIN only, with atomic checkpoints."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint, save_checkpoint
from evovariant_tr.adaptation.data import load_formal_rows, verify_formal_data
from evovariant_tr.adaptation.models import MODEL_IDS, MODEL_REVISIONS, PairedClassifier, load_backbone
from evovariant_tr.adaptation.training import TrainConfig, evaluate, train_epoch

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--stage", choices=("frozen", "partial", "full"), default="frozen")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume")
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
    train_rows, _ = load_formal_rows(root)
    data_report = verify_formal_data(root)
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size)
    if args.stage == "frozen":
        model.backbone.requires_grad_(False)
        model.backbone.eval()
    elif args.stage == "partial":
        parameters = list(model.backbone.parameters())
        for parameter in parameters:
            parameter.requires_grad_(False)
        for parameter in parameters[-max(1, len(parameters) // 4):]:
            parameter.requires_grad_(True)
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
            map_location=args.device,
        )
        start_epoch = int(payload["epoch"]) + 1
    config = TrainConfig(
        batch_size=args.batch_size,
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
        train_metrics, _ = evaluate(
            model, tokenizer, fasta, train_rows, config=config, device=args.device
        )
        save_checkpoint(
            output_dir / "latest.pt",
            model=model,
            optimizer=optimizer,
            epoch=epoch,
            metrics={"loss": loss, **train_metrics},
            protocol_hash=PROTOCOL_HASH,
        )
        (output_dir / "latest.json").write_text(
            json.dumps(
                {
                    "status": "TRAIN_ONLY_PROGRESS",
                    "stage": args.stage,
                    "epoch": epoch,
                    "loss": loss,
                    "train_metrics": train_metrics,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"epoch": epoch, "loss": loss, **train_metrics}, sort_keys=True))
    report = {
        "status": "PASS",
        "stage": args.stage,
        "selection_scope": "TRAIN_ONLY",
        "holdout_evaluated": False,
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "protocol_sha256": PROTOCOL_HASH,
        "data": data_report,
        "checkpoint": str(output_dir / "latest.pt"),
        "seed": args.seed,
        "epochs": args.epochs,
    }
    (output_dir / "run.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


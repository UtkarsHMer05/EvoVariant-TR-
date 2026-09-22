#!/usr/bin/env python
"""Evaluate one final Caduceus system and write immutable predictions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint
from evovariant_tr.adaptation.data import load_formal_rows, verify_formal_data
from evovariant_tr.adaptation.metrics import binary_metrics
from evovariant_tr.adaptation.models import MODEL_IDS, MODEL_REVISIONS, PairedClassifier, load_backbone
from evovariant_tr.adaptation.training import TrainConfig, evaluate

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", choices=("train", "validation"), default="validation")
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=8192)
    args = parser.parse_args()
    output = Path(args.output)
    if args.split == "validation" and output.exists():
        raise SystemExit("validation output already exists; the 801-row holdout is one-shot")
    import torch
    from pyfaidx import Fasta

    root = Path(args.root).resolve()
    train_rows, validation_rows = load_formal_rows(root)
    rows = train_rows if args.split == "train" else validation_rows
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    model = PairedClassifier.build(backbone, hidden_size)
    load_checkpoint(
        args.checkpoint,
        model=model,
        expected_protocol_hash=PROTOCOL_HASH,
        map_location=args.device,
    )
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    metrics, probabilities = evaluate(
        model,
        tokenizer,
        fasta,
        rows,
        config=TrainConfig(batch_size=args.batch_size, max_length=args.max_length, amp=False),
        device=args.device,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["normalized_variant_id", "gene_symbol", "label", "probability"],
        )
        writer.writeheader()
        for row, probability in zip(rows, probabilities):
            writer.writerow(
                {
                    "normalized_variant_id": row.normalized_variant_id,
                    "gene_symbol": row.gene_symbol,
                    "label": row.label,
                    "probability": probability,
                }
            )
    report = {
        "status": "PASS",
        "split": args.split,
        "holdout_evaluated": args.split == "validation",
        "selection_scope": "NONE_AFTER_FINALIZATION",
        "metrics": metrics,
        "rows": len(rows),
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "protocol_sha256": PROTOCOL_HASH,
        "data": verify_formal_data(root),
    }
    output.with_suffix(".json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


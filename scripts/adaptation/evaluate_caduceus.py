#!/usr/bin/env python
"""Evaluate one final Caduceus system and write immutable predictions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint
from evovariant_tr.adaptation.data import (
    EXPECTED_MANIFEST_SHA256,
    load_formal_rows,
    sha256_file,
    verify_formal_data,
)
from evovariant_tr.adaptation.models import (
    MODEL_IDS,
    MODEL_REVISIONS,
    PairedClassifier,
    configure_trainable,
    load_backbone,
)
from evovariant_tr.adaptation.state import record_stage
from evovariant_tr.adaptation.training import TrainConfig, evaluate

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--selection-lock")
    parser.add_argument("--state")
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", choices=("train", "validation"), default="validation")
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-length", type=int, default=8192)
    args = parser.parse_args()
    output = Path(args.output)
    report_path = output.with_suffix(".json")
    selection_hash = None
    if args.split == "validation":
        if not args.selection_lock:
            raise SystemExit("validation evaluation requires a closed TRAIN-only selection lock")
        selection_path = Path(args.selection_lock)
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        if (
            selection.get("status") != "SELECTION_CLOSED"
            or selection.get("protocol_sha256") != PROTOCOL_HASH
            or selection.get("train_manifest_sha256")
            != EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"]
        ):
            raise SystemExit("selection lock does not match the frozen adaptation protocol")
        selection_hash = hashlib.sha256(selection_path.read_bytes()).hexdigest()
    if args.split == "validation" and (output.exists() or report_path.exists()):
        raise SystemExit("validation output already exists; the 801-row holdout is one-shot")
    import torch
    from pyfaidx import Fasta

    root = Path(args.root).resolve()
    reference_sha256 = sha256_file(args.reference)
    if args.split == "validation" and selection.get("reference_sha256") != reference_sha256:
        raise SystemExit("evaluation reference FASTA does not match the closed selection")
    train_rows, validation_rows = load_formal_rows(root)
    rows = train_rows if args.split == "train" else validation_rows
    expected_metadata = None
    selected = None
    if args.split == "validation":
        selected = selection["selected_params"]
        if args.seed != selection.get("seed"):
            raise SystemExit("evaluation seed does not match the closed selection")
        config_record = {
            "stage": selected["regime"],
            "epochs": selection["final_epochs"],
            "batch_size": 1,
            "effective_batch_size": selected["effective_batch_size"],
            "dropout": selected["dropout"],
            "max_length": args.max_length,
            "learning_rate": selected["learning_rate"],
            "weight_decay": selected["weight_decay"],
            "seed": selection["seed"],
            "reference_sha256": reference_sha256,
            "selection_lock_sha256": selection_hash,
        }
        config_hash = hashlib.sha256(json.dumps(config_record, sort_keys=True).encode()).hexdigest()
        expected_metadata = {
            "config_sha256": config_hash,
            "model_revision": MODEL_REVISIONS["caduceus"],
            "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
            "reference_sha256": reference_sha256,
        }
    if args.device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    tokenizer, backbone, hidden_size = load_backbone(
        "caduceus", device=args.device, cache_dir=args.cache_dir
    )
    dropout = selected["dropout"] if selected else 0.1
    model = PairedClassifier.build(backbone, hidden_size, dropout=dropout)
    regime = "frozen_head_only"
    if args.split == "validation":
        regime = selected["regime"]
        regime = "full" if regime == "full_if_feasible" else regime
    total_parameters, trainable_parameters = configure_trainable(model, regime)
    load_checkpoint(
        args.checkpoint,
        model=model,
        expected_protocol_hash=PROTOCOL_HASH,
        expected_metadata=expected_metadata,
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
    temporary_csv = output.with_name(output.name + ".tmp")
    with temporary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["normalized_variant_id", "gene_symbol", "label", "probability"],
        )
        writer.writeheader()
        for row, probability in zip(rows, probabilities, strict=True):
            writer.writerow(
                {
                    "normalized_variant_id": row.normalized_variant_id,
                    "gene_symbol": row.gene_symbol,
                    "label": row.label,
                    "probability": probability,
                }
            )
    temporary_csv.replace(output)
    report = {
        "status": "PASS",
        "split": args.split,
        "cohort_label": "POST-HOC ADAPTATION HOLDOUT" if args.split == "validation" else "TRAIN",
        "holdout_evaluated": args.split == "validation",
        "selection_scope": "NONE_AFTER_FINALIZATION",
        "metrics": metrics,
        "rows": len(rows),
        "model_id": MODEL_IDS["caduceus"],
        "revision": MODEL_REVISIONS["caduceus"],
        "reference_sha256": reference_sha256,
        "protocol_sha256": PROTOCOL_HASH,
        "selection_lock_sha256": selection_hash,
        "training_config_sha256": config_hash if args.split == "validation" else None,
        "total_parameters": total_parameters,
        "trainable_parameters": trainable_parameters,
        "runtime_seconds": time.monotonic() - started,
        "samples_per_second": len(rows) / max(time.monotonic() - started, 1e-9),
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated())
        if args.device.startswith("cuda")
        else None,
        "checkpoint_bytes": Path(args.checkpoint).stat().st_size,
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "data": verify_formal_data(root),
    }
    temporary_json = report_path.with_name(report_path.name + ".tmp")
    temporary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_json.replace(report_path)
    if args.split == "validation" and args.state:
        record_stage(
            args.state,
            project_root=root,
            stage="CADUCEUS_HOLDOUT_DONE",
            artifacts=(output, report_path),
            details=report,
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

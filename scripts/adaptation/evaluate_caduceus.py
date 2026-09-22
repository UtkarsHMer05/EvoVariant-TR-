#!/usr/bin/env python
"""Evaluate one final Caduceus system and write immutable predictions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path

from evovariant_tr.adaptation.calibration import (
    apply_calibrator,
    selective_metrics_at_thresholds,
)
from evovariant_tr.adaptation.checkpointing import load_checkpoint
from evovariant_tr.adaptation.data import (
    EXPECTED_MANIFEST_SHA256,
    load_formal_rows,
    sha256_file,
    verify_formal_data,
)
from evovariant_tr.adaptation.metrics import binary_metrics
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
    parser.add_argument("--calibration-report")
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
    attempt_path = output.with_name(f"{output.stem}.attempt.json")
    temporary_csv = output.with_name(output.name + ".tmp")
    temporary_json = report_path.with_name(report_path.name + ".tmp")
    selection_hash = None
    calibration_report = None
    calibration_report_hash = None
    if args.split == "validation":
        if not args.selection_lock or not args.calibration_report:
            raise SystemExit(
                "validation needs a closed selection lock and TRAIN-OOF calibration report"
            )
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
        calibration_path = Path(args.calibration_report)
        calibration_report = json.loads(calibration_path.read_text(encoding="utf-8"))
        if (
            calibration_report.get("status") != "PASS"
            or calibration_report.get("fit_scope") != "TRAIN_OOF_ONLY"
            or calibration_report.get("holdout_used_for_fit") is not False
            or calibration_report.get("protocol_sha256") != PROTOCOL_HASH
            or calibration_report.get("oof_train_manifest_sha256")
            != EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"]
            or calibration_report.get("oof_predictions_sha256")
            != selection.get("train_oof_sha256")
        ):
            raise SystemExit("calibration report does not match the closed TRAIN-OOF selection")
        calibration_report_hash = sha256_file(calibration_path)
    if args.split == "validation" and any(
        path.exists() for path in (attempt_path, output, report_path, temporary_csv, temporary_json)
    ):
        raise SystemExit("validation was already attempted or has partial output; refusing a rerun")
    import torch
    from pyfaidx import Fasta

    root = Path(args.root).resolve()
    reference_sha256 = sha256_file(args.reference)
    if args.split == "validation" and selection.get("reference_sha256") != reference_sha256:
        raise SystemExit("evaluation reference FASTA does not match the closed selection")
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
        if selected is None:
            raise SystemExit("validation selection parameters are missing")
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
    attempt_hash = None
    if args.split == "validation":
        output.parent.mkdir(parents=True, exist_ok=True)
        attempt = {
            "status": "ATTEMPT_STARTED",
            "protocol_sha256": PROTOCOL_HASH,
            "selection_lock_sha256": selection_hash,
            "calibration_report_sha256": calibration_report_hash,
            "reference_sha256": reference_sha256,
            "checkpoint_sha256": sha256_file(args.checkpoint),
        }
        try:
            descriptor = os.open(attempt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as err:
            raise SystemExit("validation attempt marker already exists; refusing a rerun") from err
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(attempt, indent=2, sort_keys=True) + "\n")
        attempt_hash = sha256_file(attempt_path)
        if args.state:
            record_stage(
                args.state,
                project_root=root,
                stage="CADUCEUS_HOLDOUT_ATTEMPTED",
                artifacts=(attempt_path,),
                details=attempt,
            )
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    train_rows, validation_rows = load_formal_rows(root)
    rows = train_rows if args.split == "train" else validation_rows
    metrics, probabilities = evaluate(
        model,
        tokenizer,
        fasta,
        rows,
        config=TrainConfig(batch_size=args.batch_size, max_length=args.max_length, amp=False),
        device=args.device,
    )
    calibrated_probabilities = None
    calibrated_metrics = None
    abstention_metrics = None
    oof_mcc_threshold = None
    if calibration_report is not None:
        clipped = [min(1 - 1e-7, max(1e-7, p)) for p in probabilities]
        logits = [math.log(p / (1 - p)) for p in clipped]
        calibrated_probabilities = apply_calibrator(
            logits, calibration_report["calibrators"]
        )
        labels = [row.label for row in rows]
        calibrated_metrics = binary_metrics(labels, calibrated_probabilities)
        oof_mcc_threshold = float(
            calibration_report["mcc_threshold_supplementary"]["threshold"]
        )
        calibrated_metrics_at_oof_mcc_threshold = binary_metrics(
            labels, calibrated_probabilities, threshold=oof_mcc_threshold
        )
        abstention_metrics = selective_metrics_at_thresholds(
            labels, calibrated_probabilities, calibration_report["selective_metrics"]
        )
    else:
        calibrated_metrics_at_oof_mcc_threshold = None
    output.parent.mkdir(parents=True, exist_ok=True)
    with temporary_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["normalized_variant_id", "gene_symbol", "label", "probability"]
        if calibrated_probabilities is not None:
            fieldnames.append("calibrated_probability")
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="raise",
        )
        writer.writeheader()
        for index, (row, probability) in enumerate(zip(rows, probabilities, strict=True)):
            result = {
                "normalized_variant_id": row.normalized_variant_id,
                "gene_symbol": row.gene_symbol,
                "label": row.label,
                "probability": probability,
            }
            if calibrated_probabilities is not None:
                result["calibrated_probability"] = calibrated_probabilities[index]
            writer.writerow(result)
    temporary_csv.replace(output)
    report = {
        "status": "PASS",
        "split": args.split,
        "cohort_label": "POST-HOC ADAPTATION HOLDOUT" if args.split == "validation" else "TRAIN",
        "holdout_evaluated": args.split == "validation",
        "selection_scope": "NONE_AFTER_FINALIZATION",
        "metrics": metrics,
        "metrics_calibrated": calibrated_metrics,
        "metrics_calibrated_at_oof_mcc_threshold": calibrated_metrics_at_oof_mcc_threshold,
        "selective_metrics_at_oof_thresholds": abstention_metrics,
        "calibration_report_sha256": calibration_report_hash,
        "calibrator_method": calibration_report["calibrators"]["selected_method"]
        if calibration_report is not None
        else None,
        "calibration_fit_scope": calibration_report["fit_scope"]
        if calibration_report is not None
        else None,
        "calibration_oof_predictions_sha256": calibration_report["oof_predictions_sha256"]
        if calibration_report is not None
        else None,
        "evaluation_attempt_sha256": attempt_hash,
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
    temporary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_json.replace(report_path)
    if args.split == "validation" and args.state:
        record_stage(
            args.state,
            project_root=root,
            stage="CADUCEUS_HOLDOUT_DONE",
            artifacts=(attempt_path, output, report_path),
            details=report,
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Resumable TRAIN-only grouped-CV search for the Caduceus paired classifier."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

from evovariant_tr.adaptation.checkpointing import load_checkpoint, save_checkpoint
from evovariant_tr.adaptation.data import EXPECTED_MANIFEST_SHA256, load_train_rows, sha256_file
from evovariant_tr.adaptation.folds import make_grouped_folds
from evovariant_tr.adaptation.models import (
    MODEL_IDS,
    MODEL_REVISIONS,
    PairedClassifier,
    configure_trainable,
    load_backbone,
)
from evovariant_tr.adaptation.state import record_stage
from evovariant_tr.adaptation.training import TrainConfig, evaluate, train_epoch

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"
TARGET_TRIALS = 8
MAX_TRIALS = 12


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _completed_trials(study):
    return [trial for trial in study.trials if trial.state.name == "COMPLETE"]


def _selection(study):
    trials = _completed_trials(study)
    if not trials:
        return None
    selected = max(
        trials,
        key=lambda trial: (
            trial.user_attrs["mean_auroc"],
            trial.user_attrs["mean_auprc"],
            trial.user_attrs["mean_mcc"],
            -trial.user_attrs["mean_brier"],
            -trial.user_attrs["runtime_seconds"],
            -trial.user_attrs["trainable_parameters"],
        ),
    )
    best_epochs = selected.user_attrs["fold_best_epochs"]
    epoch_cap = int(selected.params["epoch_cap"])
    final_epochs = min(epoch_cap, max(1, round(statistics.median(best_epochs))))
    return selected, final_epochs


def _persist(
    study,
    output: Path,
    *,
    target_trials: int,
    state_path: Path,
    root: Path,
    reference_sha256: str,
) -> None:
    complete = _completed_trials(study)
    selection = _selection(study)
    selection_path = output.with_name("selection_closed.json")
    summary = {
        "status": "IN_PROGRESS",
        "protocol_sha256": PROTOCOL_HASH,
        "model_id": MODEL_IDS["caduceus"],
        "model_revision": MODEL_REVISIONS["caduceus"],
        "reference_sha256": reference_sha256,
        "selection_scope": "TRAIN_ONLY_STRATIFIED_GROUP_KFOLD",
        "holdout_evaluated": False,
        "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
        "trials_target": target_trials,
        "trials_maximum": MAX_TRIALS,
        "trials_completed": len(complete),
        "trials_total": len(study.trials),
        "trials": [
            {
                "number": trial.number,
                "state": trial.state.name,
                "value": trial.value,
                "params": trial.params,
                "user_attrs": trial.user_attrs,
            }
            for trial in study.trials
        ],
    }
    if selection:
        trial, final_epochs = selection
        summary.update(
            {
                "best_value": trial.value,
                "best_params": trial.params,
                "selected_trial": trial.number,
                "final_epochs": final_epochs,
            }
        )
    _atomic_json(output, summary)
    if len(complete) >= target_trials and selection:
        trial, final_epochs = selection
        oof_path = Path(trial.user_attrs["oof_csv"])
        locked = {
            "status": "SELECTION_CLOSED",
            "protocol_sha256": PROTOCOL_HASH,
            "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
            "reference_sha256": reference_sha256,
            "selection_scope": "TRAIN_ONLY_STRATIFIED_GROUP_KFOLD",
            "holdout_evaluated": False,
            "selected_trial": trial.number,
            "selected_params": trial.params,
            "seed": trial.user_attrs["seed"],
            "fold_best_epochs": trial.user_attrs["fold_best_epochs"],
            "final_epochs": final_epochs,
            "train_oof_csv": str(oof_path),
            "train_oof_sha256": hashlib.sha256(oof_path.read_bytes()).hexdigest(),
            "trial_count": len(complete),
        }
        if selection_path.exists():
            previous = json.loads(selection_path.read_text(encoding="utf-8"))
            if previous != locked:
                raise RuntimeError("selection is already closed with a different configuration")
        else:
            _atomic_json(selection_path, locked)
        summary["status"] = "PASS"
        summary["selection_closed"] = True
        _atomic_json(output, summary)
    elif len(study.trials) >= MAX_TRIALS:
        summary["status"] = "INCOMPLETE_RESOURCE_OR_PRUNING_LIMIT"
        summary["selection_closed"] = False
        _atomic_json(output, summary)
    artifacts = [output]
    if selection_path.exists():
        artifacts.extend([selection_path, Path(selection[0].user_attrs["oof_csv"])])
    record_stage(
        state_path,
        project_root=root,
        stage="CADUCEUS_HPO_DONE" if selection_path.exists() else "CADUCEUS_HPO_PROGRESS",
        artifacts=artifacts,
        details={
            "trials_completed": len(complete),
            "trials_total": len(study.trials),
            "selection_closed": selection_path.exists(),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--checkpoint-dir")
    parser.add_argument("--state")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--trials", type=int, default=TARGET_TRIALS)
    parser.add_argument("--microbatch-size", type=int, choices=(1, 2), default=1)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not TARGET_TRIALS <= args.trials <= MAX_TRIALS:
        raise SystemExit(f"protocol requires {TARGET_TRIALS}-{MAX_TRIALS} completed HPO trials")

    import optuna
    import torch
    from pyfaidx import Fasta

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    state_path = (
        Path(args.state).resolve()
        if args.state
        else output.parent.parent / "state" / "adaptation_state.json"
    )
    reference_sha256 = sha256_file(args.reference)
    selection_path = output.with_name("selection_closed.json")
    if selection_path.exists():
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        if (
            selection.get("protocol_sha256") != PROTOCOL_HASH
            or selection.get("reference_sha256") != reference_sha256
        ):
            raise SystemExit("existing selection lock belongs to a different protocol")
        print(json.dumps(selection, indent=2, sort_keys=True))
        return

    rows = load_train_rows(root)
    folds = make_grouped_folds(rows, n_splits=3, seed=args.seed)
    for fit_indices, validation_indices in folds:
        fit_genes = {rows[index].gene_symbol for index in fit_indices}
        validation_genes = {rows[index].gene_symbol for index in validation_indices}
        if fit_genes & validation_genes:
            raise RuntimeError("gene overlap in grouped TRAIN fold")
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)
    database = output.with_suffix(".sqlite3")
    database.parent.mkdir(parents=True, exist_ok=True)
    storage = optuna.storages.RDBStorage(
        url=f"sqlite:///{database}",
        heartbeat_interval=60,
        grace_period=120,
        failed_trial_callback=optuna.storages.RetryFailedTrialCallback(max_retry=1),
    )
    study = optuna.create_study(
        study_name="evovariant_caduceus_train_grouped_cv_v1",
        storage=storage,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=2, n_warmup_steps=1),
        load_if_exists=True,
    )
    previous_reference_sha256 = study.user_attrs.get("reference_sha256")
    if previous_reference_sha256 and previous_reference_sha256 != reference_sha256:
        raise SystemExit("resumed HPO reference FASTA does not match the original study")
    study.set_user_attr("reference_sha256", reference_sha256)
    if not study.trials:
        for regime in ("frozen_head_only", "partial_small", "partial_large", "full_if_feasible"):
            study.enqueue_trial({"regime": regime})
    checkpoints = (
        Path(args.checkpoint_dir) if args.checkpoint_dir else output.parent / "checkpoints"
    )

    def objective(trial):
        learning_rate = trial.suggest_categorical("learning_rate", [1e-5, 3e-5, 1e-4])
        weight_decay = trial.suggest_categorical("weight_decay", [0.0, 0.01, 0.05])
        dropout = trial.suggest_categorical("dropout", [0.0, 0.1, 0.2])
        regime = trial.suggest_categorical(
            "regime", ["frozen_head_only", "partial_small", "partial_large", "full_if_feasible"]
        )
        effective_batch = trial.suggest_categorical("effective_batch_size", [16, 32])
        epoch_cap = trial.suggest_categorical("epoch_cap", [4, 6, 8])
        signature = hashlib.sha256(
            json.dumps(
                {
                    "params": trial.params,
                    "protocol": PROTOCOL_HASH,
                    "revision": MODEL_REVISIONS["caduceus"],
                    "reference_sha256": reference_sha256,
                    "seed": args.seed,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]
        config = TrainConfig(
            batch_size=args.microbatch_size,
            gradient_accumulation_steps=max(1, effective_batch // args.microbatch_size),
            max_length=args.max_length,
            epochs=epoch_cap,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            amp=args.device.startswith("cuda"),
        )
        fold_scores, fold_auprc, fold_mcc, fold_brier, best_epochs, oof = [], [], [], [], [], []
        fold_epoch_history = []
        total_parameters = trainable_parameters = 0
        peak_vram_bytes = 0
        started = time.monotonic()
        try:
            for fold_number, (fit_indices, validation_indices) in enumerate(folds):
                random_seed = args.seed + fold_number
                torch.manual_seed(random_seed)
                if args.device.startswith("cuda"):
                    torch.cuda.reset_peak_memory_stats()
                tokenizer, backbone, hidden_size = load_backbone(
                    "caduceus", device=args.device, cache_dir=args.cache_dir
                )
                model = PairedClassifier.build(backbone, hidden_size, dropout=dropout)
                total, trainable = configure_trainable(
                    model, "full" if regime == "full_if_feasible" else regime
                )
                total_parameters = total
                trainable_parameters = max(trainable_parameters, trainable)
                optimizer = torch.optim.AdamW(
                    [parameter for parameter in model.parameters() if parameter.requires_grad],
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )
                fit_rows = [rows[index] for index in fit_indices]
                validation_rows = [rows[index] for index in validation_indices]
                best_auc, best_epoch, stale_epochs = -1.0, 0, 0
                checkpoint = checkpoints / signature / f"fold_{fold_number}" / "latest.pt"
                checkpoint_metadata = {
                    "trial_signature": signature,
                    "fold": fold_number,
                    "model_revision": MODEL_REVISIONS["caduceus"],
                    "train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
                    "reference_sha256": reference_sha256,
                }
                history_path = checkpoint.with_name("history.json")
                history = json.loads(history_path.read_text()) if history_path.exists() else []
                start_epoch, best_auc, best_epoch, stale_epochs = 0, -1.0, 0, 0
                if checkpoint.exists():
                    resume = load_checkpoint(
                        checkpoint,
                        model=model,
                        optimizer=optimizer,
                        expected_protocol_hash=PROTOCOL_HASH,
                        expected_metadata=checkpoint_metadata,
                        map_location=args.device,
                    )
                    start_epoch = int(resume["epoch"]) + 1
                    best_auc = float(resume["metrics"]["best_auc"])
                    best_epoch = int(resume["metrics"]["best_epoch"])
                    stale_epochs = int(resume["metrics"]["stale_epochs"])
                for epoch in range(start_epoch, epoch_cap):
                    if stale_epochs >= 2:
                        break
                    train_loss = train_epoch(
                        model,
                        tokenizer,
                        fasta,
                        fit_rows,
                        optimizer,
                        config=config,
                        device=args.device,
                    )
                    metrics, _ = evaluate(
                        model, tokenizer, fasta, validation_rows, config=config, device=args.device
                    )
                    auc = metrics["auroc"]
                    if auc is None:
                        raise RuntimeError("TRAIN fold validation has only one class")
                    if auc > best_auc + 0.0001:
                        best_auc, best_epoch, stale_epochs = float(auc), epoch + 1, 0
                        save_checkpoint(
                            checkpoint.with_name("best.pt"),
                            model=model,
                            optimizer=optimizer,
                            epoch=epoch,
                            metrics={
                                "validation": metrics,
                                "best_auc": best_auc,
                                "best_epoch": best_epoch,
                                "stale_epochs": stale_epochs,
                            },
                            protocol_hash=PROTOCOL_HASH,
                            metadata=checkpoint_metadata,
                        )
                    else:
                        stale_epochs += 1
                    history = [item for item in history if item["epoch"] != epoch + 1]
                    history.append(
                        {
                            "epoch": epoch + 1,
                            "train_loss": train_loss,
                            "validation": metrics,
                            "learning_rate": learning_rate,
                            "peak_vram_bytes": int(torch.cuda.max_memory_allocated())
                            if args.device.startswith("cuda")
                            else None,
                        }
                    )
                    _atomic_json(history_path, history)
                    save_checkpoint(
                        checkpoint,
                        model=model,
                        optimizer=optimizer,
                        epoch=epoch,
                        metrics={
                            "validation": metrics,
                            "best_auc": best_auc,
                            "best_epoch": best_epoch,
                            "stale_epochs": stale_epochs,
                        },
                        protocol_hash=PROTOCOL_HASH,
                        metadata=checkpoint_metadata,
                    )
                    trial.report(sum(fold_scores + [best_auc]) / (fold_number + 1), fold_number)
                    if trial.should_prune():
                        raise optuna.TrialPruned()
                    if stale_epochs >= 2:
                        break
                if not checkpoint.with_name("best.pt").exists():
                    raise RuntimeError("fold completed without a best-epoch checkpoint")
                load_state = torch.load(checkpoint.with_name("best.pt"), map_location=args.device)
                model.load_state_dict(load_state["model"])
                metrics, probabilities = evaluate(
                    model, tokenizer, fasta, validation_rows, config=config, device=args.device
                )
                if args.device.startswith("cuda"):
                    peak_vram_bytes = max(peak_vram_bytes, int(torch.cuda.max_memory_allocated()))
                fold_scores.append(float(metrics["auroc"]))
                fold_auprc.append(float(metrics["auprc"]))
                fold_mcc.append(float(metrics["mcc"]))
                fold_brier.append(float(metrics["brier"]))
                best_epochs.append(best_epoch)
                fold_epoch_history.append(history)
                oof.extend(
                    (
                        fold_number,
                        row.normalized_variant_id,
                        row.gene_symbol,
                        row.label,
                        probability,
                    )
                    for row, probability in zip(validation_rows, probabilities, strict=True)
                )
                del model, backbone, tokenizer, optimizer
                if args.device.startswith("cuda"):
                    torch.cuda.empty_cache()
        except torch.cuda.OutOfMemoryError as err:
            trial.set_user_attr("resource_status", "RESOURCE_DEFERRED_T4")
            if args.device.startswith("cuda"):
                torch.cuda.empty_cache()
            raise optuna.TrialPruned("T4 ran out of memory") from err

        oof_path = output.with_name(f"{output.stem}_trial_{trial.number:02d}_train_oof.csv")
        with oof_path.with_name(oof_path.name + ".tmp").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["fold", "normalized_variant_id", "gene_symbol", "label", "probability"]
            )
            writer.writerows(oof)
        os.replace(oof_path.with_name(oof_path.name + ".tmp"), oof_path)
        trial.set_user_attr("fold_best_epochs", best_epochs)
        trial.set_user_attr("fold_epoch_history", fold_epoch_history)
        trial.set_user_attr("fold_auroc", fold_scores)
        trial.set_user_attr("mean_auroc", statistics.mean(fold_scores))
        trial.set_user_attr("mean_auprc", statistics.mean(fold_auprc))
        trial.set_user_attr("mean_mcc", statistics.mean(fold_mcc))
        trial.set_user_attr("mean_brier", statistics.mean(fold_brier))
        trial.set_user_attr("total_parameters", total_parameters)
        trial.set_user_attr("trainable_parameters", trainable_parameters)
        trial.set_user_attr("runtime_seconds", time.monotonic() - started)
        trial.set_user_attr("peak_vram_bytes", peak_vram_bytes)
        trial.set_user_attr("seed", args.seed)
        trial.set_user_attr("oof_csv", str(oof_path))
        return statistics.mean(fold_scores)

    while len(_completed_trials(study)) < args.trials and len(study.trials) < MAX_TRIALS:
        study.optimize(
            objective,
            n_trials=1,
            callbacks=[
                lambda active, _: _persist(
                    active,
                    output,
                    target_trials=args.trials,
                    state_path=state_path,
                    root=root,
                    reference_sha256=reference_sha256,
                )
            ],
        )
    _persist(
        study,
        output,
        target_trials=args.trials,
        state_path=state_path,
        root=root,
        reference_sha256=reference_sha256,
    )
    print(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

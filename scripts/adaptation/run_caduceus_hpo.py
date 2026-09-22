#!/usr/bin/env python
"""TRAIN-only Optuna search over gene-grouped folds."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from evovariant_tr.adaptation.data import load_formal_rows, verify_formal_data
from evovariant_tr.adaptation.folds import make_grouped_folds
from evovariant_tr.adaptation.models import load_backbone, PairedClassifier
from evovariant_tr.adaptation.training import TrainConfig, evaluate, train_epoch

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.trials < 8 or args.trials > 12:
        raise SystemExit("protocol requires 8-12 HPO trials")
    import optuna
    import torch
    from pyfaidx import Fasta

    root = Path(args.root).resolve()
    train_rows, _ = load_formal_rows(root)
    folds = make_grouped_folds(train_rows, n_splits=3, seed=args.seed)
    fasta = Fasta(args.reference, as_raw=True, sequence_always_upper=True)

    def objective(trial):
        learning_rate = trial.suggest_float("learning_rate", 5e-6, 5e-5, log=True)
        weight_decay = trial.suggest_float("weight_decay", 1e-4, 5e-2, log=True)
        batch_size = trial.suggest_categorical("batch_size", [1, 2])
        fold_scores = []
        for fold_number, (fit_indices, validation_indices) in enumerate(folds):
            random.seed(args.seed + fold_number)
            torch.manual_seed(args.seed + fold_number)
            tokenizer, backbone, hidden_size = load_backbone(
                "caduceus", device=args.device, cache_dir=args.cache_dir
            )
            model = PairedClassifier.build(backbone, hidden_size)
            model.backbone.requires_grad_(False)
            model.backbone.eval()
            optimizer = torch.optim.AdamW(
                [parameter for parameter in model.parameters() if parameter.requires_grad],
                lr=learning_rate,
                weight_decay=weight_decay,
            )
            config = TrainConfig(
                batch_size=batch_size,
                max_length=args.max_length,
                epochs=args.epochs,
                learning_rate=learning_rate,
                weight_decay=weight_decay,
                amp=args.device.startswith("cuda"),
            )
            fit_rows = [train_rows[index] for index in fit_indices]
            validation_rows = [train_rows[index] for index in validation_indices]
            for _ in range(args.epochs):
                train_epoch(
                    model, tokenizer, fasta, fit_rows, optimizer, config=config, device=args.device
                )
            metrics, _ = evaluate(
                model, tokenizer, fasta, validation_rows, config=config, device=args.device
            )
            if metrics["auroc"] is not None:
                fold_scores.append(float(metrics["auroc"]))
            del model, backbone, tokenizer, optimizer
            if args.device.startswith("cuda"):
                torch.cuda.empty_cache()
            trial.report(sum(fold_scores) / len(fold_scores), fold_number)
            if trial.should_prune():
                raise optuna.TrialPruned()
        return sum(fold_scores) / len(fold_scores)

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=2),
    )
    study.optimize(objective, n_trials=args.trials)
    result = {
        "status": "PASS",
        "selection_scope": "TRAIN_ONLY_STRATIFIED_GROUP_KFOLD",
        "holdout_evaluated": False,
        "protocol_sha256": PROTOCOL_HASH,
        "data": verify_formal_data(root),
        "trials_requested": args.trials,
        "trials_completed": len(study.trials),
        "best_value": study.best_value,
        "best_params": study.best_params,
        "trials": [
            {
                "number": trial.number,
                "state": trial.state.name,
                "value": trial.value,
                "params": trial.params,
            }
            for trial in study.trials
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


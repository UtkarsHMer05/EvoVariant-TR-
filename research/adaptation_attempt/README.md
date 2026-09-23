# EvoVariant-TR adaptation attempt

This directory is an explicit, incomplete appendix to the frozen EvoVariant-TR result. It documents a resource-limited post-hoc Caduceus-Ph adaptation study and preserves the evidence that was actually produced.

Current gate-by-gate state: [STATUS.md](STATUS.md).

## Boundary

- The publication result remains the frozen zero-shot temporal baseline on the 946-row locked cohort.
- Adaptation selection was declared on the 3,199-row TRAIN split with 3-fold `StratifiedGroupKFold`, grouped by gene.
- The 801-row VALIDATION cohort was not opened, and the 946-row temporal cohort was not used for adaptation selection.
- The study did not complete HPO, partial-small training, partial-large training, full-encoder training, selection closure, final refits, calibration, or adaptation holdout evaluation.
- The absence of the old-account Drive source is recorded as recovery context only; it is not treated as a scientific result.

## What was actually trained

The frozen-head Caduceus stage trained only the task head over TRAIN. It is labelled **FROZEN CADUCEUS ENCODER + TRAINED TASK HEAD**, never foundation-model fine-tuning. It completed 3 epochs with losses `1.1767539545572263`, `1.1581548454985837`, and `1.1497443100928366`; the checkpoint and run metadata remain in the prior verified Drive evidence referenced by the adaptation ledger.

A separate one-step `partial_small` feasibility proof demonstrated a real encoder update: blocks 12–15 were trainable, blocks 0–11 were frozen, the encoder delta norm was `0.0013962689554318786`, and the frozen control delta was `0.0`. This proves that the implementation can update the intended encoder parameters. It does **not** prove a completed fine-tuning experiment or a selected adapted model. The recovered evidence record is [caduceus_partial_small_finetune_smoke.json](artifacts/caduceus_partial_small_finetune_smoke.json).

## Reproduction and source

The exact implementation snapshot used for this appendix is under [source_snapshot](source_snapshot/). It came from `research/posthoc-foundation-adaptation` commit `196393636b069dfeaa8dbd43f41b543d0b20d91a` and includes the paired Caduceus model, training loop, folds, checkpointing, HPO runner, and encoder-update proof. Large model weights and Drive checkpoints are intentionally not committed.

The machine-readable evidence index is [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json). The frozen protocol snapshot is [PROTOCOL.md](PROTOCOL.md); its machine-readable twin remains on the preserved adaptation branch because this appendix does not rewrite the baseline protocol.

## Figures

- [encoder update proof](figures/encoder_update_proof.svg) — feasibility evidence only.
- [adaptation workflow](figures/adaptation_workflow.svg) — persisted stage and locked-cohort boundaries.

The PNG/PDF companions are generated locally by `scripts/generate_final_readme_figures.py` when `rsvg-convert` is available.

## Precise status language

Allowed: “encoder-update feasibility proof”, “frozen-head training completed”, “partial foundation-model fine-tuning not completed”, “HPO incomplete”, and “selection open”.

Not allowed: “Caduceus fine-tuning completed”, “full fine-tuning completed”, “adaptation selected”, or any 801/946 adaptation metric.

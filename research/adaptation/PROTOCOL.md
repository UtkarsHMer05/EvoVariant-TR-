# EvoVariant-TR Post-Hoc Foundation-Model Adaptation Protocol

Status: FROZEN
Study ID: POSTHOC-FOUNDATION-ADAPTATION-001
Machine-readable twin: research/adaptation/protocol.yaml
Freeze date: 2026-09-22
Protocol SHA-256: 07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c

## Scope

This is a separate development adaptation study on the existing
research/posthoc-foundation-adaptation branch. It does not rewrite the frozen
zero-shot baseline, main, evovariant-tr-baseline-v1, or the 946-row temporal
locked-test result.

The primary question is whether feasible task-specific adaptation of Caduceus-Ph
improves P/LP-vs-B/LB resolution-direction discrimination relative to a frozen
representation on the 801-row formal gene-held-out validation cohort.

## Populations and leakage boundary

The frozen formal identities are used exactly as committed:

- development: 4,000 rows
- TRAIN: 3,199 rows, 2,645 negative and 554 positive
- VALIDATION: 801 rows, 581 negative and 220 positive
- TRAIN/VALIDATION gene overlap: 0
- adaptation/946 locked-ID overlap: 0

The exact manifest hashes are recorded in protocol.yaml. The 946-row cohort is
historical baseline evidence only. It is not loaded for adaptation fitting,
HPO, early stopping, architecture, representation, context, layer, seed,
threshold, calibration, abstention, ensemble, or any other decision.

## Predeclared study design

Caduceus-Ph is the primary adaptation model with a shared encoder applied to
reference and alternate sequences. The candidate paired representation is
selected using 3-fold StratifiedGroupKFold within TRAIN, grouped by gene.
Forward and reverse-complement logits are averaged when the model supports both
orientations. Class weighting is fold-local BCEWithLogitsLoss with
negative/positive count.

The HPO budget is 8-12 meaningful TRAIN-only trials with pruning and persisted
state. Seeds are fixed at 42, 1337, and 2026; the best seed cannot be selected
using the 801 rows. The final epoch count is derived from TRAIN-CV best epochs,
then the selected configuration is retrained on all 3,199 TRAIN rows.

The 801 rows are a one-shot terminal holdout per predeclared final system.
Primary metric is AUROC; tie-breakers are AUPRC, MCC, lower Brier, then lower
compute/trainable parameter count when scientifically equivalent.

Calibration and abstention are fit from TRAIN OOF predictions only. Ensemble
stacking and weights are fit from TRAIN OOF predictions only. Statistics use
gene-aware paired bootstrap with 2,000 replicates and Holm correction for
multiple primary comparisons.

## Resource contract

Only free Google Colab GPU, local CPU/RAM, Google Drive, public model/reference
downloads, and no-cost packages are allowed. Paid Colab units, GCP billing,
Modal spending, paid GPU providers, full Evo2 fine-tuning, and clinical
deployment are prohibited.

On a Tesla T4, FP16 is the default mixed-precision candidate. OOM may be
addressed with microbatch reduction, accumulation, checkpointing, caching, and
worker reduction; rows, labels, and split identities may not be changed. Full
Caduceus and NT PEFT are conditional and must be marked as resource-deferred
rather than fabricated if they do not fit.

## Frozen baseline anchor

The original historical temporal baseline is bound to main commit
30b515314d5f8c8be7c83c96b1f576fb7225c869 and tag evovariant-tr-baseline-v1.
Its reported AUROC is 0.909225974 on 946 locked rows. Adaptation results on
801 rows are a different stage and are not directly interchangeable with that
historical temporal result.

## Required provenance

Every successful stage must bind its protocol hash, exact data hashes, Git HEAD,
model revision, runtime, checkpoint/artifact hashes, and Drive path where
applicable. State is persisted atomically. Large weights and caches stay out
of Git.

# ADR 0004 — Zero-shot model policy

- Status: ACCEPTED
- Date: 2026-08-18

## Context

The estimand is discrimination of a *frozen* genomic language model's allele-likelihood
scores for later VUS resolution. Any fine-tuning, threshold-fitting on test labels, or
post-hoc model selection would invalidate the temporal generalization claim.

## Decision

Use Evo 2 strictly zero-shot: the official implementation and checkpoint are used
as-is. No fine-tuning on any study labels. No selection of checkpoint, context
length, centering, orientation policy, or score sign based on temporal-test
performance. Model choice is justified by the research question and the official
implementation (Milestone 49 parity spec), not by test AUROC.

## Alternatives

1. Fine-tune on the calibration cohort — rejected for the primary predictor: changes
   the estimand from zero-shot generalization; may be explored only as a separately
   labeled, explicitly-deviated secondary analysis.
2. Choose the best checkpoint after seeing temporal AUROC — rejected: post-hoc
   selection on the test set.
3. Ensemble of models — rejected for primary; comparators (Milestones 71-75) provide
   the controlled comparisons.

## Consequences

- Model identity (checkpoint, package revision, runtime) is recorded in every run
  manifest.
- Official parity must be demonstrated before study scoring (Milestones 56-57).
- Any change to model/config after cohort freeze requires a dated deviation entry.

## Validation

- Registry records model/checkpoint identity per run (Milestone 14).
- Parity spec frozen before temporal scores (Milestone 49 gate).

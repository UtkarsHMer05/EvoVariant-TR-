# ADR 0007 — Disjoint calibration

- Status: ACCEPTED
- Date: 2026-08-18

## Context

Probability calibration requires labeled examples, but using the temporal test
cohort to fit a calibrator or threshold would leak test outcomes into the predictor
and invalidate the primary AUROC. The legacy project fit its threshold on the same
rows it evaluated (documented leakage, Milestone 3).

## Decision

Calibration uses only variants that were already definitive (B/LB or P/LP) at t0 —
a cohort disjoint from the t0-VUS temporal test cohort. Enforce zero normalized-ID
overlap between calibration and temporal test (executable guard). Fit Platt/logistic
calibration with gene-grouped folds; unseen-gene analysis uses zero gene overlap;
isotonic is a sensitivity-only method requiring adequate n. Never use t1 temporal
outcomes to choose calibrator, threshold, checkpoint, context, centering,
comparator, subgroup, score sign, or abstention threshold.

## Alternatives

1. Calibrate on the temporal test cohort — rejected: direct test-set leakage.
2. Calibrate on a random mix including t0-VUS — rejected: any overlap with the test
   cohort leaks.
3. Skip calibration and report raw scores only — retained as the primary
   discrimination analysis; calibration is additive and must not touch the test set.

## Consequences

- Requires building the definitive-at-t0 calibration cohort (Milestone 38) and an
  executable zero-overlap guard with an intentional-failure regression test
  (Milestone 39).
- Calibration cohort may be large; a predeclared sampling plan may be needed before
  scoring (Milestone 76), frozen before temporal metric inspection.

## Validation

- `cohort leakage-check` reports intersection size zero (Milestone 39).
- Regression test injects overlap and must fail (Milestone 39).

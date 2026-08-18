# ADR 0009 — No test-label threshold tuning

- Status: ACCEPTED
- Date: 2026-08-18

## Context

The legacy project derived its decision threshold by ROC-Youden maximization on the
same BRCA1 rows it later evaluated (Milestone 3 audit). Any operating-point choice
informed by temporal-test outcomes inflates apparent performance and defeats the
purpose of a frozen temporal benchmark.

## Decision

No threshold, calibrator, abstention cutoff, or operating point is ever chosen
using temporal-test outcomes. Any threshold used for reporting
(sensitivity/specificity/precision) comes only from the calibration cohort (e.g., a
predeclared rule or the calibration-selected threshold) and is frozen before
temporal metric computation. The primary endpoint is AUROC, which is
threshold-free; threshold-dependent metrics are secondary and reported at the
calibration-selected threshold only.

## Alternatives

1. Pick the threshold maximizing temporal-test metrics — rejected: test-set tuning.
2. Report threshold-free metrics only — partially adopted (AUROC is primary), but
   secondary threshold-dependent metrics are useful and are reported at a
   legitimately-derived threshold.
3. Cross-validate a threshold on the temporal cohort — rejected: still uses test
   outcomes for selection.

## Consequences

- Threshold-dependent secondary metrics carry an explicit note of how the threshold
  was derived (calibration cohort, gene-grouped).
- Risk-coverage/abstention operating points must be predeclared or derived from
  calibration/uncertainty signals, not test labels (Milestone 88).
- Any deviation requires a dated entry in `research/protocol/DEVIATION_LOG.md`.

## Validation

- Calibration fit records zero temporal-test IDs (Milestone 77 gate).
- Analysis code computes temporal metrics only after the threshold is frozen
  (Milestone 80).

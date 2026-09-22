# Raw-delta AUROC sign audit — 2026-09-22

Status: `PASS_DIRECT_SIGN_CONVENTION`. No scientific artifact or metric was changed.

The frozen raw score is `delta_primary = (delta_forward + delta_reverse) / 2`, and each delta is alternate-minus-reference log likelihood. Under the declared `higher_is_more_pathogenic` convention, the direct AUROC is **0.090221150345832**, matching the Phase 14 artifact. The negated-score value **0.909778849654168** is a diagnostic only; it is not substituted into any report or metric.

There is no post-hoc sign flip, `1 - AUROC`, or label reversal. The final `0.909225973789589` AUROC is the output of the frozen Evo2-derived feature pipeline with its TRAIN-fit downstream logistic classifier and TRAIN-fit isotonic calibration, not raw Evo2 alone.

Source hashes are in `raw_delta_auroc_sign_audit_20260922.json`.

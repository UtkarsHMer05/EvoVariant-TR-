# EvoVariant-TR ML Extension Protocol v1.1.0

Status: FROZEN FOR DEVELOPMENT WITH DATED DEVIATIONS `ML-DEV-001` and `ML-DEV-002`.

This is a separate ML-extension protocol. It does not replace or rewrite the original frozen
zero-shot protocol in `research/protocol/`. The historical 1,024-record QA target remains
validation-only historical evidence; the extension's authoritative locked cohort is the
reproducibly regenerated 946-record cohort documented in `DEVIATION_LOG.md`.

## 1. Purpose

Evaluate whether trainable models built from genomic foundation-model signals and
representations improve discrimination of later ClinVar VUS resolution direction while
preserving strict separation from the frozen temporal test cohort.

## 2. Relationship to original protocol

This protocol does not replace `research/protocol/PROTOCOL.md`.

Original:
- evaluates frozen zero-shot Evo2.

Extension:
- permits training, HPO, PEFT/fine-tuning, and ensembles under separate leakage controls.

Results must be labeled by protocol.

## 3. Test estimand

Conditional on eventual resolution and the eligibility criteria, estimate discrimination of
P/LP versus B/LB later resolution for a model whose trainable choices were fixed without
using locked temporal-test labels.

## 4. Cohorts

### Locked temporal test
The ML-extension locked temporal test is the deterministic t0-VUS → t1-resolved cohort generated
from the manifest-verified 2025-01 and 2026-08 ClinVar archives under `ML-DEV-001`:

- total: 946
- B/LB: 536
- P/LP: 410
- gene labels: 946
- authoritative manifest: `research/ml_extension/splits/authoritative_locked_test_manifest.json`
- source/hash manifest: `research/ml_extension/splits/authoritative_cohort_hashes.json`
- independent reference report: `artifacts/reference/grch38_validation_20260921.json`

The historical validation-only target of 1,024 records (614 B/LB, 410 P/LP) is retained in the
machine-readable control plane for comparison and is not injected into this cohort.

### Training/development
Construct from records that do not overlap normalized IDs with temporal test and whose labels
are available at/before the permitted development cutoff. Group by gene when used for
group-aware evaluation.

### Validation
Separate from train. Used for:
- HPO,
- early stopping,
- feature/layer/context selection,
- ensemble member selection,
- ensemble weights,
- calibration,
- abstention thresholds.

## 5. Leakage constraints

Prohibit:
- identical normalized variant across train and test,
- accidental duplicate alleles under alternate representations,
- fitting scaler/imputer/feature normalizer on test,
- fitting calibration on test,
- choosing score direction on test,
- tuning model or thresholds on test,
- using t1 resolution labels as input features,
- using future metadata unavailable at the intended prediction time.

## 6. Model tracks

A. Frozen foundation-model raw scores.
B. Frozen foundation-model embeddings + downstream classifier.
C. PEFT/fine-tuned model where feasible.
D. Multi-model ensemble.
E. Specialized baseline scores.

## 7. Candidate predictors

Required:
- Evo2.

Preferred feasibility candidates:
- Nucleotide Transformer,
- Caduceus,
- GPN-MSA/GPN-Star.

Comparators:
- CADD,
- PhyloP,
- AlphaMissense valid subset.

Any substitution must be documented.

## 8. Model selection

Before locked-test evaluation:
- define primary validation metric,
- define tie-breakers,
- define HPO budget,
- define ensemble selection rule,
- freeze configuration.

## 9. Metrics

Report:
AUROC, AUPRC, MCC, balanced accuracy, accuracy, precision, sensitivity, specificity, F1,
Brier, NLL if probabilistic, ECE, coverage, runtime, cost, and confidence intervals.

## 10. Uncertainty

Use grouped bootstrap where appropriate. Preserve replicate seed and procedure.
Calibrated outputs are study probabilities, not clinical probabilities.

## 11. Robustness

Predeclare:
- context-length matrix,
- orientation policy,
- selected layer set,
- center-shift experiment,
- seed repetitions,
- subgroup analyses.

## 12. Fine-tuning

Fine-tuning is optional and resource-gated. It must:
- use official/supportable tooling,
- log optimizer/scheduler/epochs,
- store train/validation curves,
- use early stopping,
- avoid final test labels.

## 13. Ensemble

Stacking uses OOF development predictions. No in-sample leakage.
Final meta-model config is frozen before locked test.

## 14. Failure and missingness

Missing comparator scores remain missing.
Model installation failures and resource exclusions are reported.
Do not impute "benign" for unavailable evidence.

## 15. Claim policy

Do not describe the system as clinically validated.
Do not claim superiority without uncertainty-aware evidence.
Do not claim causality from association with later ClinVar resolution.

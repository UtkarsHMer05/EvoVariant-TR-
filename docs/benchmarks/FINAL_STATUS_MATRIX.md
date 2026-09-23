# Final Benchmark Status Matrix

# EvoVariant-TR Benchmark Catalog

Canonical registry generated from persisted artifacts by scripts/benchmark_expansion/run_local.py.

| ID | Benchmark | Status | Population | n | New inference? | Web tab | Limitation |
|---|---|---|---|---:|---|---|---|
| B01 | Temporal cohort identity/flow | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B02 | Class distribution | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B03 | Gene separation/leakage | PASS | locked temporal cohort | 4000 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B04 | Locked-ID isolation | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B05 | GRCh38 REF validation | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B06 | Evo2 forward raw evidence | PASS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B07 | Evo2 reverse-complement evidence | PASS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B08 | Evo2 aggregate features | PASS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B09 | Nucleotide Transformer representation | PASS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B10 | Caduceus representation | PASS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B11 | CADD | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Overview | 1109 formal rows remain missing from the authoritative CADD artifact. |
| B12 | PhyloP | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Overview | 3 formal rows remain missing from the authoritative PhyloP artifact. |
| B13 | AlphaMissense eligibility/coverage | NOT_APPLICABLE | locked temporal cohort | 0 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B14 | Foundation-model development comparison | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B15 | Representation/layer comparison | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B16 | Logistic feature-family comparison | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B17 | Tree/boosting feature-family comparison | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B18 | MLP feature-family comparison | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B19 | Classifier×feature AUROC | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B20 | Classifier×feature AUPRC | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B21 | Classifier×feature MCC | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B22 | HPO trial history | PASS | formal development | 4000 | NO | HPO & Training | Existing persisted evidence; no new fine-tuning. |
| B23 | HPO hyperparameters/sensitivity | PASS | formal development | 4000 | NO | HPO & Training | Existing persisted evidence; no new fine-tuning. |
| B24 | Ensemble performance | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B25 | Ensemble diversity/correlation | PASS | formal development | 4000 | NO | Model Disagreement | Existing persisted evidence; no new fine-tuning. |
| B26 | Calibration methods | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B27 | Reliability | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B28 | Brier/ECE/NLL | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B29 | Abstention/selective prediction | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B30 | Risk-coverage | PASS | formal development | 4000 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B31 | Learning curves | PASS | formal development | 4000 | NO | HPO & Training | Existing persisted evidence; no new fine-tuning. |
| B32 | Forward-vs-RC ablation | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B33 | Model-family ablation | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B34 | Classical-comparator ablation | PASS | formal development | 4000 | NO | Model Comparison | Existing persisted evidence; no new fine-tuning. |
| B35 | Locked ROC | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B36 | Locked PR | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B37 | Locked confusion matrix | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B38 | Complete classification metric dashboard | PASS | locked temporal cohort | 946 | NO | Core Baseline | Existing persisted evidence; no new fine-tuning. |
| B39 | Bootstrap confidence | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Existing persisted evidence; no new fine-tuning. |
| B40 | Errors by chromosome | PASS | locked temporal cohort | 946 | NO | Errors & Case Studies | Existing persisted evidence; no new fine-tuning. |
| B41 | Errors by gene | PASS | locked temporal cohort | 946 | NO | Errors & Case Studies | Existing persisted evidence; no new fine-tuning. |
| B42 | Development-vs-final generalization | PASS | formal development | 4000 | NO | Generalization | Existing persisted evidence; no new fine-tuning. |
| B43 | Runtime | PASS | formal development | 4000 | NO | Runtime & Cost | Existing persisted evidence; no new fine-tuning. |
| B44 | Throughput/cache reuse | PASS | formal development | 4000 | NO | Runtime & Cost | Existing persisted evidence; no new fine-tuning. |
| B45 | Compute cost | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Runtime & Cost | Modal provider billing is workspace-level; GPU wall-rate estimate and provider billing delta are reported separately. |
| B46 | ClinVar evidence-quality/review-status | PASS | locked temporal cohort | 946 | NO | Evidence Quality | Evidence quality is an observational association; stars are not biological certainty. |
| B47 | Temporal difficulty/time-to-resolution | PASS | locked temporal cohort | 946 | NO | Temporal Difficulty | Exploratory association; missing and invalid dates are retained. |
| B48 | Leave-one-chromosome-out generalization | PASS | formal development | 4000 | NO | Generalization | Small chromosomes may be marked insufficient support. |
| B49 | Model disagreement/hard cases | PASS | formal development | 4000 | NO | Model Disagreement | Only models with persisted common validation rows are included. |
| B50 | Deterministic case studies | PASS | locked temporal cohort | 946 | NO | Errors & Case Studies | No private or patient data is exposed. |
| B51 | Confidence strata | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Descriptive only; threshold remains frozen. |
| B52 | Model error overlap | PASS | formal development | 4000 | NO | Model Disagreement | Validation-stage only. |
| B53 | Transition-vs-transversion | PASS | locked temporal cohort | 946 | NO | Generalization | Exploratory subgroup analysis. |
| B54 | Substitution-class analysis | PASS | locked temporal cohort | 946 | NO | Generalization | Sparse classes are not over-interpreted. |
| B55 | Comparator coverage/missingness sensitivity | PASS | formal development | 4000 | NO | Model Comparison | Coverage varies by comparator and source release. |
| B56 | Frozen-threshold sensitivity | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | The 0.50 threshold and calibration remain frozen; no post-hoc optimization. |
| B57 | Downstream seed robustness | PASS | formal development | 4000 | NO | Generalization | This is downstream robustness, not foundation-model fine-tuning. |
| B58 | Per-model calibration where predictions exist | PASS | formal development | 4000 | NO | Calibration & Uncertainty | Calibration curves are not refit per model. |
| B59 | Macro/micro/weighted F1 | PASS | locked temporal cohort | 946 | NO | Core Baseline | Threshold remains frozen. |
| B60 | Probability MAE | PASS | locked temporal cohort | 946 | NO | Calibration & Uncertainty | Descriptive score-quality metric. |
| B61 | Independent high-confidence ClinVar benchmark | PASS | external manifest | 200 | YES | External Benchmarks |  |
| B62 | External review-quality subgroups | PASS | external manifest | 200 | YES | External Benchmarks |  |
| B63 | MaveDB functional correlation | DATA_BLOCKED | external manifest | 0 | NO | External Benchmarks | Functional effect is not equivalent to clinical pathogenicity. |
| B64 | Additional public classical comparators | NOT_APPLICABLE | external manifest | 0 | NO | External Benchmarks | GPN was audited but required alignment data and a verified external run were unavailable; no proxy was substituted. |
| B65 | External multi-model agreement | PASS_WITH_LIMITATIONS | external manifest | 200 | YES | External Benchmarks | No external NT/Caduceus prediction asset was available; classical comparator direction is descriptive, not retuned. |
| B66 | External transported calibration | PASS | external manifest | 200 | YES | External Benchmarks | External probabilities are transported, not recalibrated. |
| B67 | External runtime/cost/throughput | PASS | external manifest | 200 | YES | Runtime & Cost | Provider billing is workspace-level and is not treated as a per-request invoice. |
| B68 | Cohort/data-drift comparison | COMPLETED_WITH_LIMITATIONS | locked temporal cohort | 946 | NO | Temporal Difficulty | Drift is descriptive and does not establish causation. |

## External benchmark continuation — 2026-09-24

The frozen ClinVar external manifest remains unchanged at 200 rows (100 benign,
100 pathogenic). Evo2 raw forward/alternate and reverse-complement scores were
persisted before joining the manifest labels. The frozen TRAIN-fit logistic
model, isotonic calibrator, and threshold 0.50 were applied without refitting.

External n=200; AUROC=0.9502; AUPRC=0.958859294515439;
accuracy=0.85; balanced accuracy=0.85;
F1=0.8333333333333334; MCC=0.7144345083117604; Brier=0.11252009005966578;
ECE=0.13962342753163207; NLL=0.6921533824993545. Rate-estimated new Modal
cost=$0.417640; fresh rows=192;
cache-hit rows=8; remote seconds=267.84282031.

B63 remains DATA_BLOCKED because official MaveDB search metadata did not freeze
an exact GRCh38 SNV assay mapping with predeclared score direction and support.
B64 remains NOT_APPLICABLE after the GPN audit because the required alignment
asset and run contract were unavailable; no proxy comparator was substituted.
B11/B12 retain exact missing-row coverage and no imputation or mixed builds.

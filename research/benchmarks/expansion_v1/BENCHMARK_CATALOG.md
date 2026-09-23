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
| B11 | CADD | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
| B12 | PhyloP | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Overview | Existing persisted evidence; no new fine-tuning. |
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
| B45 | Compute cost | COMPLETED_WITH_LIMITATIONS | formal development | 4000 | NO | Runtime & Cost | Existing persisted evidence; no new fine-tuning. |
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
| B61 | Independent high-confidence ClinVar benchmark | COMPUTE_BLOCKED | external manifest | 200 | BLOCKED | External Benchmarks | Selected candidates are manifest-only; no new model scores are claimed. |
| B62 | External review-quality subgroups | COMPUTE_BLOCKED | external manifest | 200 | BLOCKED | External Benchmarks | No external performance without persisted scores. |
| B63 | MaveDB functional correlation | DATA_BLOCKED | external manifest | 0 | NO | External Benchmarks | A functional-effect benchmark requires an assay-specific, predeclared mapping. |
| B64 | Additional public classical comparators | NOT_APPLICABLE | external manifest | 0 | NO | External Benchmarks | No proxy comparator is substituted. |
| B65 | External multi-model agreement | COMPUTE_BLOCKED | external manifest | 200 | BLOCKED | External Benchmarks | Inference blocked before external scoring. |
| B66 | External transported calibration | COMPUTE_BLOCKED | external manifest | 200 | BLOCKED | External Benchmarks | No calibration is refit on the external cohort. |
| B67 | External runtime/cost/throughput | COMPUTE_BLOCKED | external manifest | 200 | BLOCKED | Runtime & Cost | No runtime is fabricated. |
| B68 | Cohort/data-drift comparison | COMPLETED_WITH_LIMITATIONS | locked temporal cohort | 946 | NO | Temporal Difficulty | Drift is descriptive and does not establish causation. |

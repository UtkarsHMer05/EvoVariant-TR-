# EvoVariant-TR Judge Demo

Use the local app and the generated manifest for a 10-15 minute evidence-first walkthrough:

1. Open the normal variant-analysis workflow and confirm the existing form loads.
2. Select Benchmarks in the visible navigation.
3. Start at Overview and scan the contribution registry and B01-B68 status counts.
4. Open Core Baseline for the immutable 946-row result and primary figures.
5. Compare foundation, representation, and classical evidence.
6. Show HPO & Training and explain that downstream HPO is separate from adaptation.
7. Open Calibration & Uncertainty, Evidence Quality, and Temporal Difficulty.
8. Open Generalization for LOCO and seed robustness.
9. Open Model Disagreement for common-row correlations and hard cases.
10. Open External Benchmarks to show the frozen n=200 manifest, AUROC 0.9502,
    raw-prediction hash, review strata, and explicit B63/B64 limitations.
11. Open Errors & Case Studies for deterministic locked examples.
12. Open Runtime & Cost to show the verified Modal credit, cache reuse, fresh
    rows, remote calls, rate estimate, and provider-billing distinction.
13. Open Fine-Tuning Attempt if asked; emphasize primary NO, implementation YES,
    feasibility proof YES if the persisted proof verifies, and complete study NO.
14. Use Downloads and Reproducibility to show notebooks, hashes, protocol, and
    the artifact manifest.

Likely questions:

- Is the 946 result fine-tuned? No. The primary result uses frozen foundation
  representations, a downstream classifier, and frozen calibration.
- Why are some external entries limited? B63 has no defensible exact MaveDB
  GRCh38 SNV assay mapping under the predeclared protocol, and B64 has no
  compatible verified comparator asset; no proxy or unsupported correlation is
  substituted.
- Are review stars biological certainty? No. They are observational evidence-
  quality strata only.
- Can the result be reproduced without paid GPU? The local integrity check,
  generated tables, figures, notebooks, and manifest checks run from persisted
  artifacts. Reusing the completed external evidence is local; any new fresh
  inference must repeat the verified balance, pilot, and safety-stop gates.

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

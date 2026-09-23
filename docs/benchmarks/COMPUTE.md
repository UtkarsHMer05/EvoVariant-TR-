# Compute and safety boundary

At the initial preflight, the existing frozen baseline and cached development
representations were reused. No new foundation-model fine-tuning was started,
and the first balance check failed closed before the continuation was run.
That historical preflight state is superseded by the verified continuation
recorded below.

Hard reserve: $5.00. Safety stop: $5.50. Program soft maximum: $24.00.
The continuation proceeded only after a fresh verified balance check,
external-manifest freeze, deterministic pilot, and safety-stop reconciliation.

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

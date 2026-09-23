# Results

The frozen locked cohort has n=946 variants. The locally
recomputed primary metrics match the registered phase-14 artifact within
1e-9: AUROC=0.909225973790, AUPRC=0.863039100019,
F1=0.818181818182, MCC=0.680960610666. This confirms artifact
integrity; it is not a new locked evaluation.

Evidence-quality, temporal, LOCO, disagreement, case-study, comparator
coverage, threshold-sensitivity, and seed-robustness outputs are written to
research/benchmarks/expansion_v1/local_analysis_results.json.

The external manifest contains 200 deterministic gene-disjoint candidates.
The initial no-spend preflight did not authorize scoring; the subsequent
verified continuation completed the frozen external inference and persisted
the raw scores before label joining. Current runtime and balance evidence are
reported below and in `external_clinvar_runtime.json`.

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

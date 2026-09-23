# EvoVariant-TR Benchmark Expansion v1

## Outcome

The benchmark continuation completed with primary artifact integrity status
**PASS** and external inference status **PASS_WITH_LIMITATIONS**. The frozen
946-row temporal result remains unchanged. The canonical registry contains 68
entries with status counts {"COMPLETED_WITH_LIMITATIONS": 4,
"DATA_BLOCKED": 1, "NOT_APPLICABLE": 2, "PASS": 60,
"PASS_WITH_LIMITATIONS": 1}; no benchmark remains `COMPUTE_BLOCKED`.

## Headline

- Locked cohort: n=946
- AUROC: 0.909225973790
- AUPRC: 0.863039100019
- Positive-class F1: 0.818181818182
- MCC: 0.680960610666
- External manifest: n=200; Evo2 inference completed with AUROC 0.9502 and AUPRC 0.9589
- Modal profile: `utkarshkhajuria59`; verified dashboard credit used: $0.94

## Boundary

Foundation-model fine-tuning was not part of the primary result. The existing
implementation and encoder-update proof remain available, while a complete
fine-tuned benchmark study is **not** claimed. External inference completed
under the verified Modal safety gate; B63 remains `DATA_BLOCKED`, B64 remains
`NOT_APPLICABLE`, and B65 is `PASS_WITH_LIMITATIONS` because NT/Caduceus assets
were unavailable for this cohort.

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
The final bundle contains 34 figure records (14 new external figures), figure
QA is `PASS`, the web manifest exposes 16 downloads, and the external raw,
evaluation, provenance, runtime, MaveDB, and comparator receipts are linked.

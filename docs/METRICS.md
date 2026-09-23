# Final metrics and provenance

The primary result is the immutable Phase 14 Evo2 temporal locked-test evaluation. The 946 rows contain 536 benign/likely-benign and 410 pathogenic/likely-pathogenic variants across 367 genes. The locked manifest, model contract, calibration source, threshold, and output hashes are recorded in `artifacts/phase14/phase14_locked_evo2_20260922.json`.

## Locked result

| metric | value |
|---|---:|
| AUROC | 0.909225974 |
| AUPRC | 0.863039100 |
| Accuracy | 0.843551797 |
| Balanced Accuracy | 0.839866218 |
| Precision | 0.824257426 |
| Recall | 0.812195122 |
| Specificity | 0.867537313 |
| F1 | 0.818181818 |
| MCC | 0.680960611 |
| Brier | 0.114079217 |
| NLL | 0.551757943 |
| ECE | 0.055231060 |
| Probability MAE | 0.206776935 |

Confusion counts are TP `333`, TN `465`, FP `71`, and FN `77`. Probability MAE and the threshold-derived classification rows are calculated by [scripts/generate_final_readme_figures.py](../scripts/generate_final_readme_figures.py) from the frozen joined predictions; no threshold or calibration is refit after the locked test.

## Uncertainty and score semantics

The registered bootstrap AUROC mean is `0.909095980`, with 95% CI `0.889154944–0.929919680`. The raw signed delta primary AUROC is `0.090221150`; the sign is preserved and is not inverted post hoc. The final AUROC is from the declared downstream classifier and TRAIN-fit calibration, not raw Evo2 alone.

Machine-readable outputs:

- [final_metrics_table.json](../research/reports/final_metrics_table.json)
- [final_metrics_table.csv](../research/reports/final_metrics_table.csv)
- [Phase 14 receipt](../artifacts/phase14/phase14_locked_evo2_20260922.json)
- [frozen joined predictions](../research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl)

These metrics are a temporal ClinVar-derived research benchmark. They do not establish clinical validity, prospective performance, treatment benefit, or causal effects.

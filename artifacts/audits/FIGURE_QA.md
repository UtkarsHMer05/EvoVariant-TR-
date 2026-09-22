# Figure QA — EvoVariant-TR Phase 17

Automated status: `PASS_AUTOMATED_STRUCTURAL_QA` across **39 rendered families** (expected 39).
Manual visual contact-sheet review: `PASS_CONTACT_SHEET_REVIEWED_2026-09-22`.

The high-resolution contact sheet was reviewed across all 39 rendered families
after the final `make figures` regeneration. No visible clipping, missing
labels, missing stage markers, missing sample-size markers, axis/caption
truncation, or unsupported trend claim was observed. The two conditional
`NOT_APPLICABLE_WITH_DOCUMENTED_REASON` families remain intentionally excluded.

Outputs: [contact sheet](figure_qa_contact_sheet.png), [SVG contact sheet](figure_qa_contact_sheet.svg), and [HTML gallery](figure_qa_gallery.html).

The audit checks output existence and publication-manifest hashes, SVG XML/viewBox validity, finite coordinates, visible titles/evidence stages/populations/sample-size markers/axis labels/captions, PNG dimensions, one-page PDF metadata, PDF rasterization, finite source values, and monotonic x-order within each plotted series. Ascending and descending source order are both accepted; no trend is inferred beyond the recorded rows.

| Figure | Status | Stage | n | Axes | Trend validity | Issues |
|---|---|---|---:|---|---|---|
| cohort_flow | PASS | PRELIMINARY | 15 | cohort stage / records | PASS | none |
| final_class_distribution | PASS | FINAL | 946 | class / rows | PASS | none |
| final_chromosome_distribution | PASS | FINAL | 946 | chromosome / rows | PASS | none |
| final_gene_top | PASS | FINAL | 946 | gene / rows | PASS | none |
| temporal_transition | PASS | PRELIMINARY | 7 | cohort quantity / records | PASS | none |
| compute_cumulative_rows | PASS | FINAL | 5 | phase / cumulative rows | PASS | none |
| cache_reuse | PASS | FINAL | 10 | phase/work type / rows | PASS | none |
| runtime_by_model | PASS | FINAL | 5 | workload / remote seconds | PASS | none |
| cost_by_phase_model | PASS | FINAL | 5 | workload / estimated USD | PASS | none |
| cumulative_compute_spend | PASS | FINAL | 5 | phase / cumulative estimated USD | PASS | none |
| throughput_comparison | PASS | FINAL | 5 | workload / variants per second | PASS | none |
| foundation_model_performance | PASS | PRELIMINARY | 12 | representation family / VALIDATION AUROC | PASS | none |
| representation_layers | PASS | PRELIMINARY | 6 | layer / VALIDATION AUROC | PASS | none |
| raw_vs_representation | PASS | FINAL | 2 | evidence stage/model / AUROC | PASS | none |
| classifier_auroc_heatmap | PASS | PRELIMINARY | 36 | classifier / AUROC | PASS | none |
| classifier_mcc_heatmap | PASS | PRELIMINARY | 36 | classifier / MCC | PASS | none |
| classifier_brier_heatmap | PASS | PRELIMINARY | 36 | classifier / BRIER | PASS | none |
| combination_ranking | PASS | PRELIMINARY | 12 | combination / VALIDATION AUROC | PASS | none |
| hpo_trial_history | PASS | PRELIMINARY | 48 | trial / VALIDATION objective | PASS | none |
| hpo_hyperparameters | PASS | PRELIMINARY | 25 | feature set / best VALIDATION objective | PASS | none |
| learning_curve_auroc | PASS | PRELIMINARY | 5 | training fraction / VALIDATION AUROC | PASS | none |
| learning_curve_metrics | PASS | PRELIMINARY | 25 | training fraction / metric value | PASS | none |
| ablation_metric_delta | PASS | PRELIMINARY | 30 | ablation / VALIDATION AUROC | PASS | none |
| diversity_matrix | PASS | PRELIMINARY | 3 | left model / error correlation | PASS | none |
| ensemble_comparison | PASS | PRELIMINARY | 3 | ensemble method / VALIDATION AUROC | PASS | none |
| calibration_reliability | PASS | PRELIMINARY | 20 | mean confidence / observed frequency | PASS | none |
| calibration_metric_comparison | PASS | FINAL | 9 | stage/metric / metric value | PASS | none |
| risk_coverage_development | PASS | PRELIMINARY | 20 | coverage / risk | PASS | none |
| final_abstention_semantics | PASS | FINAL | 946 | risk definition / risk | PASS | none |
| final_roc | PASS | FINAL | 946 | false-positive rate / true-positive rate | PASS | none |
| final_pr | PASS | FINAL | 946 | recall / precision | PASS | none |
| bootstrap_interval | PASS | FINAL | 946 | estimate / AUROC | PASS | none |
| final_confusion_matrix | PASS | FINAL | 946 | actual class / predicted class | PASS | none |
| final_outcome_counts | PASS | FINAL | 946 | outcome / rows | PASS | none |
| final_error_chromosome | PASS | FINAL | 946 | chromosome / errors | PASS | none |
| final_gene_errors | PASS | FINAL | 946 | gene / errors | PASS | none |
| final_fp_fn | PASS | FINAL | 946 | error type / rows | PASS | none |
| development_final_generalization | PASS | FINAL | 2 | stage / AUROC | PASS | none |
| project_timeline | PASS | FINAL | 10 | phase / status marker | PASS | none |

Source hashes are preserved per figure in `figure_qa_manifest.json` and in the existing source sidecars. The two inventory entries marked `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` are intentionally excluded from the rendered-family count and are not treated as missing figures.

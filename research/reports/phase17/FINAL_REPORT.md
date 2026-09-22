# EvoVariant-TR Phase 17–19 Publication and Reproducibility Report

## Executive result

The no-spend publication bundle is complete for every applicable figure family supported by the registered Phase 3–14 artifacts. It contains `39` rendered figure families, SVG output for every rendered figure, and PNG/PDF companions when the installed native converter succeeded. The conditional Phase 10 loss and Phase 13 context-length cells are explicitly documented as not applicable; no values were fabricated.

This bundle does not reopen scientific selection, alter the immutable Phase 14 locked evaluation, or authorize additional Modal work. Phase 17 is `PASS_LOCAL_PUBLICATION_BUNDLE`; Phase 15 is complete only as a bounded 64-row batch/resume smoke, Phase 18 passed its clean-room plus representative-smoke scope, and Phase 19 is `INTERNAL_RELEASE_READINESS_PASS` with external release `NOT_REQUESTED`.

## Abstract

The final system is an Evo2-derived feature pipeline with its frozen downstream classifier and calibration: frozen Evo2 forward/reverse/aggregate raw features feed the TRAIN-fit logistic classifier and TRAIN-fit isotonic calibration. It is not raw Evo2 alone. The authoritative current temporal cohort contains 946 locked rows (536 benign/likely-benign and 410 pathogenic/likely-pathogenic) across 367 genes. Phase 14 completed the immutable Evo2 locked evaluation with AUROC `0.909226`, AUPRC `0.863039`, Brier score `0.114079`, ECE `0.055231`, and accuracy `0.843552`. These are evidence-stage-qualified scientific results, not a clinical validation claim.

## Motivation

The study tests whether a frozen foundation-model variant signal can support a temporally defined research benchmark without leaking locked-test labels into model selection. The workbench and publication bundle therefore expose provenance and evidence stage beside every scientific output.

## Dataset and protocol

The protocol fixes the GRCh38 reference, 8192-bp context, forward and reverse-complement scoring, alternate-minus-reference log likelihood, frozen TRAIN/VALIDATION development manifests, and the authoritative 946-row `LOCKED_TEST` cohort. Labels were never sent to Modal; they were joined locally only after raw predictions were hashed.

## Temporal cohort

The temporal cohort source is the hash-registered Phase 3/17 source. The historical 1024-row target identity set is comparison-only, while the current accepted cohort is the 946-row set governed by the frozen manifest audit.

## Evo2 zero-shot model

The primary zero-shot model is Evo2 7B at revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, scored on H100 with the frozen sequence and orientation contract above. Phase 14 is an Evo2-only locked-evaluation subgate; it is not a claim that unrun comparator models were evaluated on the locked cohort.

## Methods and frozen boundary

- Model: Evo2 7B, revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, GRCh38, 8192 bp, forward and reverse-complement scoring, alternate-minus-reference log likelihood, H100.
- Phase 8–13 model selection, HPO, ensemble, calibration, abstention, ablation, and learning-curve evidence used only the frozen TRAIN/VALIDATION development boundary.
- Phase 14 evaluated exactly 946 `LOCKED_TEST` rows after the model, classifier, calibration, threshold, and abstention decisions were frozen. The raw remote artifact was hashed before labels were joined locally.
- The historical 1024-row target remains comparison-only. The accepted formal cohort is 946 rows because the authoritative Phase 3 audit governs the current study; no rows were added to force the historical aggregate.
- The renderer verifies source-file hashes and completed registry output hashes before writing the bundle. Every figure carries its source paths/hashes, evidence stage, population, row count, generator version, and Git commit in its sidecar and SVG metadata.

## Development evidence

Phase 8 evaluated 36 classifier/representation combinations. Phase 9 ran four validation-only trials per study across the declared feature families. Phase 11 recorded model diversity and ensemble comparisons. Phase 12 recorded development calibration and risk-coverage surfaces. Phase 13 recorded completed learning curves and ablations. These surfaces are marked `PRELIMINARY` in the inventory and are not promoted to locked-test evidence.

## Representations, downstream models, HPO, and ensemble

The development registry records Evo2 raw-score and frozen representation tracks, plus the Nucleotide Transformer and Caduceus representation work. The final system uses Evo2-derived features with the frozen downstream logistic classifier and frozen TRAIN-fit isotonic calibration; the raw Evo2 score is an input, not the complete final predictor. Downstream classifiers, validation-only HPO trials, and ensemble comparisons are reported only from their registered TRAIN/VALIDATION artifacts. Fine-tuning/adaptation was formally deferred; no checkpoint or training-loss curve is implied.

## Calibration, abstention, and uncertainty

Platt and isotonic calibration, reliability, Brier/NLL/ECE, and the development risk-coverage surface are reported at the development evidence stage. The final abstention target and signed-delta risk are copied from the immutable Phase 14 artifact; the bundle does not reinterpret that risk as ordinary classification error.

## Ablations, robustness, learning curves, and error analysis

The bundle includes the recorded feature ablations, learning curves, model-diversity/error-correlation surfaces, chromosome and gene error summaries, and final false-positive/false-negative counts. The context-length cell remains explicitly not applicable because the frozen cache contains only 8192-bp features; no missing robustness points are synthesized.

## Development versus final

Development VALIDATION outputs and final LOCKED_TEST outputs are shown with separate evidence-stage labels. Their side-by-side figures are descriptive and do not reopen selection, calibration, threshold, or abstention decisions.

The development-versus-final figures intentionally keep the stages separate. The strongest development Evo2 classifier AUROC is shown alongside the final calibrated locked-test AUROC, but the chart is not a claim that the populations, calibration stage, or selection context are identical.

## Final locked evaluation

The immutable Phase 14 metrics are:

| Metric | Value |
|---|---:|
| AUROC | 0.909225974 |
| AUPRC | 0.863039100 |
| Bootstrap mean | 0.909095980 |
| Bootstrap 95% interval | [0.889154944, 0.929919680] |
| Accuracy | 0.843551797 |
| Brier | 0.114079217 |
| ECE | 0.055231060 |
| NLL | 0.551757943 |
| Raw delta-primary AUROC | 0.090221150 |
| TP / TN / FP / FN | 333 / 465 / 71 / 77 |

## Raw-delta AUROC sign convention

The raw primary score is `delta_primary = (delta_forward + delta_reverse) / 2`, where each delta is alternate-minus-reference log likelihood. The reported raw-delta AUROC `0.090221150` is the direct AUROC of that signed score against the frozen labels. No post-hoc sign flip, `1 - AUROC`, or orientation relabeling is applied. The signed score can therefore have an AUROC below 0.5 under the declared direction; that is a result to report, not a reason to reverse it. The final AUROC above is from the frozen downstream classifier plus TRAIN-fit isotonic calibration and must not be described as raw Evo2 alone.

The frozen abstention target and actual coverage are `0.5` and `0.5`. The artifact risk `0.790697674` is signed-delta direction disagreement under the frozen confidence-rank selection. It is not silently relabeled as ordinary classifier error; the bundle also shows a separate descriptive prediction-error calculation at the same fixed subset.

## Compute, cost, and resource boundary

Phase 6 reused 3,968 verified rows and remotely scored 32 new rows. Phase 7 reused the accepted NT prefix and completed the Caduceus representation track under its separate authorization. Phase 14 remotely scored 946 locked rows in 30 H100 calls with recorded remote runtime `1304.297864` seconds and a direct estimate of `$1.431104601`. Phase 15 completed a 64-row batch/resume smoke with 56 cache-reused rows and 8 fresh remote parity rows; its one fresh remote invocation recorded `57.525624` seconds and a `$0.063118` rate estimate, while the resume added zero remote calls. Paid workers were shut down and the final no-spend Modal snapshot found active containers `[]`.

The compute ledger is reconciled at `artifacts/audits/COMPUTE_LEDGER_AUDIT.md` and distinguishes provider-confirmed workspace snapshots, metered deltas, app-specific measurements, and client/H100 rate estimates. The separately recorded subsequent rate estimates total `$2.989549601`. The earlier user-provided `$7.17` Phase 6 checkpoint basis is retained and is not reset at Phase 15; the later user-provided `$5.94` basis preceded the final 32-row tail. `$2.950450399` is only an indicative subtraction from that later basis, not an exact remaining-credit claim. The provider summary does not expose exact remaining free credits and its workspace meter is non-monotonic after adjustments. The final no-spend provider snapshot records metered `$31.69808745`, billed `$0E-8`, and no active containers. A fresh read-only check at `$artifacts/audits/modal_no_spend_snapshot_20260922.json` independently returned the same no-active-container state.

## Conditional and deferred work

- Phase 10 training loss: `DEFERRED_BY_COMPUTE`; no training run occurred, so no loss curve is emitted.
- Phase 13 context length: `NOT_APPLICABLE_WITH_DOCUMENTED_REASON`; the predeclared 512/1024/2048/4096/8192 cell required additional foundation-model extraction, while current cached features are frozen at 8192 bp. A 64-row, four-additional-context planning sweep is estimated at `$0.387275664` direct H100 cost from the Phase 14 rate, but it is not authorized and must not touch the locked test.
- Phase 15 batch/resume smoke: the exact 64-row development-only smoke passed with 56 cache-reused rows and 8 fresh remote parity rows, exact canonical parity, zero locked rows/labels, and a persisted-shard resume with zero additional remote calls. Full-cohort remote re-inference is not claimed.
- Phase 18 clean room: clean-room software reproducibility, hash-verified scientific artifact reproducibility, and representative remote development smoke passed. Full 4,000/946 remote re-inference was not performed and is not claimed.

## Reproducibility and release gates

The figure inventory is at `research/reports/phase17/FIGURE_INVENTORY.json` and the source sidecars are under `research/figures/final/source/`. Tables are under `research/tables/final/`. The final Phase 14 artifact SHA-256 is `4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499` and the joined-prediction SHA-256 is `77cbbb48032ac7852ff09f93ea448d1e98ca21457843c1feda16f31e8dc530e7`. The generation path is CPU/local only and records no Modal invocation.

Phase 15's bounded parity smoke is complete; the full batch remains outside scope. Phase 19 is `INTERNAL_RELEASE_READINESS_PASS`; external release is `NOT_REQUESTED`. No tag, deployment, publication submission, or external release claim is made by this report.

## Limitations

The historical target identity set is unavailable, so its aggregate is comparison-only. Development results are based on the frozen formal development manifest and are not locked-test evidence. CADD coverage is incomplete and remains explicit. The final cohort is a temporal ClinVar-derived cohort and does not establish clinical validity, prospective performance, or external validity. The provider billing summaries are workspace-level observations with meter adjustments and do not constitute a per-run invoice. Figures preserve these boundaries rather than filling missing cells.

## Conclusion

The reachable EvoVariant-TR evidence bundle is reproducible at the registered-artifact and bounded parity-smoke levels, with Phase 14 preserved as an immutable Evo2-only locked result. Remaining release status is governed by the documented clean-room storage boundary and final release gate; no unrun model, full batch, or full remote re-inference is presented as complete.

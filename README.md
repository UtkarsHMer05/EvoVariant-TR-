# EvoVariant-TR

EvoVariant-TR is a research-only study of whether frozen genomic foundation-model
signals can help rank variants that later resolve from a historical ClinVar VUS
cohort. The completed baseline is a temporal, leakage-resistant study with
GRCh38 validation, forward and reverse-complement inference, downstream
supervised models, calibration, abstention, robustness analysis, a one-shot
locked evaluation, reproducible artifacts, and a research workbench.

> **Research-only boundary:** this is not clinical decision support. It does
> not provide a diagnosis, treatment recommendation, patient-level risk
> estimate, or clinical validity claim.

## The result in one paragraph

The final reported system is an **Evo2-derived feature pipeline with a frozen
downstream classifier and calibration**. Frozen Evo2 forward, reverse-complement,
and aggregate features feed a TRAIN-fit logistic classifier and TRAIN-fit
isotonic calibration. The final result is therefore not “run Evo2 and display a
number,” and it is not a raw-Evo2-only result.

The immutable Phase 14 evaluation contains 946 temporal locked-test variants:
536 benign/likely-benign (B/LB) and 410 pathogenic/likely-pathogenic (P/LP)
variants across 367 genes. The final calibrated locked-test result is AUROC
<code>0.909225974</code>, AUPRC <code>0.863039100</code>, and accuracy
<code>0.843551797</code>. Model selection, threshold, calibration, and
abstention decisions were closed before the locked evaluation:
<code>selection_closed = true</code>.

## Architecture

The complete contribution is the study and engineering system around existing
foundation models:

~~~text
Historical ClinVar VUS cohort
        ↓
frozen temporal protocol
        ↓
GRCh38 validation
        ↓
Evo2 + NT + Caduceus
        ↓
forward / reverse-complement evidence
        ↓
downstream ML
        ↓
HPO
        ↓
ensemble analysis
        ↓
calibration
        ↓
abstention
        ↓
ablations / learning curves
        ↓
frozen selection
        ↓
one-shot 946-variant locked test
        ↓
statistics / figures / research UI
~~~

Evo2 was not created by this project. Nucleotide Transformer was not created by
this project. Caduceus was not created by this project.

Our contribution is the temporal study design, genomic inference pipeline,
representation comparison, downstream training, calibration, uncertainty,
robustness, locked evaluation, reproducibility, visualization, batch system,
and research workbench.

## Models evaluated

### Frozen foundation models

- **Evo2 7B**, revision
  <code>4b509ec2a22d6de472659f908bcb0714265ad3a7</code>, GRCh38, 8,192-bp
  context, H100 execution, forward and reverse-complement scoring.
- **Nucleotide Transformer v2**, evaluated as a development representation
  track under its separately registered artifacts.
- **Caduceus**, evaluated as a development representation track under its
  separately registered artifacts.
- **CADD and PhyloP**, used only within their documented public CPU-comparator
  scope where coverage was available.

### Trainable downstream models

The foundation models remained frozen in the baseline. Downstream development
comparisons included Logistic Regression, a tree/boosting model, and an MLP
across 36 model-by-feature experiments. The study also recorded 12
validation-only HPO studies, ensemble and diversity analysis, calibration,
abstention, ablations, and learning curves.

The original baseline study performed **no foundation-model fine-tuning**.
Fine-tuning/adaptation is deferred to the independent
<code>research/posthoc-foundation-adaptation</code> study branch. The immutable
946-row locked cohort must not be reused for adaptation model selection.

## Formal study design

| Split or cohort | Rows | Purpose |
|---|---:|---|
| Formal development set | 4,000 | Pre-locked development study |
| TRAIN | 3,199 | Downstream fitting and TRAIN-side calibration fits |
| VALIDATION | 801 | Model comparison, HPO, calibration/abstention selection |
| Locked temporal test | 946 | One-shot final evaluation after selection closed |
| Locked genes | 367 | Temporal locked cohort coverage |
| B/LB | 536 | Negative class |
| P/LP | 410 | Positive class |

TRAIN/VALIDATION were used for development. The 946-row temporal cohort was
evaluated once after <code>selection_closed = true</code>. Locked labels were
joined locally only after the raw prediction artifact was hashed; no labels
were sent to Modal.

The historical 1,024-row identity target is retained as a comparison-only
historical boundary. The accepted formal temporal test is 946 rows because the
authoritative reproducible cohort and locked manifest govern the current study.
Rows were not added to force the historical aggregate to match 1,024.

## What We Actually Contributed

1. A temporal ClinVar VUS cohort and reproducible historical protocol.
2. A leakage-resistant gene-separated development design.
3. GRCh38 sequence and reference validation.
4. Forward plus reverse-complement Evo2 scoring.
5. PAR hard-mask handling with documented provenance.
6. Nucleotide Transformer and Caduceus representation extraction.
7. Thirty-six downstream supervised comparisons.
8. Validation-only hyperparameter optimization.
9. Ensemble and diversity analysis.
10. Probability calibration.
11. Abstention and selective prediction.
12. Ablation and learning-curve analysis.
13. One-shot locked temporal evaluation.
14. Confidence intervals, error analysis, and subgroup analysis.
15. Cost, runtime, caching, and resumable batch engineering.
16. Batch CSV/VCF support.
17. A reproducible experiment registry.
18. A research workbench exposing registered evidence.
19. A 39-family scientific visualization bundle.
20. Clean-room reproducibility and artifact hashing.

## Immutable locked-test result

The final locked evaluation is the frozen Phase 14 artifact, not a new
calculation performed by this README. Its complete headline metrics are:

| Metric | Value | Plain-language meaning |
|---|---:|---|
| AUROC | 0.909225974 | How well scores rank P/LP above B/LB across thresholds |
| AUPRC | 0.863039100 | Precision-recall tradeoff across thresholds |
| Accuracy | 0.843551797 | Fraction of all locked rows classified correctly |
| Balanced accuracy | 0.839866218 | Average of positive-class recall and negative-class specificity |
| Precision | 0.824257426 | Fraction of predicted P/LP rows that are P/LP |
| Recall | 0.812195122 | Fraction of actual P/LP rows recovered |
| Specificity | 0.867537313 | Fraction of actual B/LB rows rejected as P/LP |
| F1 | 0.818181818 | Harmonic mean of precision and recall |
| MCC | 0.680960611 | Balanced correlation-style measure using all four outcome counts |
| Brier score | 0.114079217 | Mean squared error of predicted probabilities |
| ECE | 0.055231060 | Average gap between confidence and observed frequency |
| NLL | 0.551757943 | Probabilistic log-loss; lower is better |

The recorded confusion counts are:

~~~text
TP = 333
TN = 465
FP = 71
FN = 77
~~~

The bootstrap AUROC mean is <code>0.909095980</code> with a 95% interval of
<code>0.889154944 – 0.929919680</code>.

The requested metric definitions are:

~~~text
Accuracy = (TP + TN) / (TP + TN + FP + FN)

Precision = TP / (TP + FP)

Recall = TP / (TP + FN)

Specificity = TN / (TN + FP)

F1 = 2 * Precision * Recall / (Precision + Recall)

Balanced Accuracy = (Recall + Specificity) / 2
~~~

MAE is not the primary metric because the endpoint is binary classification,
not continuous regression.

## Score semantics and raw-delta sign

For each strand orientation, the raw score is alternate-minus-reference log
likelihood:

~~~text
delta_forward = alternate log likelihood - reference log likelihood
delta_reverse = alternate log likelihood - reference log likelihood
delta_primary = (delta_forward + delta_reverse) / 2
~~~

The direct raw-delta AUROC is <code>0.090221150</code> because the signed raw
score orientation is opposite the P/LP-positive convention. That value is
reported directly. It is not replaced with <code>1 - AUROC</code>, and no
post-hoc score flip, label reversal, or orientation relabeling was applied.

The final approximately <code>0.909</code> AUROC comes from the frozen
downstream Evo2-derived feature pipeline, logistic classifier, and isotonic
calibration. It is not a post-hoc correction of the raw Evo2 score.

## Headline figures

These images are selected from the hash-verified final figure bundle. Each
figure has a source sidecar and is covered by the 39-family visual QA audit.
Development figures are explicitly marked as development evidence; they are not
locked-test results.

<table>
<tr>
<td><img src="research/figures/final/cohort_flow.png" alt="Temporal cohort flow" width="260"><br><sub>Temporal cohort flow</sub></td>
<td><img src="research/figures/final/final_class_distribution.png" alt="Locked class distribution" width="260"><br><sub>Locked class distribution</sub></td>
<td><img src="research/figures/final/foundation_model_performance.png" alt="Foundation model development comparison" width="260"><br><sub>Foundation-model development comparison</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/representation_layers.png" alt="Representation layer comparison" width="260"><br><sub>Representation/layer comparison</sub></td>
<td><img src="research/figures/final/classifier_auroc_heatmap.png" alt="Classifier AUROC comparison" width="260"><br><sub>Classifier comparison</sub></td>
<td><img src="research/figures/final/hpo_trial_history.png" alt="HPO trial history" width="260"><br><sub>Validation-only HPO trial history</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/learning_curve_auroc.png" alt="Learning curve" width="260"><br><sub>Learning curve</sub></td>
<td><img src="research/figures/final/final_roc.png" alt="Final ROC curve" width="260"><br><sub>Final ROC</sub></td>
<td><img src="research/figures/final/final_pr.png" alt="Final precision recall curve" width="260"><br><sub>Final precision-recall curve</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/final_confusion_matrix.png" alt="Final confusion matrix" width="260"><br><sub>Final confusion matrix</sub></td>
<td><img src="research/figures/final/calibration_reliability.png" alt="Calibration reliability" width="260"><br><sub>Calibration and reliability</sub></td>
<td><img src="research/figures/final/final_abstention_semantics.png" alt="Final abstention semantics" width="260"><br><sub>Abstention semantics</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/ensemble_comparison.png" alt="Ensemble comparison" width="260"><br><sub>Ensemble comparison</sub></td>
<td><img src="research/figures/final/diversity_matrix.png" alt="Model diversity matrix" width="260"><br><sub>Model disagreement/correlation</sub></td>
<td><img src="research/figures/final/ablation_metric_delta.png" alt="Ablation results" width="260"><br><sub>Ablation results</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/final_error_chromosome.png" alt="Error distribution by chromosome" width="260"><br><sub>Subgroup/error distribution</sub></td>
<td><img src="research/figures/final/runtime_by_model.png" alt="Runtime comparison" width="260"><br><sub>Runtime comparison</sub></td>
<td><img src="research/figures/final/cost_by_phase_model.png" alt="Compute cost comparison" width="260"><br><sub>Compute-cost comparison</sub></td>
</tr>
<tr>
<td><img src="research/figures/final/development_final_generalization.png" alt="Development versus final generalization" width="260"><br><sub>Development versus final</sub></td>
<td><img src="research/figures/final/project_timeline.png" alt="Project evidence timeline" width="260"><br><sub>Project/evidence timeline</sub></td>
<td><img src="research/figures/final/final_fp_fn.png" alt="False positive and false negative counts" width="260"><br><sub>False-positive/false-negative counts</sub></td>
</tr>
</table>

The final bundle includes the other verified families, including class and
chromosome distributions, gene summaries, cache reuse, throughput, raw versus
representation comparison, classifier MCC/Brier heatmaps, combination
ranking, HPO hyperparameters, learning-curve metrics, calibration metric
comparison, development risk coverage, bootstrap interval, outcome counts,
gene errors, and final error summaries:

- [Full final figure directory](research/figures/final/)
- [Full figure QA gallery](artifacts/audits/figure_qa_gallery.html)
- [39-family contact sheet](artifacts/audits/figure_qa_contact_sheet.png)
- [Figure QA report](artifacts/audits/FIGURE_QA.md)
- [Publication report](research/reports/phase17/FINAL_REPORT.md)
- [Publication manifest](research/reports/phase17/publication_manifest.json)

No fine-tuning loss curve, context-length curve, or unsupported intermediate
temporal trend is shown. Fine-tuning loss is deferred, the context-length
cell is not applicable to the frozen 8,192-bp cache, and unsupported trends
remain absent.

## Where is the code?

| Contribution area | Main code |
|---|---|
| Evo2 inference | [scripts/phase6_development_evo2.py](scripts/phase6_development_evo2.py) |
| Foundation representations | [scripts/formal_budgeted_representations.py](scripts/formal_budgeted_representations.py) |
| Feature materialization | [scripts/materialize_formal_features.py](scripts/materialize_formal_features.py), [scripts/materialize_formal_evo2_features.py](scripts/materialize_formal_evo2_features.py), [scripts/phase6_evo2_to_features.py](scripts/phase6_evo2_to_features.py) |
| ML analysis | [src/evovariant_tr/analysis_pipeline.py](src/evovariant_tr/analysis_pipeline.py) |
| Ensembles | [src/evovariant_tr/ensemble.py](src/evovariant_tr/ensemble.py) |
| Calibration | [src/evovariant_tr/prediction_calibration.py](src/evovariant_tr/prediction_calibration.py) |
| Abstention | [src/evovariant_tr/abstention.py](src/evovariant_tr/abstention.py) |
| Final locked evaluation | [src/evovariant_tr/final_evaluation.py](src/evovariant_tr/final_evaluation.py), [scripts/evaluate_locked.py](scripts/evaluate_locked.py) |
| Batch/resume | [src/evovariant_tr/batch_pipeline.py](src/evovariant_tr/batch_pipeline.py) |
| Figures | [src/evovariant_tr/figure_artifacts.py](src/evovariant_tr/figure_artifacts.py) |
| Research workbench | [apps/web/](apps/web/) |

The experiment registry is under
[experiments/registry/](experiments/registry/). The current publication
bundle is generated from registered, hash-verified artifacts; it is not a
collection of hand-entered metrics.

## Reproducibility and validation

The free local validation surface does not require new foundation-model
inference:

~~~bash
make bootstrap
make validate
make registry-verify
make protocol-verify
make ml-protocol-verify
make test-scientific
make web-check
make web-e2e
make figures
git diff --check
~~~

The final baseline validation requires all applicable gates to pass. It checks
secrets, formatting, strict typing, unit/integration/scientific tests, schema
and registry integrity, protocol hashes, frontend/browser behavior, figure
generation, and whitespace integrity.

The final publication bundle contains 41 inventory entries, 39 rendered figure
families, 39 source sidecars, and 12 tables. The visual audit reports
<code>39/39</code> structural PASS, zero failed families, and a manual
contact-sheet review with no clipping, missing labels, missing stage markers,
missing sample sizes, axis/caption truncation, or unsupported trend claims.

## Compute and resumability

The formal Evo2 result used 4,000 development rows and the separate Phase 14
locked evaluation used 946 rows. The Phase 15 remote smoke was deliberately
bounded to 64 development rows: 56 cache-reused rows and 8 fresh remote parity
rows. Its persisted-shard resume performed zero additional remote calls.

The compute ledger separates provider-confirmed workspace snapshots, metered
deltas, application measurements, and rate estimates. The earlier user-provided
<code>$7.17</code> Phase 6 basis is not reset at Phase 15. The fresh final
read-only provider snapshot records metered workspace cost
<code>$31.69808745</code>, billed cost <code>$0.00</code>, and no active
containers; the provider does not expose an exact remaining free-credit
balance.

No new paid work is implied by the README, and no full 4,000/946 remote
re-inference is claimed for Phase 18.

## Current phase and release status

- Phase 0–5: protocol, data, reference, scoring, and model-registry gates
  completed under their documented scopes.
- Phase 6: formal 4,000-row Evo2 subtrack complete; the broader multi-model
  benchmark remains stage-qualified and separate from the locked subgate.
- Phase 7: development representation tracks for Nucleotide Transformer and
  Caduceus complete under their separate authorization.
- Phases 8–13: downstream models, HPO, ensemble, calibration, abstention,
  ablations, learning curves, and error analysis completed on the development
  boundary.
- Phase 10 fine-tuning/adaptation: <code>DEFERRED_BY_COMPUTE</code>; no
  checkpoint or training-loss curve exists in the baseline.
- Phase 14: <code>PASS / FORMAL EVO2 LOCKED SUBGATE</code>; 946 immutable
  locked rows.
- Phase 15: <code>PASS / 64-ROW BATCH-RESUME SMOKE</code>.
- Phase 16: registered-output research workbench connected to verified evidence.
- Phase 17: <code>PASS_LOCAL_PUBLICATION_BUNDLE</code>.
- Phase 18: clean-room software/artifact reproducibility plus representative
  remote smoke passed; full 4,000/946 remote re-inference was not performed or
  claimed.
- Phase 19: <code>INTERNAL_RELEASE_READINESS_PASS</code>; external release is
  <code>NOT_REQUESTED</code>.

## Post-Hoc Foundation-Model Adaptation Study

A separate follow-up study is running on branch
[`research/posthoc-foundation-adaptation`](research/adaptation/PROTOCOL.md).
It leaves the frozen baseline, `main`, the baseline tag, and the 946-row
temporal result unchanged. The adaptation population is 3,199 TRAIN rows and
an 801-row gene-held-out terminal holdout; the 946-row cohort is not used for
adaptation training or selection.

The frozen protocol asks whether adapting Caduceus-Ph, with a pinned
Nucleotide Transformer v2 500M secondary track where free-T4 resources allow,
improves P/LP-vs-B/LB resolution-direction discrimination against frozen
representations on that defined research cohort. Caduceus uses shared
reference/alternate sequence encoding, fold-local weighted BCE loss, and
forward/reverse-complement logit averaging. The 8,192 bp frozen-head baseline
completed three TRAIN-only epochs in the existing free Tesla T4 session. Its
loss declined from `1.17675` to `1.14974`; this is optimization evidence, not a
discrimination result. Grouped TRAIN-only HPO is running in that session. The
one-shot holdout remains closed and there is no adaptation improvement claim.

Implementation, protocol, progress, and inspectable walkthrough:

- Training and HPO: [`train_caduceus.py`](scripts/adaptation/train_caduceus.py),
  [`run_caduceus_hpo.py`](scripts/adaptation/run_caduceus_hpo.py)
- Frozen design and state: [`PROTOCOL.md`](research/adaptation/PROTOCOL.md),
  [`STATE.md`](research/adaptation/STATE.md),
  [`EXPERIMENT_LEDGER.md`](research/adaptation/EXPERIMENT_LEDGER.md)
- Notebooks: [autonomous runner](notebooks/EvoVariant_TR_Adaptation_Autonomous.ipynb),
  [judge demo](notebooks/EvoVariant_TR_Adaptation_Judge_Demo.ipynb)
- Walkthrough: [`docs/JUDGE_DEMO.md`](docs/JUDGE_DEMO.md)

The 4,000 development sample is class-stratified, so prevalence-sensitive
metrics describe this study distribution. Adaptation holdout values must not
be compared as though they were the historical 946-row temporal test.

## Limitations and responsible use

This is a historical ClinVar-resolution benchmark, not a prospective clinical
study. ClinVar review status is a review proxy, not biological certainty. The
study does not estimate diagnosis, treatment response, patient management,
causal pathogenicity, or when every VUS will be reclassified.

The baseline preserves the following boundaries:

- no foundation-model fine-tuning;
- fine-tuning/adaptation is deferred to the independent follow-up branch;
- context-length sweep deferred/not applicable to the frozen 8,192-bp cache;
- full second 4,000/946 remote re-inference not performed or claimed;
- historical 1,024-row cohort retained for comparison only;
- accepted formal temporal test is 946 rows;
- locked-test labels were never sent to Modal;
- final metrics, thresholds, calibration, model selection, and score direction
  are frozen.

## Important artifacts

- [Frozen Phase 14 artifact](artifacts/phase14/phase14_locked_evo2_20260922.json)
- [Phase 14 approval](artifacts/approvals/phase14_locked_evo2_20260922.json)
- [Phase 15 parity/resume validation](artifacts/phase15/phase15_parity_smoke_validation_20260922.json)
- [Phase 18 clean-room status](research/runs/phase18_clean_room_status.json)
- [Phase 19 internal release status](research/runs/phase19_release_status.json)
- [Compute ledger audit](artifacts/audits/COMPUTE_LEDGER_AUDIT.md)
- [Raw-delta sign audit](artifacts/audits/RAW_DELTA_AUROC_SIGN_AUDIT.md)
- [Frozen-hash audit](artifacts/audits/FROZEN_HASH_AUDIT.md)
- [Pre-existing dirty core-diff classification](artifacts/audits/PREEXISTING_DIRTY_CORE_DIFF_AUDIT.md)
- [Clean-room and ponytail audit reports](artifacts/audits/)
- [Current project state](docs/agent/PROJECT_STATE.md)
- [Phase ledger](docs/agent/PHASE_LEDGER.md)
- [Decision log](docs/agent/DECISIONS.md)

## References

- [CODEX_MASTER_PROMPT.md](CODEX_MASTER_PROMPT.md)
- [Original frozen protocol](research/protocol/PROTOCOL.md)
- [ML-extension protocol](research/ml_extension/PROTOCOL.md)
- [Command reference](COMMAND_REFERENCE.md)
- [Testing and validation](docs/agent/TESTING_AND_VALIDATION.md)
- [Modal compute policy](docs/agent/MODAL_COMPUTE_POLICY.md)
- [Evo2](https://github.com/ArcInstitute/evo2)
- [Nucleotide Transformer](https://github.com/instadeepai/nucleotide-transformer)
- [Caduceus](https://github.com/kuleshov-group/caduceus)
- [NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)
- [UCSC Genome Browser API](https://api.genome.ucsc.edu)

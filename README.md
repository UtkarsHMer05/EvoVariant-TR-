# EvoVariant-TR

> **TL;DR:** The shipped result is a frozen, leakage-resistant Evo2 temporal
> benchmark with a one-shot 946-row locked evaluation. The primary result is
> AUROC `0.909225974`; the foundation models were not fine-tuned for that
> result. A separate Caduceus adaptation attempt is preserved below as an
> incomplete, auditable appendix with a real encoder-update feasibility proof,
> not as a completed adapted model.

**Judge entry points:** [baseline metrics](docs/METRICS.md) · [HPO record](docs/HYPERPARAMETER_TUNING.md) · [baseline judge notebook](notebooks/EvoVariant_TR_Baseline_Judge_Demo.ipynb) · [fine-tuning-attempt notebook](notebooks/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb) · [complete figure gallery](artifacts/audits/final_polish_gallery.html)

**Benchmark expansion:** open the [Benchmark Hub](/benchmarks) or follow the
[judge demo](docs/JUDGE_DEMO.md). The generated [B01-B68 catalog](docs/benchmarks/BENCHMARK_CATALOG.md)
covers frozen baseline, model comparison, calibration, evidence quality,
temporal difficulty, LOCO, disagreement, external validation, runtime,
fine-tuning feasibility, and reproducibility. The completed continuation
preserves the immutable 946-row result, generated figures, compact notebooks,
raw external predictions, and an artifact-hash manifest. B63/B64 remain
explicitly bounded where their mapping or comparator contracts are not met.

EvoVariant-TR is a research-only study of whether frozen genomic foundation-model
signals can help rank variants that later resolve from a historical ClinVar VUS
cohort. The completed baseline is a temporal, leakage-resistant study with
GRCh38 validation, forward and reverse-complement inference, downstream
supervised models, calibration, abstention, robustness analysis, a one-shot
locked evaluation, reproducible artifacts, and a research workbench.

> **Research-only boundary:** this is not clinical decision support. It does
> not provide a diagnosis, treatment recommendation, patient-level risk
> estimate, or clinical validity claim.

## Contributions at a glance

The contribution is the **benchmark, the pipeline, and the audit trail around
existing foundation models** — not a new foundation model. Every figure below is
generated from a registered artifact in this repository; none is hand-entered.

| Contribution | Measured evidence |
|---|---:|
| Registered benchmark entries | **68** (`B01`–`B68`), **65** completed or completed-with-limitations |
| Rendered figure families | **42** final families (PNG + PDF + SVG) plus **2** adaptation figures |
| Publication bundle | **41** inventory entries, **39** rendered Phase 17 families, **12** tables |
| Registered experiment runs | **13**, all `COMPLETED` |
| One-shot locked temporal evaluation | **946** rows, AUROC **0.909226** |
| Independent external validation | **200** rows, AUROC **0.950200** |
| Downstream model × feature comparisons | **36** (logistic, tree/boosting, MLP) |
| Validation-only HPO feature families | **12** |
| Automated tests | **722** passing (unit, contract, integration, scientific, browser E2E) |
| Core-package coverage gate | **95.04%** (floor 95%) |
| Typing and lint | `mypy --strict` clean, `ruff` clean on `src`/`tests`/`scripts` |
| Browser end-to-end checks | **8** Playwright scenarios |
| Code footprint | **58** Python modules / **15,643** LOC core, **23,577** LOC scripts, **7,616** LOC TypeScript |
| New paid compute for the benchmark expansion | **$0.00** |

**What this is not.** It is not "call a model and print a number." The headline
result comes from a frozen downstream feature pipeline with TRAIN-fit logistic
regression and TRAIN-fit isotonic calibration; the raw Evo2 delta is reported
separately and honestly (raw-delta AUROC `0.090221`), and no threshold,
calibration, or model-selection decision was reopened after the locked cohort
was scored.

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

The list below is the qualitative contribution; the
[scoreboard](#benchmark-scoreboard) above gives the measured form of each item.
Every entry maps to code and to a registered artifact rather than to a claim.

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
19. A 42-family scientific visualization bundle (39 Phase 17 families plus 3
    final source-derived dashboards), each with a provenance sidecar.
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

Probability MAE is reported as a secondary descriptive probability-quality
metric in the generated final table. It is not the primary metric because the
endpoint is binary classification, not continuous regression.

## Benchmark scoreboard

Both headline evaluations are read from registered artifacts, not typed into
this README by hand.

| Evaluation | n | AUROC | AUPRC | Accuracy | Precision | Recall | Specificity | F1 | MCC | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Locked temporal test (one-shot, frozen) | 946 | 0.909226 | 0.863039 | 0.843552 | 0.824257 | 0.812195 | 0.867537 | 0.818182 | 0.680961 | 0.114079 | 0.055231 |
| Independent external cohort (transported) | 200 | 0.950200 | 0.958859 | 0.850000 | 0.937500 | 0.750000 | 0.950000 | 0.833333 | 0.714435 | 0.112520 | 0.139623 |

### Classical comparator coverage

Exact coverage with every missing row retained — no imputation, no mixed genome
builds, and no proxy substitution. Corrected 2026-09-24: the benchmark loader
did not recognise the PhyloP `sitewise_score` field, so PhyloP was previously
reported as `0/4,000 DATA_BLOCKED`; the regenerated evidence below is the
corrected state.

| Comparator | Cohort | Available | Total | Coverage | Status |
|---|---|---:|---:|---:|---|
| CADD v1.7 | formal development | 2,891 | 4,000 | 72.28% | PASS, 1,109 rows retained as missing |
| CADD v1.7 | locked temporal | 918 | 946 | 97.04% | PASS |
| PhyloP 100-way | formal development | 3,997 | 4,000 | 99.93% | PASS, 3 rows retained as missing |
| PhyloP 100-way | locked temporal | 946 | 946 | 100.00% | PASS |

### Benchmark registry status

| Status | Entries | Meaning |
|---|---:|---|
| `PASS` | 60 | Executed on registered evidence with no open limitation |
| `PASS_WITH_LIMITATIONS` | 1 | Executed with a documented scope limitation |
| `COMPLETED_WITH_LIMITATIONS` | 4 | Completed; specific rows or contracts remain unavailable |
| `NOT_APPLICABLE` | 2 | Audited and correctly excluded; no proxy substituted |
| `DATA_BLOCKED` | 1 | The required external assay mapping is not defensible |

The two deliberately bounded entries are `B63` (MaveDB functional correlation,
`DATA_BLOCKED`: no exact GRCh38 SNV assay mapping with a predeclared score
direction could be frozen) and `B64` (additional public classical comparators,
`NOT_APPLICABLE`: GPN was audited but its required alignment asset and run
contract were unavailable). The registry, not this README, is the source of
truth: [B01–B68 catalog](docs/benchmarks/BENCHMARK_CATALOG.md) ·
[status matrix](docs/benchmarks/FINAL_STATUS_MATRIX.md) ·
[machine-readable registry](artifacts/benchmarks/benchmark_registry.json) ·
[registered runs](experiments/registry/runs/).

### Benchmark gallery

<table>
<tr>
<td><img src="apps/web/public/benchmarks/figures/benchmark_status_matrix.png" alt="B01-B68 benchmark status matrix" width="260"><br><sub>B01–B68 status matrix (68 entries)</sub></td>
<td><img src="apps/web/public/benchmarks/figures/benchmark_contact_sheet.png" alt="Benchmark contact sheet" width="260"><br><sub>Benchmark contact sheet</sub></td>
<td><img src="apps/web/public/benchmarks/figures/frozen_roc.png" alt="Locked temporal ROC" width="260"><br><sub>Locked temporal ROC (n=946)</sub></td>
</tr>
<tr>
<td><img src="apps/web/public/benchmarks/figures/external_roc.png" alt="External validation ROC" width="260"><br><sub>External validation ROC (n=200)</sub></td>
<td><img src="apps/web/public/benchmarks/figures/classical_comparator_coverage.png" alt="Classical comparator coverage" width="260"><br><sub>Comparator coverage (corrected)</sub></td>
<td><img src="apps/web/public/benchmarks/figures/locked_versus_external_calibration_and_discrimination.png" alt="Locked versus external calibration" width="260"><br><sub>Locked vs external calibration</sub></td>
</tr>
<tr>
<td><img src="apps/web/public/benchmarks/figures/external_runtime_and_cache_economics.png" alt="External runtime and cache economics" width="260"><br><sub>Runtime and cache economics</sub></td>
<td><img src="apps/web/public/benchmarks/figures/evidence_quality_performance.png" alt="Evidence-quality strata performance" width="260"><br><sub>Evidence-quality strata</sub></td>
<td><img src="apps/web/public/benchmarks/figures/model_disagreement_categories.png" alt="Model disagreement categories" width="260"><br><sub>Model disagreement</sub></td>
</tr>
</table>

### Benchmark coverage by family

25 families cover the 68 entries (`B01`–`B68`):

| Family | Entries | Family | Entries |
|---|---:|---|---:|
| External validation | 8 | Representation | 2 |
| Downstream ML | 6 | Model comparison | 2 |
| Core baseline | 5 | HPO | 2 |
| Generalization | 5 | Ensemble | 2 |
| Locked baseline | 4 | Uncertainty | 2 |
| Calibration & uncertainty | 4 | Error analysis | 2 |
| Foundation evidence | 3 | Model disagreement | 2 |
| Classical comparators | 3 | Training | 1 |
| Calibration | 3 | Statistics | 1 |
| Ablation | 3 | Evidence quality | 1 |
| Runtime & cost | 3 | Temporal difficulty | 1 |
| Model Comparison (`B55`) | 1 | Errors & case studies | 1 |
| Core Baseline (`B59`) | 1 | | |

## What was actually trained

The baseline trained downstream classifiers and calibration on the declared
development boundary while keeping Evo2, Nucleotide Transformer, and Caduceus
foundation encoders frozen. The final locked result is therefore **HEAD-ONLY
DOWNSTREAM TRAINING**, not foundation-model fine-tuning.

The independent Caduceus follow-up has a separate evidence surface:

| item | measured state |
|---|---|
| frozen Caduceus encoder + trained task head | completed on TRAIN only |
| partial-small encoder-update proof | PASS; blocks 12–15 trainable, encoder delta `0.0013962689554318786`, frozen control delta `0.0` |
| partial-small complete fine-tuning trial | not completed |
| partial-large trial | not started |
| full Caduceus fine-tuning | resource-deferred; not completed |
| adaptation HPO/selection | incomplete; selection open |
| 801-row adaptation evaluation | closed and unopened |

The exact appendix is [research/adaptation_attempt/README.md](research/adaptation_attempt/README.md). The project never claims **PARTIAL FOUNDATION-MODEL FINE-TUNING COMPLETED** or **FULL FOUNDATION-MODEL FINE-TUNING COMPLETED**.

## HPO and selection boundary

Baseline HPO is validation-only and recorded in
[docs/HYPERPARAMETER_TUNING.md](docs/HYPERPARAMETER_TUNING.md). The separate
post-hoc Caduceus HPO was declared TRAIN-only, gene-grouped, and persisted, but
the mandatory queue did not complete. No adaptation configuration, final
epoch count, calibration source, or 801-row result was selected. The historical
946-row locked cohort remains prohibited for adaptation selection.

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

## Reading the web comparison dialog

The web workbench intentionally shows two different evidence sources side by
side. ClinVar supplies the external clinical-significance record. Evo2 supplies
raw research scores for the same GRCh38 single-nucleotide variant. The Evo2
score does **not** replace, reproduce, or overrule the ClinVar classification.

<p align="center">
  <img src="docs/images/variant-analysis-comparison.png" alt="Variant Analysis Comparison dialog showing ClinVar classification and Evo2 research signal" width="900">
</p>

_Example shown above: BRCA1 ClinVar record 4883316 at GRCh38 position
43,092,225. The record is classified as **Uncertain significance** by ClinVar;
that label is not inferred from the Evo2 number._

### What each field means

| Dialog field | Source or calculation | Interpretation |
|---|---|---|
| Position | Live ClinVar location, represented as a 1-based GRCh38 coordinate | The genomic base position sent to the scorer. |
| Type | ClinVar variation type | This example is a single-nucleotide variant (SNV). Indels are not sent through this single-base research action. |
| ClinVar notation | The allele notation in the ClinVar transcript record | `T>A` is transcript-oriented notation for this BRCA1 record. |
| GRCh38 allele | Reference-checked genomic allele | `A>T` is the genomic orientation used by the scorer. BRCA1 is on the reverse strand, so the transcript alleles are complemented (`T→A`, `A→T`). |
| ClinVar ID | NCBI ClinVar record identifier | The link opens the external source record used for the classification. |
| ClinVar classification | `germline_classification.description` from the ClinVar response | Values such as `Pathogenic`, `Likely pathogenic`, `Benign`, `Likely benign`, or `Uncertain significance` come from ClinVar. |
| Primary delta signal | Mean of the forward and reverse-complement deltas | The orientation-combined raw Evo2 research signal; it is not a probability, thresholded label, or confidence. |
| Forward / reverse-complement | Two independent Evo2 orientation scores | The raw alternate-minus-reference signal for each sequence orientation. |
| Disagreement | Absolute difference between the two orientation deltas | A diagnostic of orientation sensitivity, not a clinical uncertainty score. |

### Exact formulas

For each orientation, Evo2 scores the reference sequence and the sequence with
the requested alternate base. The scorer records the alternate-minus-reference
log-likelihood difference:

~~~text
delta_forward = logL(alternate, forward) - logL(reference, forward)
delta_reverse = logL(alternate, reverse-complement)
                - logL(reference, reverse-complement)

delta_primary = (delta_forward + delta_reverse) / 2

orientation_disagreement = abs(delta_forward - delta_reverse)
~~~

The screenshot's displayed values are the rounded form of the raw response:

~~~text
delta_forward = -0.0005704760551452637
delta_reverse = -0.000057756900787353516

delta_primary = (-0.0005704760551452637
                 + -0.000057756900787353516) / 2
               = -0.0003141164779663086
               → -0.000314 in the dialog

orientation_disagreement = abs(-0.0005704760551452637
                               - -0.000057756900787353516)
                          = 0.0005127191543579102
                          → 0.000513 in the dialog
~~~

### How to read the raw signal

- A negative delta means the alternate sequence received a lower raw Evo2
  score than the reference sequence in that context.
- A positive delta means the alternate sequence received a higher raw Evo2
  score in that context.
- A value close to zero means the model's raw scores are close. It does **not**
  mean benign, harmless, or clinically neutral.
- A larger forward/reverse disagreement means the two orientations respond
  differently. It is a reason to inspect the context and provenance, not a
  pathogenicity or benignity cutoff.
- There is no clinical threshold or model-derived benign/pathogenic label in
  this dialog. The only clinical-significance label displayed is the external
  ClinVar classification.

### Where the values come from

The complete request path is:

~~~text
ClinVar query
  → position, transcript allele, type, and classification
  → reverse-strand normalization when needed
  → GRCh38 reference validation
  → /api/score/variant transport route
  → configured Evo2 scoring service
  → forward + reverse-complement raw scores
  → delta formulas above
  → comparison dialog
~~~

The web client does not hard-code the values in the screenshot. The ClinVar
row is populated from a live NCBI query, and the research fields are returned
by the configured scorer with provenance such as model revision, context
length, scoring semantics, and `research_only: true`. The service URL is
configured through the server-only `EVOVARIANT_SCORER_URL` in the local ignored
`.env` or `.env.local` file (the legacy
`NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` name is still accepted, but it is
inlined at build time). The value is read at runtime, so `next start` honours an
override without a rebuild; it is not embedded in the README, and no fake scorer
is used when the service is unavailable — the transport routes answer `503`
instead.

Relevant implementation points are [the ClinVar query and scorer transport](apps/web/src/utils/genome-api.ts), [the row parsing and reverse-strand normalization](apps/web/src/components/known-variants.tsx), [the comparison dialog](apps/web/src/components/variant-comparison-modal.tsx), [the API validation/forwarding route](apps/web/src/app/api/score/variant/route.ts), and [the scorer payload formulas](evo2_scorer_app.py).

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
- [Final polish figure inventory](artifacts/audits/FINAL_FIGURE_INVENTORY.json)
- [Final metrics table](research/reports/final_metrics_table.json)

No fine-tuning loss curve, context-length curve, or unsupported intermediate
temporal trend is shown. Fine-tuning loss is deferred, the context-length
cell is not applicable to the frozen 8,192-bp cache, and unsupported trends
remain absent.

<details>
<summary>Complete rendered figure gallery (42 families: 39 Phase 17 + 3 final dashboards)</summary>

The 39 registered Phase 17 families remain unchanged. The three final polish
dashboards are source-derived from the frozen receipt and joined predictions.

- [ablation_metric_delta](research/figures/final/ablation_metric_delta.png)
- [bootstrap_interval](research/figures/final/bootstrap_interval.png)
- [cache_reuse](research/figures/final/cache_reuse.png)
- [calibration_metric_comparison](research/figures/final/calibration_metric_comparison.png)
- [calibration_reliability](research/figures/final/calibration_reliability.png)
- [classifier_auroc_heatmap](research/figures/final/classifier_auroc_heatmap.png)
- [classifier_brier_heatmap](research/figures/final/classifier_brier_heatmap.png)
- [classifier_mcc_heatmap](research/figures/final/classifier_mcc_heatmap.png)
- [cohort_flow](research/figures/final/cohort_flow.png)
- [combination_ranking](research/figures/final/combination_ranking.png)
- [compute_cumulative_rows](research/figures/final/compute_cumulative_rows.png)
- [cost_by_phase_model](research/figures/final/cost_by_phase_model.png)
- [cumulative_compute_spend](research/figures/final/cumulative_compute_spend.png)
- [development_final_generalization](research/figures/final/development_final_generalization.png)
- [diversity_matrix](research/figures/final/diversity_matrix.png)
- [ensemble_comparison](research/figures/final/ensemble_comparison.png)
- [final_abstention_semantics](research/figures/final/final_abstention_semantics.png)
- [final_chromosome_distribution](research/figures/final/final_chromosome_distribution.png)
- [final_class_distribution](research/figures/final/final_class_distribution.png)
- [final_classification_metrics](research/figures/final/final_classification_metrics.png)
- [final_confusion_matrix](research/figures/final/final_confusion_matrix.png)
- [final_error_chromosome](research/figures/final/final_error_chromosome.png)
- [final_f1_metrics](research/figures/final/final_f1_metrics.png)
- [final_fp_fn](research/figures/final/final_fp_fn.png)
- [final_gene_errors](research/figures/final/final_gene_errors.png)
- [final_gene_top](research/figures/final/final_gene_top.png)
- [final_outcome_counts](research/figures/final/final_outcome_counts.png)
- [final_pr](research/figures/final/final_pr.png)
- [final_probability_quality](research/figures/final/final_probability_quality.png)
- [final_roc](research/figures/final/final_roc.png)
- [foundation_model_performance](research/figures/final/foundation_model_performance.png)
- [hpo_hyperparameters](research/figures/final/hpo_hyperparameters.png)
- [hpo_trial_history](research/figures/final/hpo_trial_history.png)
- [learning_curve_auroc](research/figures/final/learning_curve_auroc.png)
- [learning_curve_metrics](research/figures/final/learning_curve_metrics.png)
- [project_timeline](research/figures/final/project_timeline.png)
- [raw_vs_representation](research/figures/final/raw_vs_representation.png)
- [representation_layers](research/figures/final/representation_layers.png)
- [risk_coverage_development](research/figures/final/risk_coverage_development.png)
- [runtime_by_model](research/figures/final/runtime_by_model.png)
- [temporal_transition](research/figures/final/temporal_transition.png)
- [throughput_comparison](research/figures/final/throughput_comparison.png)

The separate adaptation appendix has [encoder update proof](research/adaptation_attempt/figures/encoder_update_proof.png) and [workflow state](research/adaptation_attempt/figures/adaptation_workflow.png).
</details>

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
| Adaptation implementation snapshot | [research/adaptation_attempt/source_snapshot/](research/adaptation_attempt/source_snapshot/) |
| Final dashboard generator | [scripts/generate_final_readme_figures.py](scripts/generate_final_readme_figures.py) |

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

Rebuilding the entire benchmark surface is also free: the expansion reads
registered caches, and the external continuation can be re-derived from the
persisted raw predictions without starting a GPU worker.

~~~bash
# 1. Recompute every local benchmark artifact from registered evidence.
PYTHONPATH=src .venv/bin/python scripts/benchmark_expansion/run_local.py

# 2. Re-derive the completed external catalogs from persisted predictions.
#    (No Modal worker is constructed; remote_compute_started=false.)
EVOVARIANT_EXTERNAL_MODE=local-finalize PYTHONPATH=src \
  .venv/bin/python scripts/benchmark_expansion/complete_external.py
~~~

The second command is the reason the external statuses survive a full local
rebuild: `run_local.py` correctly reports `COMPUTE_BLOCKED` for the external
entries, and `local-finalize` then promotes them using the already-persisted
raw predictions and recorded runtime receipt.

The final baseline validation requires all applicable gates to pass. It checks
secrets, formatting, strict typing, unit/integration/scientific tests, schema
and registry integrity, protocol hashes, frontend/browser behavior, figure
generation, and whitespace integrity.

The final polish also checks notebook JSON/AST validity, local README links,
source-hashed final dashboards, and the adaptation evidence manifest. These
checks are presentation/provenance checks; they do not turn incomplete
adaptation into a completed scientific experiment.

The final publication bundle contains 41 inventory entries, 39 rendered figure
families, 39 source sidecars, and 12 tables. The visual audit reports
<code>39/39</code> structural PASS, zero failed families, and a manual
contact-sheet review with no clipping, missing labels, missing stage markers,
missing sample sizes, axis/caption truncation, or unsupported trend claims.

## Corrections applied 2026-09-24

A full read-only audit of this repository was performed, the defects it found
were fixed, and the affected evidence was regenerated. No scientific input,
label, threshold, or model artifact was modified by the audit.

| Correction | What was wrong | Regenerated evidence |
|---|---|---|
| PhyloP comparator coverage | The benchmark loader recognised only `scaled_phred`, `raw_score`, `score`, and `value`, so PhyloP's `sitewise_score` field was invisible and coverage read `0/4,000` `DATA_BLOCKED`. | [Comparator coverage](apps/web/public/benchmarks/data/figures/classical_comparator_coverage.json) now reports 3,997/4,000 formal and 946/946 locked, and the case studies gained PhyloP scores. |
| Protocol lock preservation | Regenerating on a machine without the external master prompt wrote `master_prompt_sha256: null`, silently dropping a frozen hash. | The previously locked hash is preserved and labelled `preserved-from-previous-protocol-lock`; override the source with `EVOVARIANT_MASTER_PROMPT_PATH`. |
| Web scorer URL convention | `/api/score/variant` posted to the bare configured URL while `/api/batch/*` and `/api/results/*` appended REST paths, so no single configuration could satisfy both. | A shared resolver accepts a REST base URL or an explicit endpoint; all four transport routes were verified against a live local scorer. |
| Runtime environment override | `NEXT_PUBLIC_*` values are inlined at build time, so `next start` ignored runtime overrides and the browser-test config could not retarget the scorer. | New server-only `EVOVARIANT_SCORER_URL` is read at runtime; the legacy name still works but is documented as build-time only. |
| Legacy 8,193-bp window | `evo2-backend/main.py` fetched 8,193 bases for an 8,192-base window (off-by-one) and still printed clinical labels. | The window is corrected to exactly 8,192 bases with a deprecation banner pointing at the frozen implementation. |

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
- [Final metrics](docs/METRICS.md)
- [Fine-tuning attempt](docs/FINE_TUNING_ATTEMPT.md)
- [Adaptation compute limitations](docs/ADAPTATION_COMPUTE_LIMITATIONS.md)
- [Contribution map](docs/CONTRIBUTION_MAP.md)
- [Judge demo guide](docs/JUDGE_DEMO.md)

## Experimental fine-tuning appendix

The primary science remains the frozen temporal baseline. The follow-up
foundation-model adaptation attempt is intentionally at the bottom of the
project surface so its status is visible without being confused with the
headline result:

- [Adaptation README and status](research/adaptation_attempt/README.md)
- [Fine-tuning method](research/adaptation_attempt/FINE_TUNING_METHOD.md)
- [Adaptation HPO status](research/adaptation_attempt/HYPERPARAMETER_TUNING.md)
- [Compute limitations](research/adaptation_attempt/COMPUTE_LIMITATIONS.md)
- [Evidence manifest](research/adaptation_attempt/EVIDENCE_MANIFEST.json)
- [Encoder-update proof](research/adaptation_attempt/artifacts/caduceus_partial_small_finetune_smoke.json)

Allowed wording is **encoder-update feasibility proof**, **frozen-head
TRAIN-only stage completed**, or **adaptation HPO incomplete**. The repository
does not state that partial or full Caduceus foundation-model fine-tuning was
completed.

## References

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

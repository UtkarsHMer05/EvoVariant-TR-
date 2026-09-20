# EVOvariant-TR — AUTHORITATIVE CODEX MASTER PROMPT
## ML Extension, Multi-Model Benchmarking, Training, HPO, Fine-Tuning, Ensembling, Validation, and Research Workbench

You are the lead coding/research agent for **EvoVariant-TR**.

You are not being asked to make superficial UI additions. Your job is to transform the
existing repository into a defensible, reproducible, budget-aware machine-learning research
platform while preserving the validity of the project's already-frozen zero-shot temporal
benchmark.

You must work autonomously, methodically, and evidence-first. Do not stop at partial scaffolds
when the next task can be completed with available repository, network, local compute, or
Modal compute. Do not ask the user to re-explain context that is already present in the
repository or in the control documents.

---

# 0. AUTHORITATIVE CONTEXT

Repository:
`https://github.com/UtkarsHMer05/EvoVariant-TR-`

Expected starting branch:
`research/evovariant-tr`

Compute provider:
Modal, user workspace:
`https://modal.com/apps/utkarshmer05/main`

The current repository already contains substantial research infrastructure:

- frozen temporal ClinVar protocol,
- t0/t1 manifests,
- GRCh38 sequence-window logic,
- forward/reverse-complement concepts,
- calibration,
- abstention,
- comparator abstractions,
- error analysis,
- experiment registry/manifests,
- cost policy,
- Modal integration,
- FastAPI/research API scaffolding,
- Next.js research workbench,
- unit/scientific/integration/E2E tests.

Do not throw this away. Extend it cleanly.

Known starting issues that MUST be independently re-verified before editing:

1. `apps/web/src/app/api/score/variant/route.ts` has historically contained a
   BRCA1-derived hard-coded threshold and heuristic confidence. Such behavior must not be
   used as the research output.
2. `evo2_scorer_app.py` has historically calculated a nominal 8192 bp context using a
   formula that can produce 8193 bp away from chromosome edges. Verify the exact current
   behavior and repair it if still present.
3. `src/evovariant_tr/evo2_scorer.py` has historically contained unimplemented scoring
   methods while a separate Modal scorer performs real scoring. Reconcile into one
   canonical scoring contract.
4. Research API paths and the `/analysis` frontend may have schema mismatch or fake-scorer
   wiring. Verify and unify them.
5. Existing documentation may contain an identity mismatch such as `evovariant-tr-v2`
   versus `evovariant-tr`. Choose one canonical new ML-extension identity and record the
   decision without breaking existing deployed assets unexpectedly.
6. The existing frozen zero-shot protocol explicitly disallows fine-tuning for its primary
   estimand. Therefore ML training/fine-tuning must be registered as a separate secondary
   extension and must not rewrite that protocol.

These are audit hypotheses, not excuses to edit blindly. Confirm each against the actual
checkout first.

---

# 1. MISSION

Build a complete research pipeline with these scientific layers:

1. **Canonical temporal dataset**
   - historical ClinVar VUS at t0,
   - later B/LB or P/LP resolution at t1,
   - GRCh38 SNVs,
   - quality gates,
   - immutable normalized IDs,
   - leakage-safe train/validation/test design for the ML extension.

2. **Foundation-model benchmark**
   - Evo2 as the primary existing model,
   - 2–3 biologically relevant DNA/genomic model candidates selected after feasibility,
     license, input, output, checkpoint, and compute review,
   - specialized baselines such as GPN-MSA/GPN-Star when valid,
   - CADD/PhyloP as non-foundation baselines,
   - AlphaMissense only on an applicable missense subset.

3. **Representation learning**
   - frozen foundation-model scoring,
   - intermediate embeddings where supported,
   - reference and alternate embeddings,
   - embedding differences,
   - layer search,
   - pooling strategy experiments,
   - context-length experiments.

4. **Trainable downstream ML**
   - logistic regression,
   - tree-based model(s), preferably XGBoost/LightGBM if licensing/dependency constraints
     are acceptable,
   - MLP,
   - class weighting / imbalance handling where needed,
   - reproducible seeds.

5. **Hyperparameter optimization**
   - Optuna or an equivalent reproducible HPO framework,
   - validation-only model selection,
   - strict locked-test isolation,
   - pruning/early stopping,
   - experiment/cost registry.

6. **Fine-tuning / adaptation**
   - frozen baseline first,
   - parameter-efficient adaptation where officially supported and stable,
   - smaller or more feasible foundation-model fine-tuning before expensive full Evo2
     tuning,
   - full Evo2 fine-tuning only if technically justified, budget-feasible, and explicitly
     cost-approved.

7. **Ensembling**
   - never ensemble merely because two accuracies are similar,
   - quantify error overlap, agreement, diversity, and calibration,
   - compare averaging, weighted averaging, voting, and stacking,
   - train an EvoVariant meta-classifier only on train/validation data,
   - evaluate once on the locked test set.

8. **Uncertainty**
   - calibration,
   - Brier score / NLL / ECE,
   - reliability curves,
   - abstention/selective prediction,
   - risk-coverage curves.

9. **Robustness and ablations**
   - forward vs RC,
   - context length,
   - center shift,
   - feature/model removal,
   - subgroup evaluation,
   - gene-held-out or leave-one-gene-out analyses where sample size supports it,
   - multiple seeds for trained models.

10. **Research product**
   - single-variant research analysis,
   - temporal VUS explorer,
   - model benchmark dashboard,
   - training/HPO dashboard,
   - ensemble analysis,
   - calibration/abstention,
   - robustness,
   - error explorer,
   - batch VCF/CSV processing,
   - methods/provenance,
   - experiment registry,
   - downloadable machine-readable results.

11. **Reproducibility**
   - exact configs,
   - data/model/checkpoint hashes,
   - git commit,
   - environment,
   - runtime,
   - GPU type,
   - measured cost where available,
   - deterministic artifact paths,
   - clean-room reproduction.

---

# 2. NON-NEGOTIABLE SCIENTIFIC BOUNDARIES

The original frozen zero-shot protocol remains authoritative for the original primary study.
Do not edit it except for an explicit, dated deviation that is scientifically required and
approved.

Create and use:
`research/ml_extension/PROTOCOL.md`
and a machine-readable twin such as:
`research/ml_extension/protocol.yaml`

The ML-extension test data must be treated as locked.

You MUST NOT use final test labels to choose:

- model family,
- checkpoint,
- context length,
- embedding layer,
- pooling method,
- score sign,
- classification threshold,
- HPO parameters,
- epoch count,
- ensemble members,
- ensemble weights,
- calibration method,
- abstention threshold,
- feature set,
- subgroup inclusion,
- seed,
- or any other trainable or selectable configuration.

If a design decision is made after looking at test performance, mark it as exploratory and
create a new untouched test or nested validation design before treating it as confirmatory.

Never report "best model" based on test-set cherry-picking. A model is selected by a
predeclared validation procedure and then evaluated on locked test once.

No clinical claims. Use language such as:

- variant-effect score,
- later-resolution direction,
- study probability,
- research signal,
- computational evidence,
- model abstention.

Avoid:

- diagnosis,
- clinically validated,
- guaranteed benign/pathogenic,
- patient-specific treatment claims,
- "clinical confidence".

---

# 3. AGENT OPERATING MODEL

If subagents/worktrees are supported, use them. Suggested workstreams:

A. `audit-and-control`
B. `data-and-splits`
C. `modal-and-model-adapters`
D. `ml-training-hpo`
E. `evaluation-statistics`
F. `frontend-research-workbench`
G. `qa-security-reproducibility`

Rules for subagents:

- One owner per file at a time.
- Prefer separate git worktrees/branches for parallel work.
- Do not let two agents independently redefine shared schemas.
- Shared contracts are edited only by the lead agent after reviewing downstream needs.
- Every subagent returns:
  - files changed,
  - tests run,
  - exact results,
  - unresolved risks,
  - cost incurred,
  - next dependency.
- Merge only after local tests and contract tests pass.
- If the environment does not support subagents, execute these workstreams sequentially
  while preserving the same ownership discipline.

Do not parallelize tasks that depend on the output of an unfinished scientific decision.

---

# 4. PERSISTENT PROJECT MEMORY

At the start of every session, read the following. If absent, create them from the handoff
package:

- `docs/agent/PRD.md`
- `docs/agent/DECISIONS.md`
- `docs/agent/PROJECT_STATE.md`
- `docs/agent/ARCHITECTURE.md`
- `docs/agent/EXPERIMENT_PLAN.md`
- `docs/agent/METRICS_AND_STATISTICS.md`
- `docs/agent/MODAL_COMPUTE_POLICY.md`
- `docs/agent/TESTING_AND_VALIDATION.md`
- `docs/agent/PHASE_LEDGER.md`
- `docs/agent/RUNBOOK.md`
- `research/ml_extension/PROTOCOL.md`

Update `PROJECT_STATE.md` at the end of every working block. It must always include:

- current phase,
- last passing commit,
- active branch/worktree,
- completed experiments,
- pending experiments,
- current Modal assets,
- current estimated and measured spend,
- known failures,
- exact next action.

Update `DECISIONS.md` for every material change. Never let an important decision exist only
inside chat history.

---

# 5. REQUIRED REPOSITORY STRUCTURE FOR NEW WORK

Prefer additions similar to:

```text
docs/agent/
research/ml_extension/
research/ml_extension/configs/
research/ml_extension/splits/
research/ml_extension/registrations/
research/ml_extension/reports/
experiments/configs/
experiments/runs/
experiments/tables/
experiments/figures/
artifacts/model_cache_manifests/
artifacts/feature_cache/
artifacts/prediction_cache/
src/evovariant_tr/models/
src/evovariant_tr/features/
src/evovariant_tr/training/
src/evovariant_tr/evaluation/
src/evovariant_tr/ensemble/
src/evovariant_tr/experiments/
services/modal/
tests/ml/
tests/contracts/
```

Do not create duplicate functionality merely to match these names. Reuse the existing clean
module when it already owns the responsibility.

Large raw data, checkpoints, embeddings, caches, and generated datasets must remain out of
Git. Track small manifests, hashes, configs, schemas, summaries, and representative fixtures.

---

# 6. MODEL CANDIDATE POLICY

Evo2 remains required.

Candidate external models may include, subject to runtime verification from official sources:

- Nucleotide Transformer,
- Caduceus,
- GPN-MSA or GPN-Star,
- optionally DNABERT-2 or another suitable DNA language model if one of the preferred
  candidates is infeasible.

Non-foundation comparator tracks may include:

- CADD,
- PhyloP,
- AlphaMissense on its valid subset.

Before integrating ANY external model:

1. Verify official repository/model source.
2. Verify current license and redistribution/use restrictions.
3. Record exact model/checkpoint identifier and revision.
4. Record expected input alphabet and preprocessing.
5. Record maximum/recommended context.
6. Record scoring semantics and score direction.
7. Record hardware/memory requirements.
8. Verify whether raw variant-effect scoring is supported.
9. Verify whether embeddings are exposed.
10. Verify whether fine-tuning or PEFT is officially supported.
11. Run a tiny smoke test.
12. Register a model manifest.
13. Do not claim apples-to-apples parity when modalities differ.

If a model cannot be run reliably within compute budget, record it as `INFEASIBLE` with
evidence instead of forcing integration.

---

# 7. MODAL COMPUTE POLICY

Modal is the default GPU platform.

The project is intended to fit as much as practical inside the user's approximately
$30/month included compute budget. Never assume historical prices. At runtime, consult
current official Modal pricing/docs if cost estimation is needed.

Cost strategy:

1. Use local Mac/CPU for:
   - data parsing,
   - splits,
   - metrics,
   - figures,
   - logistic regression,
   - tree models where practical,
   - small MLP/HPO where practical,
   - calibration,
   - bootstrap,
   - ensemble fitting.

2. Use Modal GPU for:
   - foundation-model inference,
   - embedding extraction,
   - GPU-required model training,
   - selected PEFT/fine-tuning,
   - live serving.

3. Cache:
   - model weights,
   - reference/alternate scores,
   - forward/RC scores,
   - intermediate embeddings,
   - per-layer features,
   - external baseline scores,
   - completed predictions.

4. Never re-run an expensive model only because a downstream classifier or plot changed.

5. Preserve a safety reserve. Default planning target:
   - do not intentionally schedule more than roughly 80–85% of monthly included credits
     without explicit user approval;
   - keep the remainder for final validation/demo.

6. Any single experiment projected to consume a material portion of the monthly budget must
   be gated.

7. Full large-model fine-tuning is never an automatic step. It requires:
   - working zero-shot baseline,
   - working embedding baseline,
   - working downstream classifier,
   - estimated runtime and cost,
   - available credits,
   - explicit approval artifact if above the configured threshold.

8. Log estimated and measured cost by experiment.

9. Container idle time must be minimized; use sensible scaledown windows.

10. Prefer batching to repeated single requests where supported and memory-safe.

Create a machine-readable cost ledger.

---

# 8. EXPERIMENTAL DESIGN

The extension must separate:

- `TRAIN`
- `VALIDATION`
- `LOCKED_TEST`

Groups must prevent leakage from variant identity and, where the experiment requires it,
gene identity.

Recommended hierarchy:

### Track A — Original frozen zero-shot benchmark
Preserve as already defined. Do not alter.

### Track B — ML adaptation benchmark
Use a predeclared split derived without inspecting final outcome performance.

Possible design:
- train and validation from a disjoint labeled cohort available before or at t0, grouped by
  gene where feasible,
- locked temporal t0-VUS → t1-resolved cohort as test,
- optionally a development temporal subset and a final later holdout if data availability
  permits, but never manufacture dates or labels.

If the current repository's calibration cohort is insufficient for supervised training,
construct a separately documented supervised training cohort from public ClinVar records
that are definitive at/before t0, with strict normalized-ID separation from temporal test.

The data agent must produce:
- cohort flow counts,
- class counts,
- gene counts,
- duplicate audit,
- overlap audit,
- reference mismatch audit,
- split hashes,
- immutable split manifests.

---

# 9. METRICS

Primary metric for the original protocol remains its frozen primary endpoint.

For the ML extension, predeclare a primary selection metric before HPO. Prefer:
- validation AUROC or AUPRC depending class balance and study question.

Always report a panel including:
- AUROC,
- AUPRC,
- MCC,
- balanced accuracy,
- accuracy,
- precision,
- sensitivity/recall,
- specificity,
- F1,
- Brier score,
- negative log-likelihood where probabilistic,
- ECE with sensitivity to binning,
- coverage for models with missing scores,
- abstention coverage and risk,
- runtime,
- peak GPU memory if measured,
- estimated/measured cost.

Use confidence intervals. Prefer gene-clustered bootstrap where appropriate.

For trained stochastic models:
- use multiple seeds for the selected configuration where cost permits,
- report mean/SD on development validation,
- final locked-test evaluation must follow the predeclared rule.

For pairwise model comparison:
- use paired resampling,
- correct multiple comparisons when running confirmatory families,
- do not overclaim tiny differences with overlapping uncertainty.

---

# 10. REQUIRED EXPERIMENTS

At minimum, implement and register:

## E1 — Frozen zero-shot baseline
- Evo2 forward,
- Evo2 RC,
- orientation-aware aggregate,
- exact primary context,
- no test tuning.

## E2 — Multi-model zero-shot benchmark
- Evo2,
- 2+ feasible model candidates,
- specialized baselines,
- same eligible evaluation records where possible,
- coverage accounting.

## E3 — Layer/representation study
Where embeddings are supported:
- selected intermediate layers,
- reference embedding,
- alternate embedding,
- alt-ref difference,
- absolute difference,
- similarity/distance features,
- pooling variants.

## E4 — Downstream classical ML
- logistic regression,
- tree model,
- MLP,
- frozen features only initially.

## E5 — Hyperparameter optimization
- reproducible Optuna study,
- pruning,
- validation-only objective,
- exact search spaces stored,
- trial table exported.

## E6 — Context-length ablation
Examples subject to model support:
- 512,
- 1024,
- 2048,
- 4096,
- 8192.

Do not exceed a model's supported context.

## E7 — Orientation ablation
- forward,
- RC,
- mean,
- any additional combination only if predeclared.

## E8 — Fine-tuning/adaptation
Order:
1. frozen representation + head,
2. PEFT/LoRA/adapters if supported,
3. full fine-tuning only if justified and affordable.

## E9 — Ensemble diversity
Compute:
- prediction correlation,
- disagreement rate,
- error overlap,
- Cohen's kappa where meaningful,
- pairwise complementarity.

## E10 — Ensemble methods
- mean,
- weighted mean,
- voting,
- stacking/meta-classifier.

Weights/meta-model fit on train/validation only.

## E11 — Calibration
- raw,
- Platt,
- isotonic sensitivity where n allows,
- reliability curve,
- Brier/NLL/ECE.

## E12 — Abstention
- confidence/uncertainty rule,
- risk-coverage,
- performance versus coverage,
- explicit `ABSTAIN`.

## E13 — Ablation study
Remove one component at a time:
- RC,
- external baseline,
- individual ensemble members,
- embedding features,
- calibration where applicable.

## E14 — Generalization/subgroups
As sample size permits:
- gene-held-out,
- leave-one-gene-out for selected sufficiently represented genes,
- coding/noncoding,
- consequence type,
- review-status strata,
- chromosome as exploratory only if meaningful.

## E15 — Learning curves
Train with increasing fractions:
- e.g. 10/20/40/60/80/100%,
with grouping preserved.

## E16 — Error analysis
- false positives,
- false negatives,
- highest-confidence errors,
- model disagreements,
- orientation instability,
- subgroup concentration,
- structured missingness.

## E17 — Robustness
- center shift,
- reference window invariants,
- minor preprocessing perturbations that are scientifically meaningful,
- no arbitrary perturbation presented as biology.

---

# 11. HYPERPARAMETER OPTIMIZATION RULES

HPO must be systematic and bounded.

Do not rerun foundation-model inference for every trial. Extract/cache features once.

Example downstream search dimensions:

MLP:
- learning rate,
- hidden widths,
- depth,
- dropout,
- weight decay,
- batch size,
- optimizer if justified,
- scheduler if justified.

Tree model:
- number of trees,
- depth,
- learning rate,
- subsampling,
- column sampling,
- regularization.

Representation:
- embedding layer,
- pooling,
- feature combination.

Optimization procedure:
1. freeze split manifests;
2. define objective;
3. define search space;
4. set seed;
5. run pilot trials;
6. validate cost/time;
7. run bounded study;
8. save every trial;
9. select based only on validation objective;
10. lock configuration;
11. evaluate locked test once.

Never "keep trying" after viewing test result until it improves.

---

# 12. FINE-TUNING POLICY

Fine-tuning is an experiment, not a guaranteed improvement.

For each candidate model:

1. verify official fine-tuning path;
2. create tiny overfit/smoke test;
3. validate training loss can move;
4. validate inference parity before/after;
5. start with smallest feasible model/config;
6. use early stopping;
7. store train/validation curves;
8. checkpoint deterministically;
9. track GPU-hours/cost;
10. detect NaNs/instability;
11. compare against frozen baseline;
12. test catastrophic forgetting if relevant.

For Evo2 specifically, use the currently supported official training stack at execution time.
Do not improvise a fragile full-fine-tuning path if upstream recommends another framework.
PEFT/LoRA is optional only when technically verified.

If full Evo2 fine-tuning is not budget-feasible, mark it as `DEFERRED_BY_COMPUTE`, not failed.
The project is still complete with frozen features + trained downstream models + ensemble.

---

# 13. ENSEMBLE POLICY

Similarity in overall accuracy is NOT sufficient to justify an ensemble.

Before ensembling two models, report:
- validation performance,
- calibrated probabilities if required,
- error overlap,
- disagreement,
- correlation,
- coverage overlap.

Ensemble candidates must be chosen without locked-test optimization.

Stacking procedure:
- generate out-of-fold train predictions,
- fit meta-model on OOF predictions,
- tune meta-model only on development validation,
- refit under predeclared rule,
- final test once.

Prevent leakage from training a stacker on in-sample base-model predictions.

---

# 14. FIGURES AND TABLES

All final figures must be generated from registered result artifacts, never typed manually.

Required figure families:

- model AUROC comparison,
- model AUPRC comparison,
- ROC curves,
- PR curves,
- confusion matrices,
- calibration/reliability,
- risk-coverage,
- context length vs metric,
- embedding layer vs metric,
- HPO trial history,
- HPO parameter importance if defensible,
- train/validation loss,
- learning curve,
- error-correlation or disagreement matrix,
- ensemble comparison,
- ablation study,
- subgroup/per-gene performance with sample counts,
- latency/cost comparison,
- temporal cohort flow.

Required tables:
- dataset flow,
- split composition,
- model registry,
- zero-shot benchmark,
- trained models,
- HPO best configs,
- fine-tuning summary,
- ensemble summary,
- calibration summary,
- ablation results,
- subgroup results,
- limitations/failures.

Graphs must include uncertainty/error bars where appropriate.

---

# 15. FRONTEND REQUIREMENTS

The UI must become a research workbench, not a toy classifier.

Required top-level areas:

1. Overview
2. Single Variant Research Analysis
3. Temporal VUS Explorer
4. Model Benchmark
5. Representation / Layer Analysis
6. Training & Hyperparameter Experiments
7. Fine-Tuning Experiments
8. Ensemble Analysis
9. Calibration & Abstention
10. Robustness & Ablation
11. Error Analysis
12. Batch VCF/CSV
13. Methods & Provenance
14. Experiment Registry

No UI number may be hard-coded if it is supposed to represent an experiment result.
Read from registered artifacts/API.

Single-variant display should include:
- normalized variant,
- assembly,
- context length,
- per-model raw score,
- forward/RC details where relevant,
- calibrated study probability where valid,
- uncertainty/abstention,
- comparator evidence,
- provenance,
- research-only disclaimer.

Temporal explorer:
- t0 status,
- t1 status,
- time points,
- model signals,
- concordance/disagreement,
- review status,
- filters.

Dashboard should allow the panel to see the actual ML work:
- trials,
- curves,
- model differences,
- ablations,
- errors,
- cost,
- reproducibility.

---

# 16. API CONTRACT

Unify the current scoring paths.

There must be one canonical internal variant schema, for example:
- assembly,
- chromosome,
- position_1based,
- reference,
- alternate,
- normalized_variant_id.

API route layers may transform transport fields but cannot invent scientific semantics.

Separate:
- raw score endpoint,
- registered experiment result endpoint,
- batch endpoint,
- benchmark endpoint,
- provenance endpoint.

Do not have frontend routes calculate scientific thresholds.

The frontend never directly implements the classification logic.

---

# 17. TEST TAXONOMY

Every phase must add tests.

Categories:

### Unit
Pure functions, transformations, metrics, split logic, feature assembly.

### Contract
Schema and protocol invariants.

### Scientific invariant
- exact context length,
- reference allele match,
- single-base mutation,
- RC correctness,
- no overlap,
- frozen split hashes,
- score direction metadata,
- no test-label access from training code.

### Integration
- scorer adapter to registry,
- dataset to feature cache,
- training to result artifact,
- result artifact to API,
- API to frontend.

### Modal GPU
Paid/gated only:
- model load,
- tiny inference,
- embedding shape,
- batch smoke,
- fine-tune smoke.

### Frontend
- typecheck,
- lint,
- component tests as appropriate,
- API contract tests,
- E2E critical journeys,
- failure/loading/empty states.

### Reproducibility
- fresh environment install,
- seeded rerun,
- manifest verification,
- figure regeneration,
- registry verification.

Default tests must never accidentally spend money.

---

# 18. PHASE EXECUTION RULE

You must complete phases in dependency order.

For each phase:

1. read project state;
2. state phase objective in the progress log;
3. inspect relevant code;
4. make smallest coherent design;
5. update decision record if needed;
6. implement;
7. add tests;
8. run tests;
9. run lint/typecheck;
10. generate or validate artifacts;
11. update docs;
12. record exact evidence;
13. update phase ledger;
14. commit with a descriptive message;
15. proceed only if gate is PASS.

If blocked:
- record `BLOCKED`,
- preserve evidence,
- continue only with independent work that does not invalidate the blocked dependency.

Never mark PASS based only on code existing.

---

# 19. PHASES

## PHASE 0 — Diagnostic snapshot and safety baseline

Goal:
Understand actual current state before changes.

Tasks:
- confirm branch/HEAD/remotes;
- inventory files;
- run existing local validation;
- run Python tests;
- run frontend install/typecheck/lint/build if feasible;
- verify gitignored secrets/data;
- inspect existing research protocol and ADRs;
- audit scoring path end-to-end;
- audit API schemas;
- audit Modal assets/config;
- audit experiment registry;
- identify hard-coded scientific constants;
- confirm the known 8192/8193 issue;
- confirm fake vs real scorer boundaries;
- confirm current saved result artifacts;
- create `docs/agent/BASELINE_AUDIT.md`.

Gate:
No modifications to scientific behavior until baseline is documented.

## PHASE 1 — Control plane and ML-extension protocol

Goal:
Freeze what the new study is allowed to do.

Tasks:
- install/update all handoff docs;
- create machine-readable ML protocol;
- create dataset split policy;
- create model registry schema;
- create experiment config schema;
- create cost ledger schema;
- create new ADRs for:
  - ML extension separate from zero-shot primary,
  - locked test policy,
  - model candidate selection,
  - feature caching,
  - HPO,
  - PEFT/full fine-tuning gating,
  - ensemble/stacking leakage prevention.

Gate:
Protocol hashes recorded; tests ensure original protocol unchanged.

## PHASE 2 — Canonical scoring pipeline repair

Goal:
One scientifically correct scoring implementation.

Tasks:
- exact 8192 window convention;
- assert invariants;
- forward + RC;
- raw scores retained;
- no hard-coded BRCA1 threshold;
- remove fake production confidence;
- unify scorer adapters;
- unify API variant schema;
- wire research API to real scorer via clean interface;
- preserve FakeScorer for tests only.

Gate:
Unit + scientific contract + one real Modal pilot.

## PHASE 3 — ML dataset and locked splits

Goal:
Create reproducible train/validation/test manifests.

Tasks:
- audit temporal cohort;
- create/validate supervised training source;
- prevent normalized-ID overlap;
- group by gene where required;
- freeze split hashes;
- class/gene/subgroup reports;
- leakage test suite.

Gate:
Zero overlap, deterministic rebuild, QC report PASS.

## PHASE 4 — Modal compute foundation

Goal:
Reliable, cost-aware model execution.

Tasks:
- canonical Modal app/service layout;
- persistent model/checkpoint cache;
- persistent feature/prediction cache;
- batch execution;
- retries/idempotence;
- GPU telemetry;
- cost ledger;
- smoke tests;
- no default paid tests.

Gate:
Tiny reproducible inference + cache hit + cost record.

## PHASE 5 — Model registry and adapter framework

Goal:
Common interface for multiple predictors.

Tasks:
- Evo2 adapter;
- feasibility review for Nucleotide Transformer;
- feasibility review for Caduceus;
- GPN track;
- CADD/PhyloP;
- AlphaMissense subset;
- choose 2–3 feasible foundation/specialized models for full benchmark;
- record exclusions.

Gate:
Each included model passes tiny parity/smoke and produces a provenance record.

## PHASE 6 — Multi-model zero-shot benchmark

Goal:
Establish untouched baselines.

Tasks:
- batch score development cohort;
- batch score locked evaluation cohort only according to protocol;
- cache raw outputs;
- harmonize score direction metadata;
- compute coverage and runtime;
- generate baseline tables/figures.

Gate:
No training yet; benchmark reproducible from registry.

## PHASE 7 — Embedding and representation extraction

Goal:
Create reusable frozen features.

Tasks:
- determine supported embedding APIs;
- choose candidate layers without locked-test tuning;
- extract ref/alt embeddings;
- calculate differences/similarity;
- store compact features with hashes;
- test deterministic shapes/dtypes;
- measure storage cost.

Gate:
Feature cache complete and verified for development set; selected test extraction rule frozen.

## PHASE 8 — Downstream supervised models

Goal:
Train models on frozen features.

Tasks:
- logistic regression;
- tree model;
- MLP;
- train curves;
- early stopping;
- imbalance strategy;
- seeded runs;
- validation metrics.

Gate:
At least one trained model beats trivial/random baselines on validation and all artifacts register.

## PHASE 9 — Hyperparameter optimization

Goal:
Systematically optimize without test leakage.

Tasks:
- Optuna storage;
- bounded search spaces;
- pruning;
- trial registry;
- cost/time measurements;
- best config selected from validation only;
- HPO plots.

Gate:
Study reproducible; chosen config frozen.

## PHASE 10 — Fine-tuning / PEFT experiments

Goal:
Measure whether model adaptation improves over frozen features.

Tasks:
- official training-path verification;
- tiny smoke overfit;
- PEFT/smaller model first;
- selected Evo2 experiment only if budget/stack permit;
- train/validation curves;
- failure recovery;
- checkpoint manifests;
- catastrophic-forgetting sanity checks as relevant.

Gate:
At least one valid adaptation experiment completed OR formally deferred with compute evidence.
No fake requirement that adaptation must improve.

## PHASE 11 — Ensemble and meta-classifier

Goal:
Exploit complementary errors.

Tasks:
- error overlap;
- agreement;
- correlation;
- choose candidates by validation;
- mean/weighted/vote/stack;
- OOF stacking;
- meta-classifier;
- locked ensemble config.

Gate:
No leakage; ensemble comparison registered.

## PHASE 12 — Calibration and abstention

Goal:
Make probabilistic output honest.

Tasks:
- Platt;
- isotonic sensitivity;
- reliability;
- Brier/NLL/ECE;
- abstention thresholds chosen on validation;
- risk-coverage.

Gate:
Calibrator never sees locked-test labels.

## PHASE 13 — Ablations and robustness

Goal:
Show what matters.

Tasks:
- context length;
- orientation;
- center shift;
- feature removal;
- model removal;
- calibration removal;
- subgroup analyses;
- learning curves;
- seed robustness.

Gate:
Predeclared matrix complete or each skipped cell justified.

## PHASE 14 — Statistical final evaluation

Goal:
Run final locked evaluation once under frozen configuration.

Tasks:
- verify protocol hash;
- verify split hash;
- verify config freeze;
- run final predictions;
- compute metrics/CIs;
- paired comparisons;
- multiple-comparison correction;
- save immutable final result bundle.

Gate:
No post-test tuning. Any later change creates a new exploratory version.

## PHASE 15 — Batch research pipeline

Goal:
Production-quality research batch execution.

Tasks:
- CSV/VCF ingest;
- validation;
- queue;
- resumability;
- partial failure;
- progress;
- result export;
- cost estimate before submission;
- sample batch demo.

Gate:
Kill/restart recovery test passes.

## PHASE 16 — Research workbench UI

Goal:
Expose the actual ML contribution.

Tasks:
Implement all required dashboard areas and connect them to registered outputs.
No result hardcoding.

Gate:
Frontend test/build/E2E pass; demo works without hidden manual edits.

## PHASE 17 — Figures, tables, report artifacts

Goal:
Generate panel/paper-quality material automatically.

Tasks:
- figures from registry;
- tables from registry;
- methods summary;
- limitations;
- compute/cost summary;
- model card-like provenance;
- export bundle.

Gate:
Delete figures and regenerate them from commands; hashes stable where deterministic.

## PHASE 18 — Security, reproducibility, clean-room

Goal:
Prove another machine/agent can reproduce.

Tasks:
- secret scan;
- clean clone;
- dependency install;
- unit suite;
- frontend build;
- protocol verification;
- small CPU reproduction;
- gated Modal smoke;
- figures regeneration;
- registry verification.

Gate:
Documented clean-room PASS.

## PHASE 19 — Final release gate

Goal:
Freeze project for academic review.

Tasks:
- final phase ledger;
- final project state;
- known limitations;
- README;
- architecture diagram;
- experiment summary;
- demo path;
- tag/release if user wants;
- never claim unrun experiments.

Gate:
All P0/P1 requirements complete or explicitly justified.

---

# 20. REQUIRED COMMAND SURFACE

Build or normalize a small set of commands, preferably Make targets or documented CLI:

- `make bootstrap`
- `make validate`
- `make test`
- `make test-scientific`
- `make web-check`
- `make data-qc`
- `make modal-smoke`
- `make benchmark-zero-shot`
- `make extract-features`
- `make train`
- `make hpo`
- `make finetune-smoke`
- `make ensemble`
- `make evaluate`
- `make figures`
- `make clean-room`

Names may differ if existing Makefile conventions are stronger. There must be one documented
control surface.

---

# 21. RESULT REGISTRY

Every experiment must have:

- `run_id`
- `experiment_family`
- `status`
- `started_at`
- `completed_at`
- `git_commit`
- `protocol_hash`
- `dataset_manifest_hash`
- `split_manifest_hash`
- `model_name`
- `checkpoint`
- `model_revision`
- `model_source`
- `license_record`
- `preprocessing_version`
- `feature_version`
- `config`
- `seed`
- `hardware`
- `GPU`
- `runtime_seconds`
- `estimated_cost_usd`
- `measured_cost_usd` if available
- `metrics`
- `artifact_paths`
- `failure_reason`
- `notes`

Experiment outputs should be append-only or immutable once marked FINAL.

---

# 22. FAILURE POLICY

Failures are data.

If:
- a model cannot install,
- a checkpoint exceeds memory,
- fine-tuning diverges,
- ensemble does not improve,
- HPO overfits,
- a comparator has missing coverage,

record it.

Do not conceal negative results.
Do not silently change the experiment until it passes.
Create a new run/config and preserve the failed run metadata.

---

# 23. COMPLETION DEFINITION

The project is complete when:

- original zero-shot benchmark remains preserved;
- ML-extension protocol is frozen and reproducible;
- canonical scoring is correct;
- train/validation/test split leakage tests pass;
- multiple models are benchmarked or infeasibility is rigorously documented;
- frozen representation training is implemented;
- HPO is implemented and evidenced;
- at least one fine-tuning/adaptation experiment is completed or formally compute-deferred;
- ensemble methods are evaluated correctly;
- calibration/abstention are implemented;
- ablation/robustness/error analyses are present;
- figures/tables derive from registered outputs;
- Modal spending is controlled;
- batch analysis works;
- research dashboard displays real registered results;
- tests pass;
- clean-room reproduction passes;
- documentation is sufficient for another coding agent to continue without chat history.

Start at **Phase 0**. Do not skip directly to model training.


# EvoVariant-TR

EvoVariant-TR is research software for a frozen temporal benchmark of genomic
variant-effect scores. The project preserves the original zero-shot Evo 2
estimand and adds a separately controlled ML-extension surface for future
representations, classical models, calibration, ensembling, and robustness
experiments.

> **Research-only boundary:** this repository does not provide a clinical
> diagnosis, treatment recommendation, or patient-level risk estimate. Raw
> sequence signals and any future calibrated study probabilities are meaningful
> only under their registered protocol and evidence stage.

## Current verified status

The current branch is `research/evovariant-tr`. The project-control state is
`BLOCKED / PARTIAL` at the final release gate. The free/local engineering
surfaces are reproducible, but the scientific execution gates are intentionally
closed:

| Area | Current evidence |
|---|---|
| Frozen protocol and ML-extension control plane | PASS; the original protocol hash is preserved. |
| Phase 3 data and splits | PASS for the ML extension under dated `ML-DEV-001`/`ML-DEV-002`; authoritative locked cohort is 946 (536 B/LB, 410 P/LP), with independent GRCh38 validation and zero unresolved mismatches. |
| Model registry and final Phase 5 roster | Seven schema-valid candidate manifests; the final roster separates Evo2 raw scoring, Nucleotide Transformer/Caduceus embedding tracks, CADD/PhyloP public CPU comparators, deferred GPN, and subset-only AlphaMissense. |
| Modal | Authorized Evo2 7B H100 pilot passed a real cache miss and equivalent cache hit; workspace billing is recorded, with no exact per-request invoice asserted. |
| Experiment registry | Nine completed `PRELIMINARY` runs are hash-verified and tracked through small summaries; no `FINAL` run is registered. |
| Research workbench | Frontend build and four browser tests PASS; the read-only registry tab displays preliminary run metadata while scientific panels remain evidence-gated. |
| Figures and tables | Final registry-driven manifest is `BLOCKED` with 9/19 figure families and 9/11 applicable tables sourced from the development subset; the fine-tuning table is explicitly `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` because Phase 10 is deferred, and a separate non-promotable preliminary bundle contains 18 development-stage outputs. |
| Spend | The bounded Evo2 development prefix used a `$4.698582` H100 wall-time estimate and stopped at a `$4.75` safety reserve under the `$5.00` cap; workspace billed cost is `$0.00` and per-request measured USD is unavailable. |

The existing 2,848-row Evo2 prefix and all derived CPU results remain `PRELIMINARY`; they are not
the formal model-selection sample. The no-spend `ML-DEV-BUDGETED-001` amendment freezes a
4,000-record subset from the 239,992-record development population: 3,199 TRAIN and 801
VALIDATION, with 3,226 negative and 774 positive rows, 1,927 unique genes, zero
TRAIN/VALIDATION gene overlap, zero locked-test overlap, and 56 IDs overlapping the old prefix
for cache accounting only. The old prefix audit concludes `NOT_ESTABLISHED` for
representativeness. The formal manifests, QC, hashes, and cost plan are in
`research/ml_extension/splits/formal_budgeted_20260921/`.

The authoritative execution state is maintained in
[`CODEX_MASTER_PROMPT.md`](CODEX_MASTER_PROMPT.md),
[`docs/agent/PROJECT_STATE.md`](docs/agent/PROJECT_STATE.md),
[`docs/agent/PHASE_LEDGER.md`](docs/agent/PHASE_LEDGER.md), and
[`docs/agent/DECISIONS.md`](docs/agent/DECISIONS.md). Historical milestone
reports under `docs/project/` are retained as history and are not a substitute
for the current ML-extension gate.

## Quick start: free local validation

The default setup and validation path does not install CUDA or download model
weights.

```bash
make bootstrap
cd apps/web && npm ci && cd ../..
make validate
make web-check
make web-e2e
```

Useful additional checks are:

```bash
make protocol-verify
make ml-protocol-verify
make schema-verify
make model-registry-verify
make registry-verify
make test-scientific
make test-e2e
make figures
make phase3-audit
make phase3-freeze
```

At the verified current baseline, `make validate` passes 703 tests with 33
deselected and 95.02% coverage. The scientific tier passes 7 tests with 1
explicit skip, the API/E2E tier passes 14 tests with 1 explicit skip, and
`make web-e2e` passes 4 local Playwright tests. The exact evidence and warnings
are recorded in the project-control files.

## What the project measures

The frozen primary estimand is:

> Among unique normalized germline GRCh38 SNVs recorded as VUS in the fixed
> historical ClinVar release at t0 and later receiving a definitive B/LB or
> P/LP classification meeting the prespecified review-status gate at t1, how
> well does a frozen zero-shot Evo 2 allele-likelihood score distinguish the
> direction of that later resolution?

The primary protocol fixes:

- t0: ClinVar `variant_summary` archived for 2025-01-02;
- t1: ClinVar `variant_summary` archived for 2026-08-06;
- assembly: GRCh38;
- unit: unique normalized biallelic A/C/G/T germline SNV;
- t1 outcomes: P/LP versus B/LB with the primary review-status gate;
- sequence context: exactly 8,192 bases;
- score: forward and reverse-complement raw components retained, with
  `delta_primary = (delta_fwd + delta_rc) / 2`;
- calibration and threshold choices: never fit using locked-test labels.

The Phase 3 archives are hash-verified. Their current recomputation yields
1,402,895 unique valid t0 VUS IDs and 946 final temporal records (536 B/LB,
410 P/LP). The validation-only handoff target was 1,403,225 and 1,024. The
difference is documented and has not been tuned away. The exact historical identity set was
not recoverable, so `ML-DEV-001` accepts the reproducible 946-record cohort for the ML extension
only; the original zero-shot study remains historical evidence. `ML-DEV-002` freezes the Broad
GATK hg38/v0 reference and its hashes for independent base validation. The pre-Phase-6
checkpoint is complete, but no full model scoring or embedding extraction is authorized until a
fresh scope-specific approval is recorded.

## Architecture

```mermaid
flowchart LR
    P[ Frozen protocol ] --> C[ ML control plane ]
    T0[ ClinVar t0 archive ] --> D[ Phase 3 audit and split builder ]
    T1[ ClinVar t1 archive ] --> D
    C --> R[ Model registry ]
    D --> G{ Data and model gates }
    R --> G
    G -->|future authorized run| M[ Modal Evo 2 execution ]
    M --> E[ Immutable experiment registry ]
    E --> F[ Registry-driven figures and tables ]
    E --> W[ Next.js research workbench ]
    W --> U[ Research-only user surface ]
```

The current repository contains the contracts and fail-closed execution
scaffolding. A tiny authorized Evo2 deployment and remote cache artifact now
exist, but they are engineering-gate evidence only and do not constitute a
cohort benchmark or scientific result.

## Repository map

```text
.
├── CODEX_MASTER_PROMPT.md       # authoritative execution instruction
├── COMMAND_REFERENCE.md         # free/gated command reference
├── Makefile                     # project control surface
├── docs/agent/                  # persistent state, decisions, ledger, runbook
├── research/protocol/           # frozen original protocol and deviation log
├── research/ml_extension/       # additive ML protocol, model registry, split policy
├── research/schemas/             # strict JSON Schemas
├── experiments/registry/        # append-only preliminary/final run records
├── src/evovariant_tr/           # typed research and control-plane package
├── apps/web/                    # Next.js research workbench
├── evo2_scorer_app.py           # canonical Modal entrypoint; pilot evidence is in artifacts/
├── scripts/                     # validation, manifest, registry, and operational tools
├── tests/                       # unit, contract, integration, scientific, API/E2E, Modal
└── data/                        # local/ignored archives and derived Phase 3 outputs
```

## Research workbench

Run the frontend from `apps/web` after installing its dependencies:

```bash
cd apps/web
npm run dev -- --port 3001
```

Open `/analysis` to inspect the evidence-gated workbench. It exposes all 14
required areas:

- Overview;
- Single Variant Research Analysis;
- Temporal VUS Explorer;
- Model Benchmark;
- Representation / Layer Analysis;
- Training & Hyperparameter Experiments;
- Fine-Tuning Experiments;
- Ensemble Analysis;
- Calibration & Abstention;
- Robustness & Ablation;
- Error Analysis;
- Batch VCF/CSV;
- Methods & Provenance;
- Experiment Registry.

The current UI can load frozen protocol metadata and can render raw research
signals only when an explicitly configured real scorer serves them. It does not
fall back to `FakeScorer`, derive clinical labels, invent metrics, or mark
downstream areas ready because a planned run exists. The Experiment Registry
tab reads safe metadata from `/api/registry`; it shows `PARTIAL` while completed
`PRELIMINARY` metadata exists without a promoted `FINAL` run. Downstream
scientific panels remain explicitly blocked until their own evidence gates pass.

## Data and reproducibility

The local archive-backed Phase 3 command is:

```bash
make data-qc
```

It rebuilds ignored record-level outputs under
`data/derived/ml_extension/phase3/` and validates deterministic split and
leakage invariants. The current split manifest hash is
`96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`, and its
content split hash is
`bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`.

The raw archives are local, ignored data. Their identity is recorded in:

- `research/data_manifests/clinvar_t0.json`;
- `research/data_manifests/clinvar_t1.json`;
- `research/ml_extension/splits/phase3_manifest_summary.json`.

The summary is the reviewable source of truth for the discrepancy, deviations,
reference validation, and authoritative cohort. It does not authorize a model
run by itself; Phase 6/7 execution still requires the separate approval and
checkpoint gates recorded in the project-control files.

## Experiment registry and figures

Every future run must be registered with protocol, git, dataset/split, model,
license, configuration, hardware, runtime/cost, metrics, artifact, and failure
metadata. The registry is append-only, terminal states are final, and completed
output hashes are recomputed by:

```bash
make registry-verify
```

The Section 21 metadata contract is implemented in
`src/evovariant_tr/registry.py` and
`research/schemas/experiment_run.schema.json`. The current registry contains
nine completed `PRELIMINARY` run records and no `FINAL` record. The bounded
development summaries and figure-source inputs are generated and registered by
`scripts/register_development_subset_results.py`.

Figure and table input discovery and export are deliberately registry-driven:

```bash
make figures
```

This writes a deterministic metadata manifest under the ignored
`research/runs/` directory and a bundle manifest under
`research/figures/bundle_manifest.json`. The Phase 17 contract covers all 19
required figure families and 12 declared tables. The final renderer reports
`BLOCKED`, removes only outputs listed by the prior final bundle manifest, and
produces no final scientific figures, tables, placeholder metrics, or inferred
values while nine mandatory source families are missing and no completed `FINAL`
run is registered. The conditional `fine_tuning_summary` table is explicitly
`NOT_APPLICABLE_WITH_DOCUMENTED_REASON` under the recorded Phase 10
`DEFERRED_BY_COMPUTE` decision; this does not waive any mandatory core source.
`make figures` also writes a separate `PARTIAL` manifest at
`research/figures/preliminary/preliminary_bundle_manifest.json`; it contains 9
development-stage figure outputs and 9 tables (18 files total), is marked
`evidence_stage: PRELIMINARY` and `promotable: false`, and must not be treated
as final evidence. When registered inputs eventually make the final manifest
`READY`, the final bundle renderer emits hash-addressed SVG figures,
JSON tables, methods, limitations, cost, and model-provenance artifacts under
`research/figures/bundle/`.

## Batch planning and local recovery contract

Phase 15 now has a free local planning and injected-scorer contract for label-free
CSV/VCF input. It validates GRCh38 biallelic SNVs, hashes the input, persists an
immutable model/revision/context/orientation plan, and supports hash-verified,
resumable shards plus deterministic export. Planning does not construct a model,
call Modal, attach labels, or create scientific predictions:

```bash
make batch-run \
  BATCH_INPUT=examples/batch/variants.csv \
  BATCH_MODEL_REVISION=4b509ec2a22d6de472659f908bcb0714265ad3a7
```

The sample command writes a `PLANNED` status under ignored
`research/runs/phase15_batch_plan/`. Remote batch parity, kill/restart evidence,
full-cohort execution, and any paid batch workload remain separately blocked and
require a new exact-scope approval.

## Budgeted development design (no-spend checkpoint)

Before any new scoring, run the local audit/design command:

```bash
make budgeted-study-design
```

It reconstructs the old prefix selection, compares available metadata against all 239,992
development records, freezes `ML-DEV-BUDGETED-001`, and writes idempotent manifests and QC. It
does not read model predictions for selection and does not invoke Modal. The measured-rate cost
plan is `$6.506744` for 3,944 new Evo2 variants, `$0.378539` for NT, `$0.226398` for Caduceus,
and `$7.111681` total. The previous `$5.00` approval is exhausted; the expected reserve is
unavailable until a fresh exact-scope approval, so the command must be completed and reviewed
before any paid workload is considered.

## Modal and paid compute

The canonical identity is app `evovariant-tr`, volume `hf_cache`, H100, the
pinned NGC PyTorch image, and Evo2 revision
`4b509ec2a22d6de472659f908bcb0714265ad3a7`. Under the dated user approval,
deployment v3 (`phase2-pilot-20260921-r1`) loaded `evo2_7b` and verified one
real prediction-cache miss plus an identical cache hit for
`GRCh38:chr10:100065200:C>T`. The raw output is research-only and carries no
clinical classification.

```bash
make modal-smoke
```

This remains a no-spend preflight for fresh environments. The completed pilot
evidence is recorded separately in
`artifacts/modal/phase2_phase4_pilot_20260921_success.json`; its superseded
chromosome-prefix failures are preserved alongside it.

Paid execution requires the explicit acknowledgement
`EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` and the project-specific approval
gates described in `docs/agent/MODAL_COMPUTE_POLICY.md`. The current
`phase6_phase7_development_20260921.json` approval allowed only the bounded
TRAIN/VALIDATION Evo2 prefix and local CPU Phases 8, 9, 11, 12, and 13; it did
not authorize full-cohort inference, locked-test evaluation, fine-tuning,
deployment, release, or publication. That approval is exhausted at the
recorded safety stop, so any further paid work requires a new exact-scope
approval.

## Phase status

The dependency-ordered phase decisions are maintained in
[`docs/agent/PHASE_LEDGER.md`](docs/agent/PHASE_LEDGER.md). In brief:

- Phases 0 and 1 are complete;
- Phase 2 and Phase 4 pass their engineering gates with the corrected remote
  Evo2 miss/hit evidence;
- Phase 3 passes for the ML extension under `ML-DEV-001`/`ML-DEV-002`, with a
  946-record authoritative locked cohort and independent reference validation;
- Phase 5 has a final separated roster: Evo2 raw score, Nucleotide
  Transformer/Caduceus embedding tracks, CADD/PhyloP public CPU comparators,
  deferred GPN, and subset-only AlphaMissense;
- Phase 6/7 and Phases 8/9/11/12/13 are partial development-subset evidence
  only; no full-cohort or locked-test claim is made;
- `ML-DEV-BUDGETED-001` is a frozen no-spend formal-study design only; no new Evo2,
  Nucleotide Transformer, or Caduceus scoring has run;
- Phase 10 is formally deferred by compute, and Phase 14/15 remain scientifically
  blocked; Phase 15 has a local label-free planning/recovery contract but no
  authorized remote batch execution;
- Phase 16's frontend/build/browser engineering gate passes and its read-only
registry tab is connected to nine preliminary runs, while its scientific
  result panels remain evidence-gated;
- Phase 17's registry-driven manifest is deterministic with partial sources but
  remains blocked and contains no scientific outputs;
- Phase 18's free clean-room gate passes, while full scientific and figure
  evidence remain unavailable;
- Phase 19 remains blocked and no release, tag, deployment, or publication is
  claimed.

## Legacy evidence boundary

The repository retains historical legacy application code, reports, and ignored
evaluation snapshots for auditability. They are not current ML-extension
results. In particular, the former BRCA1 threshold/confidence classifier and
old Modal endpoint identity must not be used as evidence for the frozen temporal
benchmark. Current code fails closed when a real scorer or registered artifact
is unavailable.

## Responsible use

ClinVar review stars are a review-status proxy, not biological certainty. The
benchmark is conditional on eventual historical resolution and does not estimate
whether every VUS will be reclassified, when it will be reclassified, patient
diagnosis, treatment, clinical management, or causal pathogenicity.

Never present a raw model score, calibrated study probability, or empty-state
status as a clinical conclusion. Preserve protocol hashes, data hashes, model
identity, evidence stage, failure records, and cost records for every future
run.

## References

- [Frozen original protocol](research/protocol/PROTOCOL.md)
- [ML-extension protocol](research/ml_extension/PROTOCOL.md)
- [Command reference](COMMAND_REFERENCE.md)
- [Project state](docs/agent/PROJECT_STATE.md)
- [Phase ledger](docs/agent/PHASE_LEDGER.md)
- [Decisions](docs/agent/DECISIONS.md)
- [Testing and validation](docs/agent/TESTING_AND_VALIDATION.md)
- [Modal compute policy](docs/agent/MODAL_COMPUTE_POLICY.md)
- [Evo2 repository](https://github.com/ArcInstitute/evo2)
- [UCSC Genome Browser API](https://api.genome.ucsc.edu)
- [NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)

# Decisions — EvoVariant-TR ML Extension

This file is append-only in spirit. Change a decision by adding a new superseding entry,
not by erasing history.

## D-001 — Preserve the original frozen zero-shot protocol
Status: ACCEPTED

The original temporal Evo2 zero-shot study remains untouched as the baseline scientific
study. Training/fine-tuning/ensemble work is a separate ML-extension protocol.

Reason:
Retrospective tuning of the original test outcomes would invalidate the original zero-shot
estimand.

## D-002 — Modal is the default GPU provider
Status: ACCEPTED

Modal will host GPU inference, embedding extraction, selected training/fine-tuning, and
research serving. CPU-capable work remains local where practical to preserve credits.

## D-003 — Cache expensive foundation-model outputs
Status: ACCEPTED

Scores and embeddings are computed once per immutable `(model, checkpoint, preprocessing,
variant, orientation, context, layer)` key and reused by downstream ML/HPO.

## D-004 — HPO is performed on frozen features where possible
Status: ACCEPTED

Repeated foundation-model inference per trial is forbidden unless the hyperparameter
actually changes foundation-model computation (e.g. context or layer extraction).

## D-005 — Full Evo2 fine-tuning is not a completion requirement
Status: ACCEPTED

A scientifically valid project can be complete with frozen Evo2 representations,
trainable downstream classifiers, and ensembles. Full large-model fine-tuning is attempted
only if official tooling, stability, and compute budget allow.

## D-006 — Ensemble selection uses error diversity, not accuracy similarity
Status: ACCEPTED

Candidates require validation performance plus complementary error evidence.

## D-007 — Final figures are generated from registry outputs
Status: ACCEPTED

No presentation number is manually inserted if it purports to be an experimental result.

## D-008 — Research-only language
Status: ACCEPTED

Outputs are computational research evidence, not diagnosis or clinical certainty.

## D-009 — Model list is feasibility-gated
Status: ACCEPTED

Preferred candidates are Evo2, Nucleotide Transformer, Caduceus, and appropriate GPN
variants, with CADD/PhyloP and AlphaMissense subset as comparators. The exact final list may
change only after an official-source feasibility/license/compute review.

## D-010 — Locked test policy
Status: ACCEPTED

Final test labels are not used for configuration selection. Post-test changes produce a
new exploratory version and may not be promoted as the original confirmatory result.

## D-011 — Canonical current Modal application identity
Status: ACCEPTED
Date: 2026-09-21
Supersedes: the unresolved `evovariant-tr-v2` proposal/confirmation in historical ADR/project-identity text for the current ML-extension worktree

Context:
Phase 0 found three competing identity states: the active root Modal entrypoint and cost
policy use `evovariant-tr`; `RuntimeConfig`, ADR 0008, and the historical project identity
use `evovariant-tr-v2`; legacy backend/evaluation assets use `variant-analysis-evo2`. The
current root entrypoint is not yet a verified deployment, and this decision does not authorize
deployment or paid compute.

Decision:
Use `evovariant-tr` as the canonical new Modal application/environment identity for the
current EvoVariant-TR ML-extension worktree. Treat `variant-analysis-evo2` as legacy and
forbidden for new infrastructure. Treat `evovariant-tr-v2` as stale historical documentation
until later control-plane reconciliation updates it additively with fresh evidence. Do not
assume the currently referenced `hf_cache` volume is an approved dedicated cache; resolve
the volume identity separately before any paid deployment.

Alternatives:
- Keep `evovariant-tr-v2`: rejected for the current worktree because active code, approval
  policy, and the root app already use `evovariant-tr`.
- Reuse `variant-analysis-evo2`: rejected by the existing cost/security policy and legacy
  evidence boundary.

Consequences:
Later phases must reconcile `RuntimeConfig`, ADR/project-identity references, cache volume,
frontend environment, and deployment manifests without silently claiming that a deployment
exists. No code or deployment was changed in Phase 0.

Validation:
`evo2_scorer_app.py`, `src/evovariant_tr/cost_policy.py`, `artifacts/approvals/full_run_approval.json`,
and the identity search recorded in `docs/agent/BASELINE_AUDIT.md`.

## D-012 — Freeze the ML extension as an additive control plane
Status: ACCEPTED
Date: 2026-09-21

Context:
The original temporal zero-shot protocol is immutable, while the ML extension needs
machine-readable rules for development data, model selection, features, HPO, and
locked-test sequencing.

Decision:
The ML extension is governed by `research/ml_extension/protocol.yaml` and
`split_policy.yaml`. These files are additive and carry the exact SHA-256 of the
original `research/protocol/protocol.yaml`. No extension choice may rewrite or
reinterpret the original protocol.

Consequences:
Extension artifacts must identify their extension protocol version separately from
the original protocol version. A protocol-hash check is part of the control-plane
command and contract tests.

Validation:
`make ml-protocol-verify` equivalent CLI invocation passed; original protocol hash
remained `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`.

## D-013 — Use strict schemas for extension manifests and cost records
Status: ACCEPTED
Date: 2026-09-21

Context:
The existing registry schema predates the ML-extension model, split, experiment, and
cost metadata requirements.

Decision:
Additive JSON Schemas govern model manifests, split manifests, experiment configs, and
cost-ledger entries. Unknown fields are rejected at schema boundaries, and schema
documents are validated as Draft 2020-12 documents.

Consequences:
Future phases must register provenance, capability, split, and cost metadata before
promoting an experiment result. The checked-in experiment template must conform to its
schema.

Validation:
The four extension schemas and `experiments/templates/experiment_config.yaml` pass
contract validation.

## D-014 — Model candidate inclusion is evidence-gated
Status: ACCEPTED
Date: 2026-09-21

Context:
The handoff names several possible predictors, but no current source, license,
checkpoint revision, input contract, or runtime evidence was verified for all of them.

Decision:
Every candidate begins as planned/unverified. Inclusion requires official-source,
license, checkpoint/revision, input, score-direction, hardware, capability, and tiny
smoke evidence. Unsupported candidates are recorded as `INFEASIBLE` or `UNAVAILABLE`,
never silently substituted.

Consequences:
The benchmark may contain fewer than the preferred candidate count when runtime or
license evidence is unavailable. Evo2 remains required and cannot be replaced by a
synthetic result.

## D-015 — Cache identity includes all scientific and model dimensions
Status: ACCEPTED
Date: 2026-09-21

Context:
Downstream HPO and ensemble work must not trigger repeated foundation-model inference
or accidentally reuse incompatible outputs.

Decision:
Cache keys include model, checkpoint, revision, preprocessing, assembly, context,
orientation, layer, and normalized variant ID. Raw scores and embeddings retain shape,
dtype, and content hashes.

Consequences:
Any mismatch is a cache miss. Cache records are provenance artifacts rather than an
opaque performance optimization.

## D-016 — HPO and adaptation are validation-only and resource-gated
Status: ACCEPTED
Date: 2026-09-21

Context:
The locked temporal cohort must remain untouched during model and configuration
selection, and full Evo2 adaptation may exceed the available compute budget.

Decision:
HPO, early stopping, calibration, abstention, and ensemble selection use development
training/validation data only. Fine-tuning proceeds from frozen features to PEFT and
then full fine-tuning only when official tooling, a smoke test, measured cost, and an
approval gate justify it. Compute deferral is a valid recorded outcome.

Consequences:
Viewing locked-test labels cannot trigger iterative tuning. Failed or deferred
adaptation remains in the registry as evidence.

## D-017 — Stacking must use out-of-fold development predictions
Status: ACCEPTED
Date: 2026-09-21

Context:
An ensemble meta-classifier trained on in-sample base predictions would leak base-model
training outcomes and overstate performance.

Decision:
Stacking uses out-of-fold train predictions, validation-only member selection and
weights, and a frozen configuration before locked-test evaluation. Error overlap and
disagreement are reported before ensemble selection.

Consequences:
An ensemble is not promoted merely because its aggregate accuracy is similar to a
member; complementary validation errors are required.

## D-018 — Canonical research scoring is raw, orientation-aware, and fail-closed
Status: ACCEPTED
Date: 2026-09-21

Context:
The pre-handoff API, Modal adapter, and frontend accepted different variant field names and
mixed a synthetic scorer with BRCA1-derived threshold/confidence behavior. The root window
formula also did not guarantee the frozen 8,192-base context.

Decision:
All research scoring requests normalize to a canonical GRCh38 payload with a 1-based
position, explicit reference and alternate alleles, and an explicit orientation policy.
Scoring must validate exact context length, coordinates, reference-allele agreement, SNV
constraints, and orientation. The result retains raw forward and reverse-complement scores,
their deltas, primary delta, and disagreement. It must not claim a clinical prediction,
confidence, or pathogenic/benign threshold classification.

Consequences:
Synthetic scoring remains test-only. The default API is unavailable until an explicit scorer
is configured. Frontend and proxy consumers can share one contract, while research artifacts
retain enough raw information to audit orientation and downstream transformations.

Validation:
`make validate`, canonical scoring/API contract tests, the frontend legacy-classification
scan, and `git diff --check` passed in the Phase 2 checkpoint.

## D-019 — Real Modal pilot is a mandatory evidence gate
Status: ACCEPTED
Date: 2026-09-21

Context:
The master prompt requires one real Modal pilot before treating the compute foundation or
Evo2 path as operational. Local fakes, static source inspection, and unit tests cannot prove
account access, image build, model loading, GPU inference, or measured cost.

Decision:
Do not mark Phase 2 or Phase 4 compute gates PASS without a real, reproducible Modal pilot
with explicit account/authentication evidence, the canonical app/cache identity, a tiny
validated request, and a cost record. If CLI/authentication or paid-compute acknowledgement
is unavailable, record the phase as BLOCKED and continue only with independent local work.

Consequences:
No GPU spend, deployment, model download, or “pilot passed” claim may be inferred from the
local test suite. A later authorized run must append exact command/output, artifact hashes,
runtime identity, and measured spend before closing the gate.

Validation:
The no-spend preflight now reports Modal CLI/account authentication, but no remote pilot or
paid-compute acknowledgement is present; the Phase 2 ledger therefore remains `BLOCKED`.

## D-020 — ClinVar VCF-normalized fields define the split identity
Status: ACCEPTED
Date: 2026-09-21

Context:
The official `variant_summary` archives contain `na` in the legacy
`ReferenceAllele`/`AlternateAllele` columns for many GRCh38 SNV rows, while the corresponding
VCF-normalized alleles and position are present in `ReferenceAlleleVCF`, `AlternateAlleleVCF`,
and `PositionVCF`. Using the legacy fields collapses distinct SNVs and cannot satisfy the
frozen A/C/G/T unit.

Decision:
For valid GRCh38 biallelic SNVs, Phase 3 uses the VCF-normalized fields when present and
falls back to the legacy fields only for older fixtures that lack those columns. The
canonical split identity is `GRCh38:<chromosome>:<position_1based>:<reference>><alternate>`
with uppercase alleles and a normalized chromosome prefix.

Consequences:
The parser, fast cohort path, calibration path, and ML split builder now share the same
identity semantics. Historical ignored results built from legacy allele fields are not treated
as current evidence and must be regenerated before scoring.

Validation:
The real t0/t1 archive audit, parser VCF-field unit test, split manifest schema validation,
and zero-overlap checks passed. Archive hashes match the checked-in data manifests.

## D-021 — Preserve the frozen QA discrepancy as evidence
Status: ACCEPTED
Date: 2026-09-21

Context:
The recomputed public archives do not reproduce every validation-only handoff checkpoint
count, even after correcting archive URL layout, VCF normalization, and the t0/t1 review-gate
interpretation.

Decision:
Record the exact recomputed counts, source hashes, structural invariants, and investigation
notes in `research/ml_extension/splits/phase3_manifest_summary.json`. Do not alter immutable
filters or select a normalization merely to force the historical target. Do not start model
scoring until the discrepancy is resolved or a dated deviation explicitly accepts the revised
cohort and its estimand impact.

Consequences:
Phase 3 can pass its structural leakage/QC gate, while downstream zero-shot and supervised
results remain blocked. Synthetic tests and historical ignored result files remain clearly
separate from current scientific evidence.

Validation:
The generated split manifest has zero normalized-ID overlap, zero train/validation gene
overlap, zero duplicate IDs, zero locked-test overlap, deterministic rebuild, and valid JSON
Schema conformance; the QA-count comparison remains documented as unresolved.

## D-022 — Use one canonical Modal execution identity and pinned Evo2 source
Status: ACCEPTED
Date: 2026-09-21

Context:
The handoff contained conflicting Modal app names, volume names, GPU defaults, and Evo2
references. An execution path that silently creates a new volume or tracks a moving source
revision would make cache and cost evidence non-reproducible.

Decision:
The active Modal identity is app `evovariant-tr`, existing volume `hf_cache` mounted at
`/root/.cache/huggingface`, H100, image `nvcr.io/nvidia/pytorch:24.07-py3`, and Evo2 repository
revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`. The app must fail closed when the named
volume is unavailable (`create_if_missing=False`). The Modal CLI preflight may verify local
installation and account authentication, but it cannot be treated as deployment or inference
evidence.

Alternatives:
Retain stale `evovariant-tr-v2`/A100/dedicated-volume values, create resources automatically,
or track an unpinned Evo2 branch. These were rejected because they obscure identity and cost.

Consequences:
All later model/cache/cost artifacts reference one explicit execution identity. A real pilot
still needs separate authorization and remote evidence; local configuration does not imply
that the app, volume, weights, or GPU function exists remotely.

Validation:
`make modal-smoke` reports `modal_installed: true` and `modal_authenticated: true` without
invoking a remote workload. Local config and deployment-guard tests pass.

## D-023 — Cache and cost evidence are first-class Phase 4 artifacts
Status: ACCEPTED
Date: 2026-09-21

Context:
Later benchmark, feature, HPO, ensemble, and batch phases must be resumable without mixing
results from different model revisions, preprocessing contracts, orientations, layers, or
variants. Missing prices or deferred work must not be represented as invented zeros.

Decision:
Cache identities include model, checkpoint, model revision, preprocessing revision, assembly,
context length, orientation, layer, and normalized variant ID. Cache writes are atomic and
payload/identity hashes are checked on read. Runtime telemetry records wall time, host, GPU
type, and optional CUDA peak memory. Cost ledger entries are append-only and permit null cost
fields for local, planned, failed, or deferred work; retryable external failures are bounded
and idempotent.

Consequences:
Cache hits are scientifically auditable rather than opaque optimizations. A phase cannot
claim measured cost from a plan or a preflight. Later remote runs must append actual runtime,
cache-hit, approval, and measured-cost evidence before their gate can pass.

Validation:
The Phase 4 test suite covers identity mismatch, payload tampering, atomic-write cleanup,
shard resume/retry behavior, CPU and CUDA-shaped telemetry, and negative cost constraints.
`make validate` passes with 591 tests and 95.21% coverage.

## D-024 — Model manifests are visible before inclusion, but adapters fail closed
Status: ACCEPTED
Date: 2026-09-21

Context:
The extension requires Evo2 plus feasible alternatives and specialized comparators, but a
candidate name or deterministic fixture implementation does not prove an official source,
license, checkpoint revision, input parity, score semantics, or runtime capability.

Decision:
Maintain one schema-validated manifest per candidate under
`research/ml_extension/models/`. Planned/deferred candidates remain visible for audit but are
not benchmark inputs. Only `INCLUDED` or `AVAILABLE` candidates with `VERIFIED` provenance may
pass the registry inclusion gate. The common adapter layer returns structured readiness and
raises `AdapterUnavailable` instead of downloading weights or returning synthetic scientific
scores. Evo2 remains required and receives a dedicated parity-aware adapter; all other current
candidates remain deferred until their official paths are verified.

Alternatives:
Treat the existing deterministic comparator hashes as scientific baselines, mark every named
candidate available from its repository URL, or silently omit infeasible candidates. These were
rejected because they would fabricate evidence or make exclusions unauditable.

Consequences:
Phase 5 can pass schema and provenance infrastructure while remaining `BLOCKED` on the model
inclusion gate. Zero-shot, embedding, and downstream results cannot be generated from the
current registry. Later authorized work must add a dated verified manifest and tiny smoke
artifact before using a candidate.

Validation:
`make model-registry-verify` reports seven valid manifests and zero included candidates;
registry/adapter tests cover duplicate IDs, schema failures, inclusion verification, readiness
states, provenance, and the no-download default adapter map.

## D-025 — Non-completed phase artifacts must be metric-free
Status: ACCEPTED
Date: 2026-09-21

Context:
The dependency-gated phases cannot execute scientific work while model, data, compute, or
authorization evidence is missing. A command that merely returns a non-zero exit or an empty
directory is difficult to audit and can be mistaken for a missing implementation.

Decision:
Every later-phase control-surface command writes a structured status artifact with phase,
family, blockers, inputs, and status. `BLOCKED`, `DEFERRED`, `NOT_RUN`, and `FAILED` artifacts
must contain no scientific metrics. Only an explicitly `COMPLETED` artifact may carry metrics.

Alternatives:
Write placeholder metric values, use an unstructured log only, or silently skip the phase.
These were rejected because they obscure the difference between unavailable evidence and a
negative result.

Consequences:
The research workbench and release ledger can display an honest empty state. Later authorized
runs must create a new completed immutable artifact rather than mutating a blocked record.

Validation:
`tests/unit/test_experiment_framework.py` covers metric rejection, atomic status writes, and
round-trip reads. The Phase 6–19 Make targets generate empty-metrics `BLOCKED` records.

## D-026 — CPU-only experiment contracts do not authorize scientific execution
Status: ACCEPTED
Date: 2026-09-21

Context:
The master prompt requires benchmark, feature, training, HPO, adaptation, ensemble,
calibration, robustness, batch, and figure work, but the current registry contains no included
model and the required compute/data gates are unresolved.

Decision:
Implement and test the deterministic contracts, freeze guards, leakage checks, and status
surfaces locally, while keeping all dependent execution phases blocked. Synthetic fixtures are
permitted only in unit tests and are never promoted to the result registry.

Alternatives:
Run deterministic comparator fixtures as if they were model outputs, use the locked cohort to
fill missing dependencies, or download unverified model weights. These were rejected because
they would change the estimand or fabricate model evidence.

Consequences:
Another agent can continue from explicit interfaces and failure artifacts without confusing
engineering readiness with scientific completion. Model inclusion, Modal authorization, and the
Phase 3 QA decision remain prerequisites for real outputs.

Validation:
Commit `7127fc7`; `make validate` passes with 610 tests and 95.34% coverage; all later-phase
status commands complete without scientific metrics.

## D-027 — The workbench renders registry state and evidence-gated empty states
Status: ACCEPTED
Date: 2026-09-21

Context:
The handoff asks for a research workbench covering 14 areas, but no completed ML-extension
result artifacts currently exist. A dashboard filled with example numbers would look complete
while violating the no-fabrication boundary.

Decision:
Expose all required areas in the top-level navigation. The single-variant surface may show raw
scorer/provenance fields from its API response; calibration, uncertainty, comparator, benchmark,
training, batch, figure, and registry panels show explicit blocked/pending states until their
registered artifacts exist. Protocol identity fields are loaded from `/api/protocol`.

Alternatives:
Hide unfinished areas, hard-code historical counts/metrics, or show clinical labels from raw
signals. These were rejected because the UI must expose actual ML work and preserve research-only
semantics.

Consequences:
The local UI is useful for reviewing project state without implying scientific results. A later
registry/API integration can populate the same panels without changing their evidence boundary.

Validation:
Commit `459ad11`; `tests/contract/test_frontend_workbench_contract.py`, changed-file ESLint,
`make web-check`, and a local production-server Playwright browser smoke passed. Automated
browser E2E and registered outputs remain explicit blockers.

## D-028 — Clean-room validation must not depend on ignored historical outputs
Status: ACCEPTED
Date: 2026-09-21

Context:
The legacy clean-room tests required `research/results/*.json`, but that directory is ignored
and contains historical snapshots that are not current ML-extension evidence. A genuine clone
therefore failed before validation even though the tracked Phase 3 manifest and control plane
were present.

Decision:
When ignored legacy results are present, the tests continue validating their JSON contracts.
When they are absent, clean-room checks use the tracked Phase 3 manifest summary and its
structural invariants instead. Generated Python package metadata under `src/evovariant_tr.egg-info`
is ignored rather than tracked, so dependency installation does not dirty a clean clone.

Alternatives:
Commit stale result snapshots, copy ignored files into every clean clone, or skip the checks
without a tracked fallback. These were rejected because they would make historical artifacts a
hidden scientific dependency.

Consequences:
The clean-room suite validates the current tracked evidence boundary and remains runnable from
a fresh clone. Historical result files may still be inspected locally, but they are not promoted
to the current registry.

Validation:
Commit `e52d7ab` updates the fallback checks and commit `421a7ef` untracks generated metadata.
A fresh clone at `421a7ef` passed `make validate`, `make web-check`, `make test-scientific`,
`make test-e2e`, protocol/schema/model-registry checks, and remained clean after installation.

## D-029 — The canonical frontend gate includes full lint and typed legacy API boundaries
Status: ACCEPTED
Date: 2026-09-21

Context:
The workbench surface already passed targeted lint, typecheck, build, and browser smoke checks,
but the full legacy `apps/web/src` tree still had 143 lint errors and 17 warnings. The Makefile
frontend gate also checked only TypeScript and the production build, so a clean build could leave
an unverified lint surface.

Decision:
Repair the existing frontend lint findings with behavior-preserving changes: explicitly handle
floating promises, declare React hook dependencies, remove unused imports, set the forward-ref
display name, use nullish/optional-safe access where required, and define response shapes for the
UCSC, NCBI Clinical Tables, NCBI E-utilities, and ClinVar JSON boundaries. Make `frontend-build`
run the repository-local ESLint entrypoint before TypeScript and the production build.

Alternatives:
Exclude legacy files, weaken the lint rules, add blanket disable comments, or leave the
Makefile gate partial. These were rejected because they would hide defects and make the local
frontend gate less reproducible.

Consequences:
The full frontend source tree is now statically clean and the canonical `make web-check` gate
covers lint, typecheck, and production build. This is engineering evidence only; it does not
authorize model downloads, paid compute, or scientific result generation.

Validation:
Commit `1d9cf43` implements the source/Makefile changes. Full ESLint passes with zero
errors/warnings; `make web-check` passes; `make validate` passes
with 610 tests, 33 deselected, and 95.34% coverage; `make test-scientific` passes 7 tests with 1
explicit skip; `make test-e2e` passes 14 tests with 1 explicit skip; protocol, schema, model
registry, registry, clean-room, and no-spend Modal preflight checks pass.

## Template for new decisions

### D-XXX — Title
Status: PROPOSED | ACCEPTED | SUPERSEDED | REJECTED
Date:
Supersedes:
Context:
Decision:
Alternatives:
Consequences:
Validation:

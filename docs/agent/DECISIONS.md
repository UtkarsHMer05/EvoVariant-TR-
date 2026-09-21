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
`make web-check`, and a local production-server Playwright browser smoke passed. The follow-up
commit `7f6c1b1` adds the committed three-test `make web-e2e` suite; registered outputs remain an
explicit blocker.

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
registry, registry, clean-room, and no-spend Modal preflight checks pass. A final clone from
`3f1496b` reproduced these gates and ended with a clean Git status.

## D-030 — Browser E2E covers the evidence-gated workbench without scientific fixtures
Status: ACCEPTED
Date: 2026-09-21

Context:
The workbench needed committed browser coverage for navigation, loading, blocked, and validation
journeys, but no real model output or registered scientific result exists yet. A browser suite
must not turn synthetic values into scientific evidence or require a paid scorer.

Decision:
Add a small Playwright suite under `apps/web/tests/e2e/` and a `make web-e2e` target. The suite
runs against a production Next server and verifies the 14-area navigation, the explicit blocked
Temporal VUS empty state, protocol metadata loading from `/api/protocol`, and client-side allele
validation that exits before a scorer request. The target installs only the local Chromium test
browser and never invokes Modal, model weights, or a scoring service.

Alternatives:
Keep the milestone placeholder skip, test only static source strings, or mock a scientific score
and mark the result panels complete. These were rejected because the first two would not verify a
real browser interaction and the last would violate the evidence boundary.

Consequences:
The frontend browser gate is reproducible and covers critical no-fabrication behavior. Phase 16
and Phase 18 still cannot pass their full project gates until registered outputs, gated compute,
and registry-driven figures exist.

Validation:
Commit `7f6c1b1` adds the suite and `bd7647c` makes its environment clone-safe. `make web-e2e`
passes 3 Playwright tests against the production build locally and from the final clean clone.
Commit `4817ef2` removes stale browser-E2E blocker text from the Phase 16, 18, and 19 status
surfaces. No scientific output or paid-compute artifact is created.

## D-031 — Figure generation must fail closed on unregistered or synthetic inputs
Status: ACCEPTED
Date: 2026-09-21

Context:
The legacy M099 `research/scripts/generate_figures.py` read ignored historical snapshots and
constructed 100 synthetic scoring records for demonstration ROC, PR, calibration, and score
distribution files. Those files could be mistaken for current ML-extension evidence even though
the experiment registry was empty.

Decision:
Make the Phase 17 control surface registry-driven and metadata-only until real result artifacts
exist. A figure-input manifest may expose only hash-verified `COMPLETED` PRELIMINARY/FINAL runs;
missing inputs, excluded stages, and hash mismatches remain explicit blockers. The compatibility
script delegates to this manifest and never emits synthetic curves or promotes ignored historical
snapshots. The manifest is deterministic so delete-and-regenerate checks can compare hashes.

Alternatives:
Keep the legacy demo curves, use the ignored cohort snapshots as current inputs, or silently
return an empty figure directory. These were rejected because each would blur the boundary
between software demonstrations, historical baseline material, and current registered science.

Consequences:
`make figures` now produces an auditable `BLOCKED` manifest with no metrics while the registry
has no eligible completed outputs. Once authorized runs exist, their output hashes and source
paths are available to a renderer without changing the evidence policy. Phase 17 and dependent
release gates remain blocked until actual registered results and rendered artifacts exist.

Validation:
Commit `cb304c9` implements the fail-closed manifest and compatibility guard. The empty-registry
manifest is stable across regeneration; temporary eligible fixtures become
`READY` only when all required source files are hash-verified; tampering blocks the manifest;
`make figures`, targeted Ruff, strict mypy, unit tests, and integration tests pass. No model
weights, remote inference, locked-label selection, or paid compute was used.

## D-032 — Align the immutable registry with the Section 21 result contract
Status: ACCEPTED
Date: 2026-09-21

Context:
The existing append-only registry already recorded lifecycle, protocol, git, and output-hash
metadata, but it did not persist the complete result-registry surface required by the master
prompt. The verifier also constructed a registry without an explicit repository root, so a
completed record's output hashes could not be checked reliably when the registry was inspected
from another working directory.

Decision:
Extend `RunRecord` and the JSON Schema with the required experiment family, lifecycle timestamps,
dataset/split hashes, model/checkpoint/source/license identity, preprocessing and feature
versions, config, GPU, runtime/cost, metrics, artifact paths, failure reason, and notes. New
records populate these fields; transitions revalidate the full record before persistence,
disallow metrics on non-completed records, and require completed artifacts to remain hashable.
Update the verifier to accept `--repo-root` and recompute hashes for every completed record.
Backward-compatible Pydantic defaults allow existing fixture records to be read while new
scientific records cannot omit the required JSON fields when serialized.

Alternatives:
Leave the old lifecycle-only schema, store result metadata outside the registry, or trust the
recorded hashes without recomputation. These were rejected because they would weaken the
reproducibility and failure-accounting contract.

Consequences:
The registry can now carry the metadata needed for later scientific runs without creating one.
The current registry remains empty, so no benchmark or result evidence is promoted. Tampered
completed outputs now fail verification explicitly.

Validation:
Commit `800e016`; `make validate` passes with 619 tests, 33 deselected, and 95.31% coverage;
`make schema-verify`, `make registry-verify`, targeted registry tests, Ruff, and strict mypy pass.

## D-033 — Expose registry metadata through a fail-closed read-only workbench surface
Status: ACCEPTED
Date: 2026-09-21

Context:
The workbench had an Experiment Registry tab, but its status was static and could not distinguish
an empty registry from an actual completed scientific run. The project has no current scientific
result artifacts, so a UI integration must not expose raw values or imply downstream readiness.

Decision:
Add a dynamic `/api/registry` GET route that reads append-only run records and returns only run
identity, status, evidence stage, experiment family, timestamps, model name, and artifact counts.
The route marks the surface `READY` only when a `COMPLETED` PRELIMINARY or FINAL run exists; an
empty or malformed registry remains blocked or returns an explicit error. The workbench overview
and registry tab consume this metadata, retain blocked empty states, and omit metrics, file
locations, and clinical labels.

Alternatives:
Keep the static status, expose full run JSON to the browser, or mark the registry ready when any
planned/engineering record exists. These were rejected because they would either hide actual
state or overstate scientific evidence.

Consequences:
The UI is now connected to the real control plane while preserving the evidence boundary. The
current empty registry is visibly blocked, and downstream panels remain independently gated.

Validation:
Commit `800e016`; frontend ESLint, TypeScript, Next production build, contract tests, and
`make web-e2e` pass with four local Playwright tests. The required scoped impeccable detector
reported no findings after the UI change.

## D-034 — Preserve the Phase 3 archive discrepancy instead of tuning the cohort
Status: ACCEPTED
Date: 2026-09-21

Context:
The handoff's validation-only QA checkpoint expects 1,403,225 unique t0 VUS and 1,024 final
temporal records, while a fresh `make data-qc` run over the manifest-verified archives produces
1,402,895 unique valid t0 VUS and 946 final records. A direct streaming audit of the t0 archive
found 1,402,906 exact `Uncertain significance` rows before 11 invalid/self/noncanonical rows are
rejected. The t0 archive SHA-256 matches `research/data_manifests/clinvar_t0.json`.

Decision:
Keep the archive-derived cohort and its zero-overlap, deterministic split artifacts as the
current engineering result, retain the discrepancy in the tracked Phase 3 summary and ledger,
and block model scoring until the difference is resolved from source evidence or approved by a
dated protocol deviation. Do not change the VUS string filter, germline rule, assembly rule,
coordinate normalization, allele validity rule, or duplicate policy merely to reproduce a QA
count.

Alternatives:
Inject the handoff target, broaden filters until the counts match, substitute another archive,
or treat the structural split pass as permission to score. These were rejected because each
would risk changing the frozen estimand or converting a validation target into observed evidence.

Consequences:
The data-only structural gate remains reproducible and reviewable, but the downstream zero-shot,
representation, training, calibration, ensemble, locked-test, figure, and release gates remain
blocked. The exact raw-accounting evidence makes the remaining investigation concrete for a
future approved deviation review.

Validation:
`make data-qc` reproduced the existing split and audit hashes; the direct archive audit found
the counts above; no tracked protocol/data rule changed; and the fresh clean-room clone from
`e798c20` passed all free local engineering gates while retaining an empty registry and blocked
figure manifest.

## D-035 — Make the repository README reflect current evidence, not legacy claims
Status: ACCEPTED
Date: 2026-09-21

Context:
The legacy root README still described a BRCA1 threshold/confidence classifier, an old Modal
endpoint, and historical milestone PASS statements as if they were current EvoVariant-TR ML
extension evidence. Those claims conflicted with the repaired research-only API, empty model and
result registries, current cost gate, and the authoritative phase ledger.

Decision:
Rewrite `README.md` as the current reviewer entry point. It states the frozen temporal estimand,
observed archive-derived counts, unresolved Phase 3 discrepancy, free/local validation commands,
registry/UI/figure behavior, paid-compute boundary, legacy-evidence boundary, and current
`BLOCKED / PARTIAL` release status. Historical reports remain available under `docs/project/`
but are explicitly not current ML-extension result evidence.

Alternatives:
Keep the legacy README and rely on the agent-only control files, or silently edit the old claims
in place while retaining the historical success narrative. These were rejected because a fresh
reviewer would otherwise receive an unsafe and materially misleading project summary.

Consequences:
The root README is now consistent with the master prompt and persistent project-control files.
It does not claim model execution, deployment, clinical validity, release, or scientific results
that have not been evidenced.

Validation:
Commit `0db7e8b`; `git diff --check` passed before commit. The README-only commit changed no
executable code; the exact implementation baseline `800e016` and clean-room evidence at `e798c20`
remain documented separately.

## D-036 — Render the complete Phase 17 bundle only from verified registry artifacts
Status: ACCEPTED
Date: 2026-09-21

Context:
The earlier Phase 17 control surface correctly removed legacy synthetic curves and produced a
metadata-only manifest, but it declared only a subset of the master prompt's figure families and
did not yet provide the required tables, methods summary, limitations, cost summary, provenance,
or export bundle. The checked-in result registry remains empty, so any renderer must continue to
fail closed rather than making the phase look complete.

Decision:
Declare all 19 required figure families and 12 required tables as explicit source-artifact
contracts. Before an entry becomes available, validate its recorded relative path, output hash,
JSON/JSONL row shape, required fields, and finite numeric values. Render a deterministic bundle
with dependency-free SVG figures, source-derived JSON tables, methods and limitations Markdown,
compute/cost JSON, and model-provenance JSON only from hash-verified completed PRELIMINARY or
FINAL registry runs. A blocked or tampered manifest emits only a blocked bundle manifest with no
scientific outputs; reruns remove only paths recorded by the prior bundle manifest.

Alternatives:
Keep a manifest-only surface, add a plotting dependency that could render placeholders, accept
unregistered fixtures, copy ignored historical snapshots, or fill missing rows with inferred
values. These were rejected because they would leave Phase 17 incomplete or blur software
demonstration data with current scientific evidence.

Consequences:
The current repository has a complete local export control surface but remains scientifically
blocked: its registry has zero runs, the manifest has zero available figures/tables, and the
bundle has zero outputs. Once an authorized run supplies the declared artifacts, the same command
surface can regenerate a hash-addressed bundle without manual editing. No model weights, locked
labels, remote inference, or paid compute are needed to validate the renderer itself.

Validation:
Commit `14d9593`; `make validate` passes 625 tests with the 95% coverage floor enforced at
95.34%; strict mypy, Ruff, schema verification, data-QC, scientific/API tiers, frontend build,
browser E2E, registry verification, and `make figures` pass. The blocked manifest hash is
`b1a69cc4674b279967984e9e2d5b77addcc9015da8f1bf396d69d3305fb554a8` and the blocked bundle hash
is `a780d87816fa75ed0fe1f4a69d597e5310d5f70eae1946d49e2bd036e8e0c006`. Scientific Phase 17 and
all dependent release gates remain blocked; spend is `$0`.

## D-037 — Canonicalize chromosomes at the Modal/UCSC boundary
Status: ACCEPTED
Date: 2026-09-21
Supersedes: none

Context:
The first authorized remote Evo2 pilot loaded the model successfully but failed before inference
because the input chromosome `10` was used as the UCSC chromosome key. The same endpoint already
used `chr10` for its cache identity, so a request could have inconsistent transport, fetch, and
cache namespaces.

Decision:
Normalize chromosome values once through `normalize_chromosome`, require `GRCh38`/`hg38` at the
Modal boundary, and use the canonical `chr`-prefixed value for UCSC requests, cache identity,
result provenance, and logs. Add a unit regression test for bare, whitespace-padded, prefixed,
and blank chromosome values.

Alternatives:
Patch only the UCSC request, accept raw chromosome aliases in multiple code paths, or retry the
remote request without changing the app. These were rejected because they would preserve schema
drift or erase the failed evidence.

Consequences:
The corrected endpoint accepts the project's split/API chromosome forms while maintaining one
UCSC-compatible identity. Invalid assembly/genome combinations fail closed. The superseded 500
responses remain recorded.

Validation:
Focused schema tests and `make validate` pass; the corrected Modal request for
`GRCh38:chr10:100065200:C>T` returned HTTP 200. Evidence is in
`artifacts/modal/phase2_pilot_20260921_failed_attempts.json` and the corrected pilot artifact.

## D-038 — Accept real Evo2 pilot evidence without promoting scientific results
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-026

Context:
The user explicitly authorized a bounded Modal pilot after authentication was verified. The
master prompt requires exact run metadata, a small real model call, persistent cache evidence,
and available cost accounting before later scientific phases can proceed.

Decision:
Accept the corrected Evo2 7B H100 miss/hit pair as Phase 2 and Phase 4 engineering-gate
evidence. Record the model revision, app deployment, protocol hash, exact normalized variant,
raw forward/reverse scores, runtime, cache path, and cost distinction in tracked artifacts and
the append-only ledger. Do not treat the single variant as a benchmark, cohort result, figure
input, clinical classification, or locked-test evidence.

Alternatives:
Claim success from the deployment alone, claim an exact per-request invoice from the workspace
summary, or run a larger batch while the cohort discrepancy remains unresolved. These were
rejected because they would overstate evidence or expand spend beyond the bounded pilot.

Consequences:
Evo2 is eligible for later execution only after the Phase 3 and multi-model gates are resolved.
The Modal model-weight cache remains remote and untracked. Per-request measured USD remains
unknown; rate-based estimates and workspace-level billing are labeled separately.

Validation:
`artifacts/modal/phase2_phase4_pilot_20260921_success.json`, four new cost-ledger entries,
deployment v3 `phase2-pilot-20260921-r1`, HTTP 200 miss/hit responses, exact score equality on
the hit, and `make validate`.

## D-039 — Reopen Phase 3 because the cohort discrepancy is scientifically material
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-021, D-034

Context:
The current manifest-verified archives produce 1,402,895 valid t0 VUS and 946 final temporal
records (536 B/LB, 410 P/LP), while the validation-only handoff target reports 1,403,225 t0 VUS
and 1,024 final records (614 B/LB, 410 P/LP). The target ID set and target-side leakage/duplicate
evidence are not available for direct comparison.

Decision:
Reopen the Phase 3 acceptance review and classify the discrepancy as material to IDs, temporal
eligibility, class balance, cohort denominators, and potentially gene grouping. Keep the current
archive-derived data and structural invariants unchanged. Do not score the full cohort or call it
the handoff cohort until source-level reconciliation or a dated protocol deviation explicitly
accepts the changed estimand.

Alternatives:
Proceed because the P/LP count matches, tune filters to the handoff counts, or use the pilot
variant as a substitute for cohort validation. These were rejected because B/LB and denominator
changes can alter every downstream metric and the pilot is not a cohort result.

Consequences:
Phases 6–19 remain blocked. The current split's zero-overlap and duplicate checks remain useful
engineering evidence but are not evidence that the unavailable target set has identical IDs or
leakage properties.

Validation:
`artifacts/phase3_discrepancy_impact_20260921.json` and
`research/ml_extension/splits/phase3_manifest_summary.json`; source archive hashes remain
unchanged and no protocol filter was modified.

## D-040 — Audit candidate models explicitly and include only verified Evo2
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-025

Context:
Phase 5 requires official-source, license, checkpoint/revision, input, score, hardware,
embedding/fine-tuning, and tiny-smoke review for every candidate. The official candidates do not
share one ready-to-run contract: GPN-Star needs a large exact MSA store; Nucleotide Transformer
and Caduceus expose masked-LM/embedding paths; CADD needs a very large annotation bundle; PhyloP
is site conservation; AlphaMissense is a missense-only precomputed database without weights.

Decision:
Set Evo2 to `INCLUDED` with verified provenance after its real pilot. Set the other six registry
manifests to explicit `INFEASIBLE` statuses with source-backed deferred reasons; do not count
their fixture comparators as scientific models. Select GPN-Star as the next relevance candidate
if its exact alignment data and a separate bounded budget become available, but do not download it
or run a smoke under the current approval.

Alternatives:
Include masked-LM pseudo-likelihoods as if they were Evo2 scores, use synthetic comparators, or
download multi-gigabyte/terabyte assets before resolving Phase 3. These were rejected because
they would violate score-contract parity, provenance, or cost gates.

Consequences:
The model registry is auditable and schema-valid with one included candidate; Phase 5 remains
blocked for the required multi-model benchmark selection. No Phase 6 benchmark is started.

Validation:
`artifacts/model_audit/phase5_candidate_audit_20260921.json`, updated manifests under
`research/ml_extension/models/`, official source pages/revisions recorded in the audit, and
`make model-registry-verify` with `included_count: 1`.

## D-041 — Make Phase 3 QA funnel counters mutually exclusive
Status: ACCEPTED
Date: 2026-09-21
Supersedes: none

Context:
The frozen QA checkpoint reports `below_two_stars` and `not_definitive_at_t1` as separate funnel
categories. The archive-derived implementation previously counted every low-star matched record
as `below_two_stars` and counted only high-star non-definitive records as `not_definitive_at_t1`,
so the fields were not comparable to the target partition even though the primary label gate was
unchanged.

Decision:
Define the audit categories without changing eligibility or model policy: absent records remain
absent; definitive B/LB or P/LP records below two stars count as `below_two_stars`; all
non-definitive outcomes, including low-star non-definitive records, count as
`not_definitive_at_t1`; only definitive outcomes meeting the >=2-star gate enter the final cohort.

Alternatives:
Leave the ambiguous counters in place, tune the archive filters to force the target counts, or
alter the immutable primary star gate. These were rejected because the first obscures the QA
comparison and the latter two would change or contaminate the frozen research design.

Consequences:
The current archive now reports 9,049 below-star definitive records and 1,389,441 non-definitive
records, with a mutually exclusive sum of 1,402,895. The target remains 330 t0 IDs and 78 final
B/LB records larger; without the target ID/source set, Phase 3 remains blocked and no scoring is
authorized.

Validation:
`artifacts/phase3_partition_audit_20260921.json`, `make data-qc`, and
`./.venv/bin/pytest -q tests/unit/test_splits.py` (7 passed). The original protocol hash and all
immutable protocol fields remain unchanged.

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

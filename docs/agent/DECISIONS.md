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

## D-042 — Retain the Phase 3 discrepancy after independent parser cross-check
Status: ACCEPTED
Date: 2026-09-21
Supersedes: none

Context:
After correcting the QA-funnel counter semantics, the archive-derived streaming path still
produced 1,402,895 unique t0 VUS versus the validation-only target of 1,403,225. The target ID
set was not present in the handoff or repository.

Decision:
Run a non-authoritative cross-check through the existing version-aware parser and normalized
identity implementation. It produced 1,402,906 unique t0 VUS, only 11 above the ML-extension
path and still 319 below the target. Treat this as corroboration that the remaining discrepancy
cannot be resolved by selecting between the two in-repository parser paths. Retain the current
archive-derived cohort, do not tune filters, and keep scoring blocked pending target source/ID
provenance or a dated protocol deviation.

Alternatives:
Choose the parser path closer to the target, import unverified IDs from an external source, or
declare the discrepancy benign from aggregate counts. These were rejected because none supplies
the missing identity-level evidence required for cohort, label, and leakage reconciliation.

Consequences:
The Phase 3 blocker is now supported by two independent local implementations and the recorded
official archive provenance. The missing target ID/source artifact remains an external evidence
requirement; no downstream scientific phase is authorized.

Validation:
The cross-check is recorded in `artifacts/phase3_partition_audit_20260921.json`; the official
archive hashes remain unchanged, `make data-qc` and `make validate` pass, and no model scoring ran.

## D-043 — Keep phase-status command surfaces aligned with current gates
Status: ACCEPTED
Date: 2026-09-21
Supersedes: none

Context:
The ignored Phase 6, 15, 18, and 19 status artifacts had been reconciled after the bounded Evo2
pilot, but their Makefile targets still contained pre-pilot blocker text. Rerunning those targets
would have overwritten truthful status with stale claims.

Decision:
Update the Makefile blocker arguments to state the current gates: Evo2 is verified only for
single-variant engineering evidence, the Phase 3 discrepancy and Phase 5 multi-model gate remain
open, full-cohort authorization/batch parity are absent, and clean-room scientific reproduction
and registered result artifacts remain unresolved.

Alternatives:
Leave the generated JSON as a one-off manual correction, remove the status targets, or mark later
phases as passed because local contract tests pass. These were rejected because persistent command
surfaces must be reproducible and a local gate cannot replace scientific output evidence.

Consequences:
Rerunning the free status commands preserves the same truthful `BLOCKED` records and does not
invoke Modal, download weights, or create scientific result artifacts.

Validation:
The four status targets were rerun after the Makefile update; their JSON blockers match the
current Phase 3/5/6/15/18/19 control-file state. `make validate` and the targeted contract gates
remain passing.

## D-044 — Make the local Evo2 batch contract genuinely batched

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The local `Evo2Scorer.score_batch` surface existed before a real Evo2 adapter was verified, but it
implemented the batch by calling the model once per variant and orientation. That was compatible
with unit-level interfaces but did not provide the intended model-batch execution path for Phase
15 or a useful basis for remote parity.

Decision:
Prepare the forward/RC reference and alternate sequences for every valid row, then submit them to
`Evo2.score_sequences` in chunks no larger than `Evo2ScorerConfig.batch_size`. Preserve the
existing `ScoringResult` row mapping and per-row validation failures, and retain raw reference,
alternate, and delta values. Add a deterministic fake-model regression that proves chunking and
mapping without importing weights or invoking Modal.

Alternatives:
Keep the one-call-per-sequence implementation, or silently increase the batch size for a remote
pilot. Both were rejected: the first leaves the batch contract nominal, while the second would
change paid-compute behavior without a separately bounded approval and remote parity test.

Consequences:
The local adapter is now suitable for a later authorized batch parity test. This decision does
not authorize a full cohort, locked-test scoring, model download, or Modal batch invocation. The
Phase 15 gate remains `BLOCKED` until remote batch behavior and kill/restart recovery are evidenced.

Validation:
`./.venv/bin/pytest -q tests/unit/test_evo2_scorer.py` passed with 8 tests, including a fake-model
test that submits four sequences as chunks of 3 and 1 and checks exact row mapping and delta
arithmetic. No paid compute or scientific result artifact was created.

## D-045 — Keep the Modal batch endpoint bounded and undeployed pending parity approval

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The Phase 15 control surface needs a true remote batch path, but the current approval artifact
only covers the corrected single-variant Evo2 pilot, cache miss/hit evidence, and a bounded model
smoke. Deploying or invoking a new endpoint would change the paid-compute scope and would not by
itself resolve the Phase 3 cohort discrepancy or Phase 5 multi-model gate.

Decision:
Add a source-level `score_batch` endpoint to `evo2_scorer_app.py` with an eight-variant request
limit, eight-sequence model chunks, the canonical four-score orientation payload, persistent cache
identity, input-order preservation, and explicit completed/partial/failed responses. Keep the
endpoint undeployed until a new bounded approval authorizes a remote batch parity and recovery
smoke.

Alternatives:
Deploy immediately under the existing single-variant approval, or implement a sequential wrapper
that calls the single endpoint for each row. Both were rejected because the first exceeds the
recorded scope and the second would not test actual model batching.

Consequences:
Phase 15 has a reviewable implementation surface and no additional spend, but its scientific and
remote execution gate remains `BLOCKED`. The deployed app and the recorded Phase 2/4 artifact
remain unchanged.

Validation:
Ruff, strict mypy, Python compilation, the eight Evo2 adapter unit tests, and a no-spend source
helper smoke passed. No deployment, model download, batch result, or paid request was performed.

## D-046 — Estimate full-cohort cost before any Phase 6 launch

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The master prompt requires measured pilot behavior and a cost estimate before a subsequent full
benchmark. The corrected pilot provides one single-variant H100 miss, but no remote batch
throughput measurement exists and the current approval explicitly excludes a full benchmark.

Decision:
Record a transparent prelaunch estimate using the observed `$0.0398` single-variant wall-rate
estimate and the current archive-derived cohort counts. Preserve separate sequential and
hypothetical perfect-eight-times scenarios, label both as low-confidence planning bounds, and do
not launch Phase 6 from the estimate.

Alternatives:
Treat the workspace billing delta as a per-request invoice, assume unmeasured batch throughput is
linear, or use the stale August full-run artifact as current authorization. These were rejected
because the billing summary is workspace-level, throughput is unmeasured, and the current protocol
and scope require a fresh approval for a materially larger run.

Consequences:
The project has an auditable prelaunch budget estimate: about `$55,835.221` sequential or `$6,979.403`
under the unverified perfect-eight-times scenario for the current 1,402,895-variant t0 cohort.
Those figures are not scientific results or permission to spend; Phase 6 remains `BLOCKED`.

Validation:
The artifact `artifacts/modal/phase6_preflight_cost_estimate_20260921.json` parses and records the
current read-only workspace summary, source pilot inputs, cohort counts, assumptions, confidence,
and required approvals. No additional remote invocation was made.

## D-047 — Persist the resumability denominator in every batch manifest

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
`BatchJob.to_dict()` persisted total variants and shard size but omitted `total_shards`. A job
manifest produced by the serializer could therefore be read by `check_resume_state()` with its
fallback denominator of one, overstating progress after a restart.

Decision:
Validate non-negative job sizes, derive and persist `total_shards` from total variants and shard
size, and reject non-positive shard, model-batch, or rank sizes before deterministic sharding.
Cover the serialized denominator and invalid-input behavior with unit tests.

Alternatives:
Keep the fallback denominator, infer it only when reading old manifests, or trust callers to add
the field manually. These were rejected because a newly written manifest must be self-consistent
and invalid execution parameters should fail before queueing work.

Consequences:
Local batch resume progress is now auditable and deterministic for manifests written by the
canonical serializer. Older hand-authored manifests remain readable through the existing fallback;
the remote Phase 15 recovery gate remains blocked until a real authorized smoke.

Validation:
`./.venv/bin/pytest -q tests/unit/test_batch.py` passed with 34 tests; Ruff and strict mypy passed
for the changed module. No Modal invocation or scientific output was created.

## D-048 — Upgrade frontend dependencies and align Next 16 lint/build tooling

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The previous Next 15 frontend passed its build/browser gate but a clean dependency install
reported production and development advisories, including critical/high findings in the Next
dependency tree. Next 16 also removes the legacy `next lint` command and the `eslint` field from
`NextConfig`, so retaining the old configuration would leave the repository with a broken clean
build path.

Decision:
Upgrade the frontend to Next.js `16.3.5` and the matching `eslint-config-next`/Windows SWC
optional package, update PostCSS to `8.5.28`, use the native flat-config export from
`eslint-config-next/core-web-vitals`, run ESLint directly from package scripts and the Makefile,
remove the removed Next `eslint` config field, and preserve the deliberate client-side effect
patterns through a narrowly scoped Next 16 rule override. Apply the normal non-force npm audit
remediation to the lockfile.

Alternatives:
Keep the old dependency graph and document known advisories, use `npm audit fix --force`, or
silence the entire lint gate. These were rejected because the first leaves known vulnerabilities,
the second permits unreviewed major changes, and the third would weaken source validation.

Consequences:
The frontend dependency graph is audit-clean for both production and development installs, and
the web build/lint/browser gates remain explicit. Next 16 reports only non-failing tracing warnings
for the dynamic registry filesystem and parent-directory package-lock discovery. This decision
does not create scientific outputs, alter the frozen protocol, or promote any blocked phase.

Validation:
Commit `739310d` passes `make web-check` and four-test `make web-e2e`. A fresh clone passed
`make bootstrap`, `make frontend-install`, `make validate`, `make test-scientific`, `make test-e2e`,
protocol/control-plane/schema/model-registry/registry checks, `make web-check`, and `make web-e2e`;
`npm ci` and both full and production-only `npm audit` reported zero vulnerabilities. The fresh
clone's `make figures` and `make release-check` correctly remained blocked on missing scientific
artifacts.

## D-049 — Record local batch recovery evidence without promoting it to remote evidence

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
Phase 15 requires kill/restart recovery, but the current Modal approval scope excludes remote
batch parity and recovery. The repository already contains a gated test suite that simulates
persisted shard completion and failure, then reconstructs resumable progress without loading a
GPU model.

Decision:
Run the explicitly acknowledged modal-tier test command as a no-GPU local recovery simulation and
record its result separately from remote evidence. Preserve the real remote batch endpoint as
undeployed until a new approval authorizes batch parity, partial-failure behavior, and kill/restart
recovery.

Alternatives:
Treat the local simulation as a remote recovery PASS, run the undeployed endpoint under the
single-variant pilot approval, or omit the recovery evidence entirely. These were rejected because
they would either misstate the execution environment, exceed the approval scope, or discard useful
local contract evidence.

Consequences:
The local Phase 15 recovery contract is more strongly evidenced, while the overall phase remains
`BLOCKED` on remote batch parity, full-cohort authorization, and remote recovery. No GPU model,
Modal function, or scientific result artifact was created by this test.

Validation:
`EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS ./.venv/bin/pytest --run-modal -m modal
tests/modal -rs` passed 9 tests with one documented placeholder skip in 1.44 seconds. The suite
covered deterministic shards, persisted completed/failed states, progress reconstruction, retry
classification, and shard serialization.

## D-050 — Reject full-run approvals tied to stale protocol hashes

Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The repository contains an old August full-run approval artifact whose schema is valid but whose
protocol hash predates the frozen ML-extension protocol. The previous cost-policy loader checked
fields, environment, and GPU type but did not compare the approval hash with the current control
plane.

Decision:
Make `require_full_run_approval()` load the current ML-extension protocol hash from
`research/ml_extension/protocol_hashes.json` and reject any approval whose hash differs. Keep the
existing pilot approval separate because it is not a full-run approval and remains bounded to its
recorded scope.

Alternatives:
Trust the human-readable approval scope, accept any non-empty hash, or silently rewrite the stale
approval. These were rejected because a stale approval can authorize the wrong estimand, and
rewriting an approval would invent user authority.

Consequences:
The stale August artifact cannot pass the full-run gate. A future full benchmark requires a new
approval artifact explicitly tied to the current frozen protocol, in addition to the paid
acknowledgement and scientific phase gates. No compute or scientific result was created by this
change.

Validation:
The targeted cost-policy suite passes 26 tests; Ruff and strict mypy pass for the changed module.
An explicit check reports `approval protocol_hash does not match the current frozen ML-extension
protocol` for `artifacts/approvals/full_run_approval.json`.

## D-051 — Freeze the source-level Evo2 representation contract
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
Phase 7 needs a deterministic representation contract before any downstream classifier or
hyperparameter work can be considered. The official Evo2 API supports returning named hidden
layer embeddings from a forward pass. The current compute approval does not authorize a remote
embedding smoke, so the repository must record the contract without presenting it as executed
feature evidence.

Decision:
Use Evo2 7B revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, layer
`blocks.28.mlp.l3`, and mean pooling across the token axis. Extract four vectors per SNV:
forward reference, forward alternate, reverse-complement reference, and reverse-complement
alternate. Persist reference, alternate, and alternate-minus-reference vectors for each
orientation with shape, dtype, SHA-256 hashes, provenance, and a separate content-addressed
feature-cache identity. Reject caller-selected layers so locked-cohort selection cannot be
tuned through the endpoint.

Alternatives:
Expose arbitrary layers or pooling modes, store only a single orientation, or run the remote
embedding endpoint under the existing single-variant raw-score pilot approval. These were
rejected because they would leave the feature estimand under-specified or exceed the approved
compute scope.

Consequences:
Phase 7 has an implementable, auditable source contract and a no-spend payload regression test.
The feature API remains source-level only; no remote embedding shape, memory, latency, cost, or
completed feature-cache evidence is claimed. Phases 8 and 9 remain blocked until a future
approval authorizes the embedding smoke and the Phase 3/6 gates are resolved.

Validation:
`tests/unit/test_modal_scorer_source.py` passes 3 tests; Ruff and Python compilation pass for
the source-level endpoint. The implementation follows the official Evo2 embedding interface
documented at https://github.com/ArcInstitute/evo2#extract-embeddings.

## D-052 — Formally defer adaptation by compute and authorization
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The master prompt permits Phase 10 to be completed by a formal compute deferral when a valid
adaptation experiment cannot be justified. The current approval is capped at `$2.00` and
explicitly excludes training, HPO, fine-tuning, and locked-test work. The real Evo2 pilot
measured `3.914133089` H100 runtime seconds and `18,075,978,752` peak GPU bytes for one raw-score
request; the current-cohort preflight projects `$55,835.221` under a sequential single-variant
bound or `$6,979.403` under an unmeasured perfect eight-variant throughput assumption. These are
inference-planning observations, not a training-cost quote, so no training feasibility claim is
made from them.

Decision:
Record Phase 10 as `DEFERRED_BY_COMPUTE` with no training metrics. Preserve the measured
inference envelope and prelaunch cost evidence, record that no official training runner is
checked into this repository and no local CUDA/Torch training runtime is available, and require a
new approval tied to the current protocol before any official Savanna/BioNeMo or PEFT smoke is
attempted. The status surface remains no-metrics and reopenable.

Alternatives:
Run a tiny training smoke under the current raw-score pilot approval, treat inference memory as
proof of training feasibility, or mark Phase 10 `PASS` because the source interfaces exist.
These were rejected because they would exceed the approval scope or confuse infrastructure
evidence with an adaptation experiment.

Consequences:
The master prompt's optional adaptation requirement has a formal, auditable deferral outcome.
No checkpoint, loss curve, validation metric, or scientific result is created. Phases 8, 9, and
11 onward remain governed by their independent prerequisites; this deferral does not unblock
them.

Validation:
`artifacts/modal/phase10_adaptation_deferral_20260921.json` is valid JSON and records the
current protocol hash, approval scope, measured pilot evidence, and resume conditions.
`tests/unit/test_cli.py` covers `--status DEFERRED`, and `make finetune-smoke` writes
`research/runs/phase10_ft_status.json` with `status: DEFERRED` and empty metrics.

## D-053 — Formally defer the multi-model benchmark track after the candidate audit
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-040

Context:
The Phase 5 audit evaluated all seven declared candidates against the frozen GRCh38 raw-SNV
score contract, provenance/license requirements, required assets, applicability, and bounded
compute. Evo2 passed a real H100 smoke. Nucleotide Transformer and Caduceus expose masked-LM or
embedding paths without a frozen raw-SNV parity contract; GPN requires an absent approximately
42 GB alignment asset; CADD requires an approximately 300 GB annotation bundle and different
score semantics; PhyloP is site-wise conservation; and AlphaMissense is a missense-only
precomputed subset without a frozen applicability manifest.

Decision:
Record the multi-model Phase 5 track as `DEFERRED` with Evo2 as the only included model. Keep
all six exclusions explicit and source-backed, do not download their assets or promote fixture
comparators, and require a new candidate-specific approval plus tiny parity smoke before Phase 6
can reopen.

Alternatives:
Treat masked-LM logits as raw allele scores, download the GPN/CADD assets before resolving Phase
3, or count deterministic comparator fixtures as included models. These were rejected because
they would change the score estimand, exceed current authority, or fabricate multi-model
evidence.

Consequences:
The master prompt's requirement to benchmark multiple models or rigorously document
infeasibility is now represented as a formal deferral outcome. Phase 6 remains `BLOCKED` because
no second score-compatible model is verified and the Phase 3 discrepancy is unresolved.

Validation:
`artifacts/model_audit/phase5_candidate_audit_20260921.json` and
`artifacts/model_audit/phase5_multi_model_deferral_20260921.json` preserve the candidate-level
evidence and resume conditions. `make model-registry-verify` continues to pass with 7 manifests
and 1 included model.

## D-054 — Validate embedding payloads before feature-record storage
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
Phase 7 has a frozen source-level Evo2 representation contract, but a raw embedding payload is
not yet a safe downstream feature artifact by itself. A storage boundary must reject incomplete,
tampered, dimensionally inconsistent, or differently pooled payloads without introducing model
selection or locked-label feedback.

Decision:
Add `feature_record_from_embedding_payload()` to `src/evovariant_tr/feature_store.py`. It accepts
only completed payloads using the frozen `mean_tokens` pooling rule, verifies the normalized ID,
layer, finite reference/alternate/difference vectors, shape metadata, SHA-256 hashes, exact
alternate-minus-reference arithmetic, and forward/reverse dimension agreement, then emits a
content-addressed `FeatureRecord`. The default representation is the fixed concatenation of
forward and reverse-complement alternate-minus-reference vectors; explicitly named forward-only,
reverse-only, and orientation-mean representations remain deterministic storage choices rather
than tuned choices. The adapter does not call Modal, inspect labels, choose a layer, or unlock
the locked test.

Alternatives:
Store raw payloads without verification, accept caller-selected pooling/layers, or run a remote
embedding smoke to populate a cache under the existing approval. These were rejected because
unverified payloads would weaken provenance, arbitrary representation choices would reopen
selection leakage, and the current approval does not authorize remote embedding work.

Consequences:
Phase 7 now has a tested local conversion boundary that can be used after a separately approved
remote embedding smoke. It does not create a feature cache, establish remote shape/latency/cost,
or unblock Phases 8 and 9; the Phase 7 gate remains `BLOCKED` until remote evidence and the
upstream Phase 3/6 prerequisites are resolved.

Validation:
Commit `2c9b3ca` adds the adapter and `tests/unit/test_feature_store.py`. The no-spend tests
cover compact record construction, orientation-mean conversion, tamper/hash rejection, and
pooling rejection. The latest `make validate` run passed 642 tests, 33 deselected, strict mypy
over 51 source files, Ruff, secret scan, and 95.01% coverage.

## D-055 — Retain manifest-verified ClinVar archives after source-path audit
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
Phase 3 remains blocked because the manifest-verified archive-derived cohort is 330 unique t0
VUS IDs and 78 final records below the validation-only handoff target. The target ID list is not
present locally, so an alternate official source path was checked before treating the discrepancy
as an external provenance blocker.

Decision:
Retain the frozen manifest-verified NCBI archive files and their existing SHA-256 manifests.
The archived 2025-01 and 2026-08 URLs return HTTP 200 with the recorded byte lengths and release
timestamps; the corresponding non-archive `tab_delimited` URLs return HTTP 404. Do not replace
the archives, tune filters, or infer target IDs from aggregate counts.

Alternatives:
Swap to an unverified URL, alter the temporal filters until the aggregate target matches, or
construct a synthetic target ID set from the counts. These were rejected because each would
destroy provenance or change the frozen estimand.

Consequences:
The archive provenance is better constrained, but the Phase 3 gate remains `BLOCKED` until the
target-side IDs/source records are supplied or a dated protocol deviation accepts the current
archive-derived cohort. All dependent scientific phases remain blocked.

Validation:
`artifacts/phase3_source_provenance_check_20260921.json` records the six read-only endpoint
checks, HTTP statuses, release timestamps, content lengths, local archive hashes, and the
resulting decision.

## D-059 — Verify Phase 3 source archives before generating splits
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The Phase 3 builder previously hashed the manifest JSON files into the derived summary but did
not verify that the raw archive bytes still matched those manifests before reading and splitting
the data. A later `make data-verify` repair made the legacy ClinVar metadata readable, exposing a
safe opportunity to apply the same integrity gate to the actual data-building path.

Decision:
Before any Phase 3 row processing or output creation, require each source archive to be described
by exactly one manifest entry with the expected filename and to pass size, stored SHA-256, and any
recorded uncompressed-content checks. Abort with a manifest error on mismatch.

Alternatives:
Continue hashing only manifest metadata, verify after derived files are written, or silently
rebuild from a changed archive. These were rejected because each could produce derived artifacts
from unverified source bytes or leave partial outputs that appear reviewable.

Consequences:
`make data-qc` now fails closed before processing if either source archive is missing, tampered,
or paired with the wrong manifest. Valid current archives reproduce the existing deterministic
split and temporal hashes; the frozen protocol, cohort filters, and Phase 3 discrepancy decision
are unchanged.

Validation:
Commit `601e366` adds the gate and a tampered-source regression. The real archive-backed
`make data-qc` run passed with split-manifest SHA-256
`96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72` and split hash
`bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`; `make validate` passed
650 tests with 33 deselected and 95.08% coverage.

## D-058 — Normalize legacy ClinVar manifests at verification time
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The free `make data-verify` command used the generic multi-entry manifest loader, while the
frozen ClinVar acquisition manifests intentionally use the earlier single-file metadata shape.
The command therefore failed before checking the already present archive bytes, even though the
archive hashes and sizes were independently recorded and verified.

Decision:
Keep the frozen single-file ClinVar manifest JSON unchanged and normalize it to the generic
manifest model only when loading it for verification. Preserve strict validation, source-URL
sanitization, compression detection, and the existing multi-entry manifest behavior.

Alternatives:
Rewrite the historical ClinVar manifests into the newer schema, weaken the generic manifest
model, or add a separate one-off verifier. These were rejected because rewriting source evidence
would change its recorded format, weakening the model would reduce guarantees, and a second
verification path would duplicate logic.

Consequences:
Both manifest-verified raw archives can be checked through the documented `make data-verify`
surface, while newer manifests remain supported. This fixes an engineering/data-integrity gate;
it does not change the frozen protocol, cohort definition, or Phase 3 discrepancy status.

Validation:
Commit `c401140` adds the normalization and regression coverage. `make data-verify` passes for
both `research/data_manifests/clinvar_t0.json` and `research/data_manifests/clinvar_t1.json`;
`make validate` passes with 649 tests, 33 deselected, and 95.08% coverage.

## D-057 — Do not tune the Phase 3 VUS definition to aggregate counts
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The Phase 3 current archive-derived cohort has 330 fewer unique t0 IDs than the validation-only
handoff target. A read-only sensitivity audit tested the populated VCF fields, legacy allele
fields, every raw clinical-significance label containing `uncertain`, and broader assembly,
origin, and variant-type filters.

Decision:
Keep the frozen exact `Uncertain significance` plus GRCh38 germline SNV definition. The exact
definition produces 1,402,895 unique IDs; all uncertainty-containing labels produce 1,403,086,
still 139 below the target; and broader filters overshoot substantially. The legacy allele fields
are `NA` for the VUS rows and `ClinSigSimple` contains numeric `0`/`1`, so neither is a defensible
replacement. Do not infer target IDs from aggregate counts or alter the protocol to force a match.

Alternatives:
Include every uncertainty-related label, use the legacy allele fields, relax assembly/origin/type
filters, or add an arbitrary subset of records to reach 1,403,225. These were rejected because
they change the estimand without target-side provenance and would make the cohort irreproducible.

Consequences:
The Phase 3 discrepancy is narrowed to missing target-side provenance or a historical computation
not represented by any tested current-archive filter. The current cohort remains internally
auditable, but Phase 3 and all dependent scientific phases remain blocked.

Validation:
`artifacts/phase3_filter_sensitivity_20260921.json` records the raw-label counts, unique-ID
counts, filter matrix, legacy-field result, and decision. No source archive or frozen protocol
was modified.

## D-056 — Require explicit remote smoke evidence for Evo2 adapter readiness
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
`Evo2Adapter.check_readiness()` previously returned `READY` when local package/parity checks
passed even though its reason stated that the required remote tiny-inference smoke was still
missing. An injected scorer could therefore be treated as executable without a machine-readable
remote-evidence boundary.

Decision:
Keep local parity and package checks separate from remote execution evidence. `Evo2Adapter` now
requires an explicit `remote_smoke_checker` whose named checks all pass before returning `READY`.
Missing, malformed, incomplete, or failed remote evidence returns `DEFERRED` or `FAILED` and is
included in the readiness report. The default adapter map remains non-executing and does not
download weights or invoke Modal.

Alternatives:
Treat local CUDA/package presence as sufficient, trust the injected scorer, or infer remote
readiness from the model manifest's prose. These were rejected because infrastructure presence is
not a remote scientific smoke and would weaken the Phase 5 gate.

Consequences:
The adapter control plane is fail-closed and future remote runners must inject auditable smoke
evidence before scoring. This does not create new remote evidence, change the current Evo2 pilot
artifact, or unblock the deferred multi-model Phase 5 track and dependent phases.

Validation:
Commit `696fcd6` updates `src/evovariant_tr/model_adapters.py`; commit `89563b2` adds the full
readiness regression coverage in `tests/unit/test_model_adapters.py`. Targeted Ruff, strict
mypy, and eight adapter tests pass; the full `make validate` gate passes with 647 tests, 33
deselected, and 95.07% coverage.

## D-060 — Keep Phase 3 blocked after complete local integrity audit
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-039, D-041, D-042, D-055, D-057, D-059 where the newer audit provides the consolidated current gate evidence

Context:
The user-prioritized continuation required an exact diagnosis of the Phase 3 blocker and a
complete data-integrity audit rather than a count-only discrepancy note. The manifest-verified
2025-01 and 2026-08 ClinVar archives, frozen protocol, derived temporal artifacts, and split
artifacts were available locally. The validation-only handoff target identity/source set and the
frozen GRCh38 FASTA/index were not.

Decision:
Run and retain the evidence-first `make phase3-audit` surface. Require source byte/hash/gzip
verification, exact VUS/assembly/origin/SNV/REF/ALT/coordinate filters, normalized-ID uniqueness,
duplicate/conflict accounting, review/date/temporal accounting, overlap and gene-leakage checks,
serialized schema/hash checks, and two fresh deterministic rebuilds. Do not force the handoff
aggregate counts. Keep the overall Phase 3 status `BLOCKED` because
`handoff_target_identity_reconciliation` is `BLOCKED_MISSING_TARGET_ID_SET` and
`independent_grch38_reference_base` is `NOT_RUN` when the frozen FASTA/index is absent.

Alternatives:
Add synthetic records to reach the target, tune the frozen filters to match aggregate counts,
use the current assembly/identity cross-check as a substitute for FASTA base validation, or
promote the internally clean cohort to an ordinary Phase 3 PASS. These were rejected because
they would change the estimand or claim evidence that is not present.

Consequences:
The current cohort remains reproducible and safe for audit, but the final denominator and class
counts cannot be treated as the validation-only target. All downstream scientific phases remain
blocked until target-side identities/source rows and independent frozen-reference evidence are
supplied or a dated protocol deviation is explicitly approved.

Validation:
`artifacts/phase3_integrity_diagnostic_20260921.json` records the exact expected/actual values,
affected counts, and impact on labels, temporal eligibility, overlap, reference matching,
duplicates, gene grouping, and denominators. `artifacts/phase3_integrity_audit_20260921.json`
records the machine-readable scan. `make validate` passed with 656 tests, 33 deselected, strict
mypy over 52 source files, Ruff, secret scan, and 95.14% coverage. The audit artifact SHA-256 is
`ffce3a86eed002822d6501a2d0d95ecf59bf73d2a646ae22398c517a772f9fa5`.

## D-061 — Advance Phase 5 to two subset-only real smoke tracks
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-040 and D-053 for current Phase 5 execution status

Context:
The user-prioritized continuation required meaningful work beyond the already verified Evo2
candidate. The existing six-candidate deferral was not sufficient by itself. The current bounded
approval authorizes Phase 5 smoke-test evidence only, not full benchmark inference, training,
HPO, embedding extraction, or locked evaluation.

Decision:
Run bounded real H100 checkpoint smokes for the two best practical preferred candidates,
Nucleotide Transformer v2 500M and Caduceus-Ph. Verify official source/checkpoint revision,
license, preprocessing/tokenization, context limit, finite logits, hidden states, and a
synthetic one-base ref/alt embedding plumbing path. Record both as `SUBSET_ONLY` because neither
provides the frozen GRCh38 alternate-minus-reference raw-score contract; keep Evo2 as the only
raw-score `INCLUDED` model. Classify GPN and CADD as `DEFERRED_BY_COMPUTE`, and PhyloP and
AlphaMissense as `DEFERRED_BY_COMPATIBILITY` under the explicit status vocabulary.

Alternatives:
Promote masked-LM logits to a pseudo-likelihood without a predeclared protocol, call synthetic
embedding deltas scientific variant scores, download the approximately 42 GB GPN alignment or
approximately 300 GB CADD bundle under the smoke approval, or leave all non-Evo2 work globally
deferred. These were rejected because the first two would change semantics, the asset downloads
exceed scope, and the last would fail the required Phase 5 effort.

Consequences:
Phase 5 now has two additional evidence-backed model tracks and a frozen roster with explicit
compatibility boundaries. Phase 6 remains blocked: only Evo2 can enter the raw-score benchmark,
and the current Phase 3 external gates plus full-run authorization remain unresolved. The two
smokes used synthetic inputs and create no ClinVar metrics, feature cache, or locked-label use.

Validation:
`artifacts/model_audit/phase5_real_smokes_20260921.json` records real H100 outputs for both
checkpoints. `artifacts/model_audit/phase5_multi_model_smoke_resolution_20260921.json` records
the full seven-candidate roster, official sources, exact revisions, status, smoke and blocker
evidence, and workspace billing interpretation. The smoke wall-rate estimate was `$0.0152`; the
post-smoke workspace snapshot was metered `$12.21122616` and billed `$0.00`.

## D-062 — Accept the reproducible 946-record ML-extension cohort after exhaustive recovery
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-060 for the Phase 3 gate decision; preserves the historical zero-shot record

Context:
The handoff target of 1,403,225 t0 VUS identities and a 1,024-record temporal cohort (614
B/LB, 410 P/LP) was documented only as aggregate counts. The final recovery search covered
reachable history, deleted paths, all refs, reflog entries, unreachable objects, fetched remote
heads/tags, repository artifacts, generated data, presentations, scripts, logs, local worktrees,
and supplied attachments. The machine-readable search record reports 133 reachable commits,
95 reflog entries, 91 reflog commits, 6 refs, 1 unreachable commit, 2 unreachable blobs, 12
deleted paths, and one fetched remote branch head. No normalized-ID set or source-row manifest
reconstructing the historical target was recovered.

Decision:
Keep the historical aggregate counts as validation-only evidence. Under ML-DEV-001 and ML
extension protocol v1.1.0, freeze the manifest-verified current archive pipeline's 946-record
cohort (536 B/LB, 410 P/LP, 946 gene labels). Do not invent records, manually add IDs, or tune
filters to match the historical count. The original zero-shot study is not rewritten.

Alternatives:
Construct a synthetic 78-record B/LB supplement, relax the frozen filters, or treat aggregate
counts as an identity manifest. These were rejected because none preserves source provenance or
the original estimand.

Consequences:
The ML extension has a new denominator and is not directly comparable to reports based on the
undocumented 1,024-record target without an explicit cohort caveat. Phase 3 can pass only after
the independent GRCh38 reference-base audit and all freeze artifacts pass.

Validation:
`artifacts/phase3_recovery_search_20260921.json`, `research/ml_extension/DEVIATION_LOG.md`,
and the final Phase 3 audit/freeze artifacts provide the search, source hashes, code commit,
filter funnel, count delta, overlap/leakage checks, and deterministic-regeneration evidence.

## D-063 — Freeze Broad GATK hg38/v0 as the ML-extension GRCh38 reference
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None; original protocol remains unchanged

Context:
The original protocol named `Homo_sapiens_assembly38.fasta` but did not specify an immutable
provider object, accession/build detail, byte size, FASTA checksum, FAI checksum, or contig
naming convention. That gap prevented independent base validation of the extension cohort.

Decision:
For the ML extension only, freeze the Broad Institute GATK Resource Bundle hg38/v0 uncompressed
FASTA and its provided FAI. Record the source URLs, GRCh38/build identity, retrieval timestamp,
sizes, SHA-256 values, chr-prefixed primary contig convention plus provider-supplied auxiliary
contigs, and acquisition script in
`data/manifests/grch38.json` and `research/scripts/acquire_grch38_reference.py`. Keep the large
FASTA and FAI outside Git. Record the new reference decision as ML-DEV-002 rather than changing
the original protocol.

Consequences:
The Phase 3 gate now requires an independently generated full-cohort base audit with zero
unresolved mismatches. A missing or mismatched reference remains a hard failure; alleles are
never changed to force a match.

Validation:
`artifacts/reference/grch38_validation_20260921.json` and the authoritative cohort hash
manifest record the exact reference and report status. The expected FASTA SHA-256 is
`93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564`; the expected FAI SHA-256
is `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b`.

## D-064 — Finalize Phase 5 as separated raw, embedding, and public-comparator tracks
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-061 for the final Phase 5 roster only

Context:
Real bounded H100 smokes established finite hidden states/logits and synthetic ref/alt
embedding plumbing for Nucleotide Transformer v2 and Caduceus, but neither checkpoint exposed
the frozen Evo2-style raw REF-vs-ALT likelihood contract. The Phase 5 follow-up also checked
whether public CADD and PhyloP assets could provide CPU lookup comparators without GPU
recomputation.

Decision:
Record Evo2 as `INCLUDED_RAW_SCORE`; Nucleotide Transformer and Caduceus as
`INCLUDED_EMBEDDING_TRACK` for a separately labeled future supervised representation phase;
GPN as `DEFERRED` pending its matching 100-way alignment asset; CADD and PhyloP as
`INCLUDED_RAW_SCORE` public comparator contracts with explicit non-foundation semantics and
lookup-time missingness; and AlphaMissense as `SUBSET_ONLY` for valid mapped missense variants.
Masked logits are not relabeled as raw allele-effect scores, and no public comparator asset is
treated as present until its file manifest and cohort missingness report exist.

Consequences:
The exact Phase 6 raw foundation-model set remains Evo2 only. Nucleotide Transformer/Caduceus
do not create Phase 6 results; CADD/PhyloP are low-GPU comparator candidates; all launches remain
blocked pending the final Phase 3 artifacts and a fresh scope-specific approval.

Validation:
`artifacts/model_audit/phase5_final_roster_20260921.json` records the contracts, source URLs,
coverage and missingness policy, checkpoint smoke evidence, and Phase 6/7 launch boundary.

## D-065 — Record the final Phase 3 freeze hashes and preserve the pre-Phase-6 boundary
Status: ACCEPTED
Date: 2026-09-21
Supersedes: The hash values in the earlier recovery checkpoint sections; it does not change D-062, D-063, or D-064.

Context:
The recovery, independent GRCh38 validation, and final Phase 5 roster work passed. The first
generated Phase 3 summary omitted historical provenance fields, so the freeze generator was
corrected and committed before the authoritative manifests were regenerated. The historical
1,024-record target remains unavailable and validation-only.

Decision:
Use the manifests generated by committed code `36063e8e1b65ddf1653347a5705e89115e52f1d5` as
the current ML-extension control artifacts. Preserve the source archive metadata, historical
target comparison, discrepancy investigation, and current PASS gate in the Phase 3 summary.
Keep model scoring, full Phase 6/7 execution, training, HPO, fine-tuning, and locked-test
evaluation blocked until a new scope-specific approval is granted.

Validation:
The authoritative locked-test manifest SHA-256 is
`9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb`; the canonical record-set
SHA-256 is `ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0`; the cohort
manifest SHA-256 is `0d4386b34196a523ca43b50cc4242d4ecb01df2b40923fc0aa52f15d61c593b1`; and the
restored Phase 3 summary SHA-256 is
`654c74151302e4ad5d7d9e89403e3dfb4917d19c4c7491e31403230b3888b420`. The integrity audit
SHA-256 is `e0c79be4332347b79e1647f02a12f848ec0cf4da5d8250ec2f4a0b49c8284339`, and the
independent reference report SHA-256 is
`74d5face2929e1ad6795ce950f3ec6e586bde40b464a96b2461b21265c40784f`. The resulting cohort is
946 total, 536 B/LB, 410 P/LP, 946 gene labels, and 367 unique genes, with zero unresolved
reference mismatches and deterministic regeneration PASS.

## D-066 — Complete only the approved Phase6A qualification and preserve the full-phase boundary
Status: ACCEPTED
Date: 2026-09-21
Supersedes: The Phase 6 launch-boundary language in D-064 and D-065 only for the bounded Phase6A qualification; it does not supersede their raw-score, cohort, or downstream-gate semantics.

Context:
The user-prioritized continuation supplied a dated pre-Phase-6 checkpoint that authorized a
bounded cache/comparator/throughput study, but explicitly prohibited a full 946-record Evo2
benchmark, inference over the 1,402,895-record t0 VUS pool, training, HPO, fine-tuning, and
automatic progression to Phase 6. The locked manifest contains 946 records, while the only
existing prediction cache entry is an unrelated Phase 2/4 pilot. The Phase6A approval also
authorized a very small unlabeled Nucleotide Transformer/Caduceus embedding-throughput smoke
after Evo2.

Decision:
Run and preserve Phase6A as a qualification phase only. Treat the cache preflight as 0 reusable
locked-cohort Evo2 hits and 946 potential new inferences. Qualify CADD v1.7 and UCSC phyloP100way
as public CPU comparator artifacts with row-level coverage/missingness, while retaining
AlphaMissense as a subset-only track with a measured 507-row eligible denominator and 0/507
prediction coverage. Measure canonical Evo2 `evo2_7b` on H100 using GRCh38 8192-bp
forward/reverse alternate-minus-reference scoring over sample sizes 8/16/32 and batch sizes
1/2/4/8. Record the lower-cost A100 comparison as failed closed when the pinned checkpoint
requires compute capability 8.9+ for FP8. Then run only the approved four-variant, unlabeled,
real-GRCh38 NT/Caduceus pooled-embedding smoke; do not create a feature cache. Keep CADD and
PhyloP as qualified public comparator roles but `SUBSET_ONLY` in the model registry, so the
exact Evo2-only raw benchmark inclusion set cannot silently widen; keep AlphaMissense
`SUBSET_ONLY`, and keep NT/Caduceus `SUBSET_ONLY` embedding tracks. Keep the scientific result
registry empty and stop at the Phase6A boundary.

Alternatives:
Launch the full 946-record Evo2 inference based on the measured rate estimate, treat the
unrelated pilot cache or historical aggregate metrics as reusable outputs, promote masked-LM
hidden states/logits to raw allele-effect scores, download AlphaMissense predictions, retry the
A100 with changed precision or a changed checkpoint, or begin feature extraction/training after
the smoke. These were rejected because they would exceed the approved scope, change score
semantics, erase explicit missingness/compatibility evidence, or cross the required phase gate.

Consequences:
Phase6A is `PASS` within its bounded qualification scope. The full Phase 6 zero-shot benchmark
remains `BLOCKED / NOT STARTED`; the full Phase 7 extraction remains `BLOCKED / NOT STARTED`;
and no downstream phase, scientific metric, locked-label selection, feature cache, or result
registry record is created. The H100 throughput estimate is planning evidence only: it does not
authorize the full run or constitute a scientific result. The A100 failure is a hardware/runtime
compatibility constraint for this pinned Evo2 checkpoint, not an A100 throughput measurement.

Validation:
Implementation commit: `4e072ef` (`feat: complete bounded phase6a qualification`).
The approval is `artifacts/approvals/phase6a_throughput_20260921.json`. Cache, comparator, Evo2,
representation, and registry evidence are respectively recorded in
`artifacts/phase6a/phase6a_cache_preflight_20260921.json`,
`artifacts/phase6a/phase6a_comparator_qualification_20260921.json`,
`artifacts/phase6a/phase6a_evo2_throughput_20260921.json`,
`artifacts/phase6a/phase6a_representation_throughput_20260921.json`, and
`artifacts/phase6a/phase6a_registry_update_20260921.json`. `make model-registry-verify` and
Ruff passed for the updated scripts/manifests. The two throughput artifacts record a combined
client wall-rate estimate of `$0.560167`; Modal workspace snapshots remained `$0.00` billed.

## D-067 — Continue the remaining phases only under a current exact-scope approval
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-066 only for the active task objective; it does not widen the Phase6A approval or change any scientific contract

Context:
The active task now requests completion of every remaining phase after the previously completed
Phase6A qualification. D-066 and `artifacts/approvals/phase6a_throughput_20260921.json` were
deliberately limited to the bounded qualification and explicitly prohibited full Phase 6 and
downstream work. The repository also contains `artifacts/approvals/full_run_approval.json`, but
that record is dated 2026-08-19 and carries the legacy identifier
`frozen_v1.0.0_2026-08-18`, not the current frozen ML-extension protocol hash. The current cost
policy rejects it before any remote execution.

Decision:
Treat the active user request as authorization to continue preparing and, once properly gated,
executing the remaining phases. Do not interpret the request as a fabricated or implicit numeric
Modal budget, do not edit either existing approval to widen its scope, and do not launch paid work
until a current approval artifact covers the exact cohort, model revision, workload, and budget.
Keep Phase6A as `PASS` within its original scope, keep the scientific result registry empty, and
continue only free/local validation or independent engineering work while the full-run approval
is absent. The first paid continuation must be a bounded full-Phase-6 parity/cohort step, followed
by the dependency-ordered Phase 7 through Phase 19 gates.

Alternatives:
Reuse the stale `$500` August approval, treat the Phase6A `$1.50` approval as covering the full
946-record run, or infer an unlimited budget from the phrase “finish everything.” These were
rejected because they would bypass the repository's cost policy, exceed the explicitly recorded
scope, and make the resulting scientific evidence unauditable.

Consequences:
The current phase is continuation preparation, not a scientific Phase 6 PASS. Full Phase 6,
full Phase 7 extraction, and all dependent scientific phases remain `BLOCKED`/`NOT_STARTED`.
Local gates may be rerun and implementation gaps may be closed without changing the locked
protocol. A new approval must be hash-checked against
`39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3` before remote work.

Validation:
At the current HEAD before this documentation update, `make validate` passed 656 tests with
33 deselected and 95.12% coverage; ML protocol, schema, model-registry, registry, and frontend
build gates passed; `make figures` and `make release-check` remained truthfully blocked with no
registered scientific outputs. `require_full_run_approval()` rejected the August artifact with
the exact current-protocol-hash mismatch. A read-only Modal billing summary reported `$13.00`
metered and `$0.00` billed, with no new remote workload launched.

## D-068 — Use an approval-gated, resumable Phase 6/7 execution contract
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The Phase6A qualification measured a bounded Evo2 throughput envelope, but no current
approval exists for the full locked-cohort benchmark or representation extraction. The
repository therefore needed a real execution surface that is safe to validate locally and
cannot silently turn a stale approval, a malformed manifest, or a partial remote response into
scientific output.

Decision:
Use `src/evovariant_tr/phase_execution.py` and `scripts/phase_execute.py` as the canonical
Phase 6/7 cohort runner. Before a caller constructs the remote transport, the runner requires
the paid-compute acknowledgement, a current approval whose protocol hash matches the current
ML-extension protocol, and every requested workload token in the approval scope. Manifest rows
retain their source spelling and their canonical UCSC/Modal `chr` identity; request payloads
contain only variant fields and never labels. Score and embedding responses must be completed,
finite, identity-complete, and layer-compatible. Each shard is written atomically with a
content hash and is skipped only after verification, so interrupted work can resume without
recomputing completed shards. The Modal app exposes a bounded `extract_embeddings_batch`
endpoint with the same partial-failure semantics as `score_batch`. The runner emits raw,
provenance-bearing predictions/features and no fabricated metrics.

Alternatives:
Use the stale August full-run approval, widen the Phase6A approval, send labels to the remote
endpoint, accept partial/unknown rows, or rely on the existing status-only Make targets. These
were rejected because they would bypass the cost policy, weaken leakage controls, or make a
future result unreproducible.

Consequences:
The Phase 6/7 execution engineering subgate is locally validated, but it is not a scientific
Phase 6 or Phase 7 pass. No remote request, model download, feature cache, prediction cache, or
registry result was created in this change. Full execution remains blocked until a current
exact-scope approval and the dependent endpoint/model evidence are present.

Validation:
`make validate` passed with 672 tests, 33 deselected, strict mypy, Ruff, secret scanning, and
95.02% total coverage. The targeted Phase 6/7 contract suite passed 19 tests; `evo2_scorer_app.py`
compiled and its source lint passed. `make phase-execute` defaults to `--help` and makes no
network request. Implementation commit: `82ff2d6` (`feat: add gated resumable phase execution`).

## D-069 — Execute downstream training and HPO only from verified development feature artifacts
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The repository already had deterministic CPU classifier and validation-only HPO primitives, but
no artifact-driven entry point connected them to the Phase 7 feature contract. A downstream
implementation must not silently train on a locked row, a mixed model/layer cache, a tampered
vector, or a shared gene group.

Decision:
Use `src/evovariant_tr/downstream_pipeline.py`, `scripts/train_from_features.py`, and
`scripts/hpo_from_features.py` for Phase 8/9 local work. The loader accepts only content-hashed
TRAIN and VALIDATION JSONL feature rows, requires binary labels and gene symbols, verifies the
feature content hash, rejects locked-test rows and cross-split identity/gene leakage, and records
the feature-artifact hash. Phase 8 fits logistic regression, a transparent decision stump, and a
small MLP on TRAIN and reports an explicit metric panel on VALIDATION only. Phase 9 runs a bounded
logistic search whose objective is AUROC on VALIDATION only; search configurations and the chosen
trial are written separately. Neither command opens a remote endpoint or creates a final result
registry record automatically.

Alternatives:
Train directly from arbitrary NumPy/CSV files, infer missing gene metadata, select by locked-test
performance, or add a heavyweight ML dependency before the feature contract is proven. These
were rejected because they would weaken reproducibility, leakage controls, or the local-first
compute policy.

Consequences:
The Phase 8/9 engineering surfaces are implemented and tested, but their scientific gates remain
`BLOCKED / NOT STARTED` until an approved Phase 7 extraction produces a real development feature
artifact. Synthetic fixtures in the test suite are software tests only and cannot enter the
experiment registry or figure bundle.

Validation:
`make train` and `make hpo` remain truthful `BLOCKED` status surfaces when `FEATURES` and, for
HPO, `HPO_CONFIGS` are unset. With explicit paths they invoke only the local CPU scripts.
`make validate` passed with 676 tests, 33 deselected, strict mypy, Ruff, secret scan, and 95.01%
coverage. The new downstream contract suite passed 4 tests. Implementation commit: `af97560`
(`feat: add local downstream training and hpo runners`).

## D-070 — Analyze ensembles, calibration, and abstention on development predictions only
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The repository had isolated ensemble, calibration, and risk-coverage primitives, but no
artifact-driven analysis boundary tying them to the validation-only selection rule. A shared
prediction file can also accidentally contain locked-test rows or duplicate model/variant rows.

Decision:
Use `src/evovariant_tr/analysis_pipeline.py` and `scripts/analyze_ensemble.py` for the local
Phase 11/12 analysis surface. The loader validates JSONL identity, split, labels, finite scores,
and duplicates, and rejects locked-test rows by default. The analysis requires common validation
IDs, computes pairwise disagreement/error overlap/correlation, applies a fixed weighted mean,
reports discrimination/calibration metrics, and emits risk-coverage and abstention curves. A
probability-to-logit transform is used only for the existing abstention primitive's zero-centered
score contract. Output is an immutable local artifact; it is not automatically promoted to the
result registry.

Alternatives:
Choose ensemble members from locked-test scores, silently intersect incomplete model coverage,
use a raw probability as a zero-centered abstention score, or write over an existing analysis
artifact. These were rejected because they would leak selection information, hide missingness,
misstate score semantics, or destroy provenance.

Consequences:
The Phase 11/12 engineering surface is implemented and tested, but the scientific phases remain
`BLOCKED / NOT STARTED` because no real development prediction artifact exists. Phase 13's
predeclared ablation/robustness matrices remain available but cannot be evaluated without frozen
base predictions.

Validation:
`make ensemble` remains a truthful `BLOCKED` status surface unless explicit prediction/model
paths are supplied. `make validate` passed with 679 tests, 33 deselected, strict mypy, Ruff,
secret scan, and 95.00% coverage. The new analysis contract suite passed 3 tests. Implementation
commit: `a3df7ac` (`feat: add validation-only ensemble analysis`).

## D-071 — Keep phase status surfaces aligned with the accepted continuation state
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
After the Phase3 recovery/deviation and Phase6A qualification, several Make/benchmark status
messages still described the earlier pre-recovery state. A stale blocker message is itself a
reproducibility defect because it can misdirect the next agent and contradict the persistent
project state.

Decision:
Phase 6 status surfaces must identify the actual blockers: no current exact-scope approval, no
full-cohort batch parity/endpoint evidence, and no registered scientific Phase 6 result. Phase 7
must identify the absent approved full extraction and feature cache. Release status must identify
unresolved scientific artifacts, locked evaluation, registry/figure, and approval gates. The
accepted Phase 3 ML-extension deviation and Phase6A PASS are not reported as current blockers.

Consequences:
Status artifacts remain `BLOCKED` without inventing a run, but their reasons now match the
authoritative state. Historical ledger entries retain their original wording as historical
evidence; only current command surfaces were changed.

Validation:
`make benchmark-zero-shot`, `make extract-features`, and `make release-check` each wrote
truthful blocked status artifacts. `make validate` passed with 679 tests, 33 deselected, strict
mypy, Ruff, secret scan, and 95.00% coverage. The change is local-only and has no compute cost.

## D-072 — Add a frozen, one-shot locked-test evaluation guard
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The downstream analysis surfaces are now locally implemented, but no real Phase 7 feature cache,
development prediction artifact, or current approval exists. The Phase 14 surface therefore needs
to remain blocked by default while providing a correct path for a future, already-frozen final
evaluation. A generic evaluator would be unsafe if it could select a model, tune a threshold, or
overwrite a prior locked result from test labels.

Decision:
Use `src/evovariant_tr/final_evaluation.py` and `scripts/evaluate_locked.py` as the only local
Phase 14 evaluation entry point. The evaluator requires a content-hashed configuration with
`selection_closed=true`, an explicit score direction and threshold, a positive bootstrap count,
one model's `LOCKED_TEST` prediction rows, both labels, and a matching caller-supplied config hash.
It harmonizes raw scores before computing the fixed-threshold metrics and bootstrap AUROC interval,
writes an immutable provenance-bearing artifact, and refuses to replace an existing output. The
Make target remains a truthful blocked status surface unless all explicit locked-prediction,
configuration, hash, and model variables are supplied.

Alternatives:
Reuse the validation-only ensemble path, allow threshold selection from locked labels, accept a
stale approval as authorization, or overwrite a prior evaluation artifact. These were rejected
because they would mix development and test roles, leak selection information, bypass the current
approval boundary, or destroy result provenance.

Consequences:
The Phase 14 engineering guard is implemented and locally validated, but the scientific Phase 14
gate remains `BLOCKED / NOT STARTED`. No locked prediction was evaluated, no model or threshold
was selected, and no scientific result registry entry or figure input was created. Phases 15-19
remain blocked on the same absent real scientific outputs and approval dependencies.

Validation:
`make validate` passed with 684 tests, 33 deselected, strict mypy over 56 source files, Ruff,
secret scanning, and 95.04% coverage. `make evaluate` with default variables wrote a blocked
status artifact and made no network or paid-compute request. Implementation commit: `1423577`
(`feat: add frozen locked evaluation guard`).

## D-073 — Refresh all no-spend control-plane and downstream status surfaces
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
After the Phase 14 engineering guard was added, the remaining local gates needed a fresh run so
the checkpoint would distinguish current reproducibility evidence from older historical runs.
These commands must not be used to imply that absent remote inference or scientific result
artifacts exist.

Decision:
Run the free protocol, schema, registry, scientific-test, E2E, frontend, figure, and downstream
status commands and preserve their actual outcomes. Treat the control-plane checks as PASS only
for their respective local contracts. Treat the scientific Phase 6-19 surfaces as BLOCKED when
their required remote predictions, feature artifacts, locked results, or registry inputs are
absent. Preserve the frontend build warnings as warnings rather than hiding them.

Consequences:
The current no-spend checkpoint is reproducible: ML protocol, schema, model-registry, and
experiment-registry checks pass; the scientific tier is 7 passed/1 skipped; the E2E tier is
14 passed/1 skipped; and the frontend build succeeds. The figure manifest has zero available
figures, and Phase 6/7/8/9/11/12/13/14/15/16/17/18/19 status surfaces remain blocked. No
remote endpoint, model download, training, locked evaluation, deployment, release, or push was
performed by this refresh.

Validation:
`make ml-protocol-verify`, `make schema-verify`, `make model-registry-verify`, `make
registry-verify`, `make test-scientific`, `make test-e2e`, `make web-check`, `make figures`,
and the Phase 6-19 status commands all completed with truthful output. The frontend build
reported two existing Turbopack warnings about dynamic filesystem access in
`apps/web/src/app/api/registry/route.ts`; no warning was promoted to a failure.

## D-074 — Record the current no-spend Modal preflight boundary
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The development environment now has Modal authentication, but authentication is not approval for
new paid work. The checkpoint needs fresh workspace-level billing and task evidence without
launching a model or endpoint.

Decision:
Use `make modal-smoke` as the no-spend authentication/preflight check. Record its result as
`PLANNED` with zero GPU count and no measured or estimated per-request cost. Treat `modal billing
summary` and `modal app list` as workspace observations only; they are not a substitute for a
current exact-scope approval or a per-request invoice.

Consequences:
Modal authentication is verified, but the full Phase 6/7 workload remains blocked. The fresh
workspace snapshot reports `$13.00` metered cost and `$0.00` billed cost; the listed deployed and
stopped app entries have zero tasks. No remote invocation, model download, training, or paid
workload was started by this preflight.

Validation:
`make modal-smoke` returned `modal_installed=true`, `modal_authenticated=true`, `gpu_count=0`,
`status=PLANNED`, and the note `no remote invocation requested`. The read-only billing and app
listing commands completed successfully.

## D-075 — Keep current project-state metadata aligned with the checkout
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The top of the persistent project-state file still named a pre-continuation commit as the
current HEAD, even though subsequent implementation and documentation commits had been validated.
That drift could cause a future agent to inspect the wrong checkpoint.

Decision:
Record the current branch, full HEAD, continuation implementation commits, and continuation
documentation commits explicitly at the top of `PROJECT_STATE.md`. Preserve the older Phase 3
freeze commit as historical baseline evidence rather than relabeling it as the current checkout.

Consequences:
The persistent state now distinguishes the latest code-bearing validated checkout (`1423577`)
from later documentation-only commits and retains the untracked `.agents/` ownership boundary.
No scientific phase status or approval scope changed.

Validation:
`git status --short --branch`, `git rev-parse HEAD`, the recent commit log, and the current
`make validate`/control-plane results agree with the corrected metadata.

## D-076 — Execute the explicitly approved bounded development continuation
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The user supplied a current continuation checkpoint and explicitly authorized the Phase 6/7
development scope, then increased its maximum budget from `$3.00` to `$5.00`. The approval is
separate from both the stale August full-run approval and the earlier `$1.50` Phase6A throughput
approval. The current protocol, development manifest, model revision, orientation rule, and
locked-test exclusion had to remain exact while making progress possible.

Decision:
Use `artifacts/approvals/phase6_phase7_development_20260921.json` as the sole authority for this
continuation. Run a deterministic, resumable Evo2 `evo2_7b` H100 development prefix on TRAIN and
VALIDATION only, with locally reconstructed 8192-bp GRCh38 reference/alternate forward and
reverse-complement sequences. Never send labels or locked identifiers to Modal. Stop at the
runner's `$4.75` rate-estimate reserve under the `$5.00` cap, then run only local CPU adapters,
training, validation-only HPO, fixed validation-only ensemble/calibration/abstention analysis,
and the feasible predeclared Phase 13 subset matrix. Do not widen the run into full-cohort
inference, NT/Caduceus extraction, fine-tuning, locked evaluation, registry promotion, release,
or deployment.

Consequences:
The run produced a truthful `PARTIAL_BUDGET_STOP` artifact with 2,848 of 239,992 development
rows and a verified four-feature raw-score adapter. Local Phase 8/9/11/12/13 subset artifacts
are usable for engineering and preliminary validation-only diagnostics, but they cannot support
full-cohort or confirmatory claims. NT/Caduceus representations, context-shift robustness,
external comparator joins, fine-tuning, Phase 14, result registry, figures, release, and
deployment remain unresolved. A future continuation requires a new explicit scope/budget.

Validation:
The final artifact is `artifacts/phase6/phase6_development_evo2_20260921.json`; its SHA-256 is
`be5edd45942a70f494512c111dd1245f2d721c1a10f909e9de03524f5a22cfe5`. The approval SHA-256 is
`f903a8ebed963e5c82e5a7578c54fc674685f1b5c1f445b23e38fd4b895fb50a`. The local manifest/prefix,
split counts, labels, raw-score arithmetic, zero locked overlap, shard hashes, and all downstream
validation boundaries passed. Implementation fixes are `69a2e4f` and `0f1c5a4`; the current
Modal workspace snapshot is metered `$19.34` and billed `$0.00`, with per-run invoice USD
unavailable. No push or deployment was performed.

## D-077 — Register bounded development results as preliminary and connect the UI
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The current approved continuation produced real, hash-verified development-subset outputs, but
the experiment registry was still empty and the workbench therefore could not display even their
provenance. The output files under `research/runs/` are intentionally regenerated and ignored by
Git, so registry records also need small tracked summaries that preserve source hashes and scope.

Decision:
Use `scripts/register_development_subset_results.py` as the narrow registration surface. It
materializes tracked summaries and partial figure inputs under
`artifacts/registry/development_subset_20260921/`, validates the approved protocol/development
manifest and locked-test boundary, and registers the bounded Phase 6/7/8/9/11/12/13 outputs plus
the figure-source bundle as completed `PRELIMINARY` runs. The UI may treat those runs as real
metadata, but no record may be promoted to `FINAL` from this dirty/development-subset state.
Missing source families continue to block the Phase 17 renderer.

Alternatives:
Leave the registry empty, register ignored raw files without tracked summaries, or label the
subset outputs `FINAL`. These were rejected because they would hide verified provenance, make a
fresh checkout unable to verify the registry, or overstate incomplete validation-only evidence.

Consequences:
Phase 16 is `PARTIAL / PRELIMINARY REGISTRY CONNECTED`; the workbench registry route and browser
journey now expose seven completed preliminary records. Phase 17 is still `BLOCKED / PARTIAL
SOURCES`; 9/19 figure families and 9/12 tables have real source artifacts, but the bundle emits
zero scientific outputs until every required source is available. Phase 14, full clean-room
science, release, deployment, and publication remain blocked or excluded.

Validation:
`make registry-verify`, `make ui-check`, `make web-check`, and `make web-e2e` passed. The Phase 17
manifest is `BLOCKED` with seven eligible completed runs, 9 available figure families, 9 available
tables, and the ten explicitly missing source families. No locked-test row was consumed and no
remote or paid compute was started by this registration step.

## D-078 — Fit development calibration maps only on TRAIN
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The fixed development-subset ensemble already had uncalibrated ECE, risk-coverage, and
abstention diagnostics, but the protocol requires a Platt/isotonic comparison and a calibration
effect ablation. The current approval permits local CPU Phases 11-13, while prohibiting any
locked-test selection.

Decision:
Fit deterministic Platt and weighted isotonic maps on aligned TRAIN rows only, then evaluate
each map once on aligned VALIDATION rows. Keep the uncalibrated ensemble as the reference,
record all fit/evaluation counts and parameters, and register both the calibration comparison
and the Phase 13 calibration-effect summary as `PRELIMINARY`. Do not choose a calibrator from
the locked test and do not promote any method to `FINAL`.

Alternatives:
Fit on VALIDATION, choose the method after reading locked labels, or omit the required
calibration sensitivity because isotonic is high-capacity. These were rejected because they
would leak evaluation information or leave a required development analysis unrecorded. The
high-capacity isotonic result is retained as sensitivity evidence with its 311 fitted blocks,
not as a final selected method.

Consequences:
Phase 12 is now `PARTIAL / DEVELOPMENT CALIBRATION SUBSET`, and the feasible Phase 13
calibration-effect cell is complete. The overall ML extension remains partial: all metrics are
from 572 VALIDATION rows in a 2,848-row processed prefix, and full cohort, multi-model,
embedding, comparator, locked-test, release, and publication gates remain unresolved.

Validation:
The calibration runner completed with 2,276 TRAIN fit rows, 572 VALIDATION evaluation rows,
and `locked_test_evaluated=false`. Preliminary validation ECE was `0.0843577465` uncalibrated,
`0.0727681965` Platt, and `0.0389348144` isotonic. `make calibration-abstention` remains
blocked without explicit input paths, `make registry-verify` passes with nine eligible
preliminary runs, and no remote or paid compute was used.

## D-079 — Add a label-free local Phase 15 batch contract without widening compute scope
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
Phase 15 had low-level shard primitives and a bounded single-variant Modal surface, but it did
not provide a reviewable input-to-plan boundary or a deterministic local recovery/export path.
The current `$5.00` approval is exhausted and explicitly excludes a full cohort, remote batch
parity, and kill/restart smoke. The repository still needs useful engineering progress without
silently converting a plan into a scientific run.

Decision:
Implement `src/evovariant_tr/batch_pipeline.py` as a free local contract. Accept only label-free
GRCh38 biallelic SNVs from canonical CSV or VCF/VCF.GZ, normalize identities with the shared
variant schema, hash the input, and persist an immutable model/checkpoint/revision/context/
orientation plan before scoring. Use an injected scorer for local contract tests only. Persist
atomic content-hashed shard envelopes with exact ordered IDs, failure taxonomy, explicit retry,
and deterministic plan-order export. Reject outcome/label fields, tampered or stray shards,
duplicate IDs, and malformed result shapes. Expose planning through `scripts/plan_batch.py` and
`make batch-run`; planning must report `PLANNED` and must not invoke Modal or create scientific
outputs.

Alternatives:
Wire the Make target directly to Modal, infer a scorer from the configured endpoint, accept
annotated/outcome-bearing input, or keep the status-only surface. These were rejected because
they would spend outside the approval, create an unreviewable label boundary, or leave the
required Phase 15 recovery contract untestable.

Consequences:
Phase 15 is `BLOCKED / LOCAL CONTRACT READY`, not PASS. The tracked three-row sample plans to
one shard with input SHA-256
`d0778b9ad572f7aa6d9b48f0d6675b1e8bd29180826ba0834aa64eff799f7378`; no remote call, model
download, label transfer, or paid workload occurs. Remote parity, kill/restart recovery,
full-cohort execution, and scientific registration still require a new exact-scope approval.

Validation:
Implementation commit `6196dc5`; targeted batch tests pass, `git diff --check` passes before
documentation changes, and `make batch-run BATCH_INPUT=examples/batch/variants.csv
BATCH_MODEL_REVISION=4b509ec2a22d6de472659f908bcb0714265ad3a7` reports `PLANNED` with three
variants and one shard. The full `make validate` rerun is recorded in the current project state.

## D-080 — Separate preliminary figure output from the final Phase 17 bundle
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The registry now contains nine hash-verified development-subset runs and real source artifacts
for 9/19 figure families and 9/12 tables. The final renderer correctly refuses to produce a
scientific bundle while ten required source families are absent, but the workbench and
engineering reviewers still need a deterministic way to inspect available artifact wiring.

Decision:
Add a separate `render_preliminary_figure_bundle` surface and `make figures` output under
`research/figures/preliminary/`. It may render only available registered sources and must mark
the manifest `status: PARTIAL`, `evidence_stage: PRELIMINARY`, and `promotable: false`. Keep the
existing final renderer fail-closed with `status: BLOCKED` and zero scientific outputs until all
required source families are present. Update the registry API and workbench to report `PARTIAL`
when completed preliminary runs exist but no `FINAL` run is registered.

Alternatives:
Treat preliminary outputs as final, leave the UI in a misleading `READY` state, or fill missing
families with placeholders/inferred values. These were rejected because the outputs are
development-subset diagnostics and the master prompt requires source-complete, registry-backed
final artifacts.

Consequences:
The preliminary bundle contains 9 figures, 9 tables, and 18 hash-addressed output files, with
manifest SHA-256 `026a82c02e1151d9bade98744bbd07c11d4c1e2ca7630b4b8ec3fda744cc9d40`. It is useful
for engineering review but cannot satisfy Phase 17, Phase 18, or Phase 19. The final bundle
remains blocked, the API/UI remains truthful, and no scientific claim or locked-test result is
promoted.

Validation:
Implementation commit `6196dc5`; `make figures` produced the blocked final manifest and the
separate non-promotable preliminary manifest; `make registry-verify`, `make ui-check`,
`make web-check`, and `make web-e2e` pass. No remote or paid compute was used.

## D-081 — Keep conditional figure families explicit without weakening the final gate
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The registry-driven Phase 17 manifest had a required `finetuning.json` table source even though
the project-control record already marked Phase 10 fine-tuning `DEFERRED_BY_COMPUTE`. Treating that
conditional source as an unconditional missing source would make the final bundle permanently
blocked for a study decision that is explicitly allowed by the master plan. Treating it as
available would fabricate evidence.

Decision:
Extend the figure/table manifest contract with explicit applicability metadata. A conditional
source may become `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` only when an exact decision artifact
exists and has the expected status. For the current Phase 10 decision, `finetuning.json` is
documented as not applicable with the reason that fine-tuning was not executed due to the compute
budget deferral. The final bundle still requires every mandatory core source, a hash-valid
completed `FINAL` registry run, and all applicable outputs.

Alternatives:
Keep fine-tuning unconditionally blocking, silently omit the family, fabricate a placeholder
plot/table, or make all missing families conditional. These were rejected because they either
misrepresent an explicit deferral or weaken the core scientific gate.

Consequences:
The manifest schema is `1.2`. The current final status remains `BLOCKED`: nine of nineteen figure
families and nine of eleven applicable tables are available, nine core source families are still
missing, and no `FINAL` run is registered. The fine-tuning table is visible in the manifest's
not-applicable list with its decision artifact and reason. The existing preliminary outputs remain
non-promotable.

Validation:
`tests/unit/test_figure_artifacts.py` passes 13 tests; strict mypy passes for the touched figure
source and Ruff passes for the touched source, test, and design script; `make figures` produces a blocked final manifest and a separate
non-promotable preliminary bundle without invoking Modal.

## D-082 — Freeze a deterministic budgeted development subset before new scoring
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The existing 2,848-record Evo2 development run was an ascending SHA-256 normalized-ID prefix
stopped by a paid-compute safety reserve. Its downstream artifacts are valid `PRELIMINARY`
engineering/research evidence but are not a formal model-selection sample. Sequentially scoring
all 239,992 available development records is not financially justified, and the existing `$5.00`
approval is exhausted.

Decision:
Adopt additive study amendment `ML-DEV-BUDGETED-001`. Keep the complete 239,992-record frozen
development population and the untouched 946-record `LOCKED_TEST`. Before any future scoring,
freeze a 4,000-record subset with a 5,000-record maximum without another approval. Select within
the frozen TRAIN/VALIDATION and class strata by ascending
`SHA256(normalized_variant_id + '|' + 'ML-DEV-BUDGETED-001|2026-09-21|sha256-v1')` using the
largest-remainder allocation. Do not read model predictions for selection, and use the same exact
manifests for every formal track.

The frozen allocation is TRAIN 3,199 (2,645 negative, 554 positive) and VALIDATION 801 (581
negative, 220 positive), totaling 3,226 negative and 774 positive records across 1,927 unique
genes. TRAIN/VALIDATION gene overlap and locked-test overlap are zero; 56 IDs overlap the old
prefix and are counted only as potential cache reuse.

Alternatives:
Resume sequential full-population scoring, continue using the first/old prefix as formal, select
by model predictions, or tune subset size against locked-test outcomes. These were rejected because
they exceed the budget rationale, fail reproducibility or leakage controls, or turn the locked test
into a selection instrument.

Consequences:
The protocol amendment, formal train/validation/development manifests, population-vs-subset QC,
metadata audit, source metadata aggregate, and manifest hash index are stored under
`research/ml_extension/splits/formal_budgeted_20260921/`. The audit concludes that the old prefix
is `NOT_ESTABLISHED` as representative. The cost plan estimates Evo2 `$6.506744`, NT `$0.378539`,
Caduceus `$0.226398`, and `$7.111681` total using measured rates. No new Modal job or model
download is authorized by this decision; a fresh exact-scope approval and reserve are required.

Validation:
`scripts/design_budgeted_development_study.py` completes the audit and design twice
idempotently, with no network or paid-compute call. The formal subset has unique IDs, remains in
the authoritative population, preserves frozen split/class/gene constraints, has zero locked-test
overlap, and has stable SHA-256 manifest hashes. The amendment is recorded in
`research/ml_extension/AMENDMENT_ML-DEV-BUDGETED-001.md`.

## D-083 — Use an explicit compute-deferral status for the Phase 10 command surface
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The authoritative Phase 10 decision and conditional figure policy use `DEFERRED_BY_COMPUTE`, but
the generic `phase-status` CLI and `make finetune-smoke` surface only emitted the less specific
`DEFERRED` value.

Decision:
Add `DEFERRED_BY_COMPUTE` to the execution-status and CLI contracts, and make
`make finetune-smoke` emit that exact status. Preserve the generic `DEFERRED` value for other
resource or workflow deferrals that do not have the Phase 10 compute-specific decision.

Consequences:
The Phase 10 status is now machine-readable and consistent across the decision artifact, phase
ledger, figure applicability policy, CLI, and Make surface. This does not authorize training or
change the compute boundary.

Validation:
`make finetune-smoke` writes `research/runs/phase10_ft_status.json` with
`status: DEFERRED_BY_COMPUTE`; the CLI and experiment-framework tests pass, and strict mypy/Ruff
pass for the touched source and test.

## D-084 — Execute the exact-scope ML-DEV-BUDGETED-001 continuation under the new user authorization
Status: ACCEPTED
Date: 2026-09-21
Supersedes: The no-spend-only execution boundary in D-082 for this authorization window; it does not alter the frozen amendment or historical preliminary results.

Context:
The additive `ML-DEV-BUDGETED-001` design is frozen at 4,000 development records, but the prior
`$5.00` approval was consumed by the 2,848-row preliminary Evo2 prefix. The user has now supplied
an explicit checkpoint authorizing the formal development study with a maximum additional Modal
compute of `$8.00` and a runner safety stop of `$7.75`. This authorization is narrower than the
master protocol: it excludes the 946-record locked test, Phase 14, full-population scoring,
fine-tuning, context/center GPU sweeps, GPN GPU work, deployment, release, and publication.

Decision:
Proceed through the pre-Phase-14 boundary only after the current validated changes are committed
and a fresh approval artifact is created and validated against the current ML protocol hash,
formal manifest hashes, combined record-set hash, current commit, model revision, H100 identity,
exact workloads, and stop conditions. Materialize CADD/PhyloP evidence for the exact 4,000 rows
before GPU work. Run a deterministic 64-row Evo2 preflight, compare its measured rate with the
frozen estimate, and continue resumably only while the `$7.75` safety stop and `$8.00` hard cap
remain satisfied. Reuse only the 56 rows independently verified as scientifically compatible
historical cache results. Extract the predeclared NT and Caduceus layers with labels excluded from
the remote boundary, then perform Phases 6-13 locally on TRAIN/VALIDATION only and stop before
Phase 14. Phase 10 remains `DEFERRED_BY_COMPUTE`.

Alternatives:
Continue the previous no-spend stop, silently widen the budget, score all 4,000 immediately,
reuse the old prefix as a formal sample, score the locked cohort, or replace missing comparator
values with zeros or class labels. These were rejected because the new user authorization permits
the exact formal study but does not waive its staged-cost, provenance, leakage, or stop controls.

Consequences:
The formal runner and representation runner are approval-gated, resumable, and fail closed on
hash, identity, provenance, schema, projection, or budget violations. The formal 4,000-row result
will supersede neither the preliminary 2,848-row artifact nor the locked cohort. A separate
authorization is still required for Phase 14 and any final or release claim.

Validation:
The protocol hash is refreshed to the additive amendment, the frozen formal manifest hashes and
`b4559171...` combined record-set hash are independently verified, the cost wording reports the
positive `$2.111681` excess over the old cap, and local engineering gates remain green before the
new approval is written.

## D-085 — Require exact formal comparator qualification and a measured Evo2 preflight projection
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The formal development amendment permits CADD, PhyloP, AlphaMissense, Evo2, Nucleotide
Transformer, and Caduceus tracks on one exact 4,000-row TRAIN/VALIDATION cohort. The new user
authorization is bounded by a `$7.75` runner stop and an `$8.00` hard cap, so the frozen planning
estimate alone is not sufficient evidence to launch the full Evo2 workload.

Decision:
Complete exact-cohort CADD/PhyloP/AlphaMissense qualification locally before GPU work and require
a deterministic 64-row Evo2 preflight before the full 4,000-row Evo2 run. The preflight must
verify completion, finite four-view scores, hash-verified predictions, remote label exclusion,
historical-cache accounting, and a conservative measured cost projection. The full runner refuses
to start unless the local projection artifact passes and remains at or below `$7.75`.

Evidence:
`artifacts/phase6a/comparators/phase6a_comparator_qualification_20260921.json` records CADD
coverage 2,891/4,000, PhyloP coverage 3,997/4,000, AlphaMissense zero eligible predictions,
`modal_invoked: false`, and `labels_read_for_scoring: false`. Missing comparator values remain
explicitly missing. `scripts/validate_formal_preflight.py` writes the separate measured projection
gate after the sample artifact exists.

Consequences:
The formal study remains staged and fail-closed. A fast or incomplete sample cannot silently
authorize the full run; conversely, a full run cannot be launched based only on a planning number.
The 946-row locked test, Phase 14, and final/release claims remain outside this decision.

## D-086 — Stop after two identical Modal preflight stream failures
Status: ACCEPTED
Date: 2026-09-21
Supersedes: The immediate retry portion of D-085 for this authorization window

Context:
The exact-scope approval and comparator gates passed, but the deterministic 64-row Evo2 preflight
was attempted twice under the approved `$8.00` hard cap and `$7.75` runner safety stop. Both
attempts completed image construction and then ended before any H100 worker/container returned a
score, with `StreamTerminatedError: Connection lost`. Modal billing remained `$19.33` metered and
`$0.00` billed before and after, and no active container remained.

Decision:
Stop paid execution at the failed preflight gate. Preserve the final failed sample artifact and
the `FAIL_FORMAL_PREFLIGHT` projection artifact. Do not launch the 4,000-row Evo2 run, NT/Caduceus
representation extraction, or downstream formal Phases 6-13 until the external Modal
scheduling/transport problem is resolved and a fresh explicit continuation decision authorizes a
new bounded attempt.

Consequences:
The formal 4,000-row study is not a PASS and has no scientific metrics. The old 2,848-row Evo2
prefix remains preliminary, the 946-row locked test remains untouched, Phase 14 remains blocked,
and no final, release, deployment, publication, or clinical claim is made. Local control-plane
and comparator evidence remains valid and reusable.

Validation:
`artifacts/phase6/phase6_formal_evo2_20260921_sample64.json` records `FAILED`, zero completed
shards, zero remote rows, and `labels_sent_to_modal: false`; the two app IDs are recorded in the
phase ledger and project state; `artifacts/phase6/formal_budgeted_preflight_gate_20260921.json`
records `FAIL_FORMAL_PREFLIGHT` and no full-launch authorization.

## D-087 — Use durable Modal FunctionCall polling for the next bounded attempt
Status: ACCEPTED
Date: 2026-09-21
Supersedes: The synchronous result-collection path in the formal Evo2 runner

Context:
Both failed preflight attempts ended after approximately five minutes with no worker/container
score and `StreamTerminatedError: Connection lost`. The runner used the synchronous
`worker.score_batch.remote(...)` result path, which ties queue/startup waiting to the client output
stream. The installed Modal SDK is 1.5.4 and exposes a durable `.spawn()` FunctionCall with
server-side `.get(timeout=...)` polling.

Decision:
Change the formal Evo2 runner to submit each shard through `score_batch.spawn(...)` and retrieve
the result through `FunctionCall.get(timeout=900)`. Set the class startup timeout explicitly to
the same 900-second bounded batch timeout. Preserve `retries=0`, the atomic shard contract, the
existing approval caps, and the two-failure stop; this change does not authorize a new paid run.

Consequences:
The next approved attempt can survive a long H100 queue/startup interval without depending on the
synchronous client output stream. A missing, timed-out, non-finite, incomplete, or otherwise
invalid response still fails closed, and the cost guard remains unchanged. The current failed
preflight artifact is not rewritten or promoted.

Validation:
The recovery-path code passes `make validate`, including 703 tests, strict mypy, Ruff, secret
scan, and 95.02% coverage. No new Modal request was made after the two failed attempts.

## D-088 — Isolate Modal transport and stop at the first diagnostic container failure
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None; constrains the next execution permitted by D-087

Context:
The first two exact-scope formal 64-row Evo2 preflight attempts ended with
`StreamTerminatedError: Connection lost` after image construction and before a remote score.
Before this continuation checkpoint arrived, a third attempt had already reached an H100
container, initialized the qualified Evo2 image, and started repeated eight-record calls, but it
was stopped by the local operator and produced no accepted formal result. The latest checkpoint
required isolating local client, transport, generic Modal execution, H100/CUDA, volume, model
initialization, and scoring in order, without another formal retry.

Decision:
Authorize only the diagnostic artifact
`artifacts/approvals/modal_transport_diagnostic_20260921.json`, capped at `$0.50` with a
`$0.45` safety stop. Use the smallest no-model/no-GPU/no-volume CPU function first and verify
both durable `spawn/get` and official `modal run --detach` retrieval. Because those CPU layers
passed, run one minimal H100 CUDA/tensor probe. Stop when that probe fails at
`ModuleNotFoundError: No module named 'torch'`; classify the result as a client/container
diagnostic dependency failure, not an H100 scheduling outage. Do not run the volume or Evo2
diagnostic layers and do not retry the formal 64-row preflight from this decision.

Consequences:
The CPU Modal transport path is now evidenced as healthy for deterministic calls and detached
result retrieval. H100 allocation is evidenced by the diagnostic container and the interrupted
formal app, but isolated CUDA/PyTorch readiness is not PASS because the diagnostic image omitted
`torch`. The exact next recommendation is `CLIENT_FIX_REQUIRED`: correct and independently
validate the diagnostic image before requesting a new H100-layer diagnostic or formal retry.
The formal sample remains `FAILED`, the formal gate remains `FAIL_FORMAL_PREFLIGHT`, no formal
rows or metrics are accepted, and labels/locked-test data remain outside Modal.

Validation:
`artifacts/modal_diagnostics/formal_preflight_failure_analysis_20260921.json` records the
current HEAD, protocol/study binding, app/function/container/call IDs, exact exceptions,
environment/timeouts, billing snapshot, CPU PASS, detached PASS, H100 diagnostic FAIL, and all
not-run downstream layers. `make validate` passed 703 tests with 95.02% coverage before the
evidence commit; all diagnostic apps were stopped and `modal container list` was empty.

## D-089 — Correct the isolated H100 diagnostic image without rerunning paid compute
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The bounded H100 diagnostic allocated a real H100 container but failed at `import torch` because
the probe image added Python 3.12 without installing the PyTorch package into that interpreter.
The existing formal Evo2 image already uses the known-good CUDA 12.4 PyTorch installation command.
Independent local Phase 3, scientific, frontend, and browser gates can continue without another
GPU request.

Decision:
Update `scripts/modal_h100_diagnostic.py` to install the same pinned `torch==2.4.0` wheel from
the CUDA 12.4 PyTorch index used by the qualified formal image. Validate the correction with
Ruff, strict mypy, and Python compilation only. Do not rerun the H100 diagnostic, mount
`hf_cache`, load Evo2, or retry the formal 64-row preflight until a fresh explicit continuation
authorizes that external execution.

Consequences:
The local client/container definition now addresses the observed dependency failure, but H100
CUDA readiness remains unverified after the correction. The historical failure artifact is not
rewritten. The exact recommendation remains `CLIENT_FIX_REQUIRED` until the corrected image is
verified under a new authorized diagnostic; no formal study gate changes.

Validation:
`make data-qc`, `make phase3-audit`, and `make phase3-reference-audit` passed the current local
data gates. The corrected H100 script passes Ruff, strict mypy, and compilation. No new Modal
H100 or formal app was started in this continuation.

## D-090 — Stop the corrected H100 diagnostic at the result-deserialization boundary
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None; constrains the diagnostic continuation authorized after D-089

Context:
The fresh continuation checkpoint authorized a corrected minimal H100 diagnostic under a new
approval capped at `$0.50`, after the prior image failed with `ModuleNotFoundError: No module
named 'torch'`. The corrected image installed the same pinned CUDA 12.4 PyTorch package used by
the qualified formal image. The run used detached Modal execution and was not a formal cohort
retry.

Decision:
Run only the corrected minimal H100 probe, then stop at the first new failure. App
`ap-ST5uHP1cHmdblqU4CIAncx` allocated container `ta-01M32FFXEKXGSTP7SHMPF1KNTR`; logs showed
NVIDIA PyTorch 24.07 and PyTorch `2.4.0a0+3bcc3cd`. Therefore H100 scheduling, container
startup, and remote PyTorch import are PASS. The local `FunctionCall.get` path then failed with
`DeserializationError: Deserialization failed because the 'torch' module is not available in the
local environment.` The required CUDA result was not accepted. Do not run `hf_cache`, Evo2,
one-row, eight-row, or formal 64-row work from this stopped attempt.

The exact continuation label required by the checkpoint is `PYTORCH_IMAGE_FIX_REQUIRED`; the
precise local remediation is to coerce all diagnostic return fields to plain JSON-safe builtins.
That remediation is committed at `e8ae239` and passes `make validate`. The existing approval is
bound to execution HEAD `14d8a98` and must not be silently rebound; any future H100 retry needs a
fresh approval bound to the corrected HEAD.

Alternatives:
Treating the remote banner as a complete CUDA PASS was rejected because the result payload could
not be decoded locally. Treating this as H100 scheduling unavailability or a Modal outage was
rejected because the H100 container started and emitted the PyTorch banner. Continuing to
`hf_cache` or Evo2 was rejected by the checkpoint stop rule.

Consequences:
The durable evidence is `artifacts/modal_diagnostics/h100_dependency_retry_analysis_20260921.json`
and `artifacts/modal_diagnostics/h100_cuda_probe_20260921.json`; all previous failed app IDs and
the original failure analysis remain preserved. Phase 6 remains `FAIL_FORMAL_PREFLIGHT`, and all
dependent scientific/downstream phases retain their existing blocked or deferred statuses. No
labels, locked-test data, or formal rows were sent to Modal.

Validation:
The corrected diagnostic source passes the source guard, Ruff, strict mypy, Python compilation,
and `make validate` with 704 tests passed, 33 deselected, and 95.02% coverage. Modal app and
container inventories were checked after execution; the diagnostic app was stopped and no active
container remained. Workspace billing was `$0.00` billed before and after in the available
workspace-level summaries.

## D-091 — Keep downstream status surfaces fail-closed after the H100 stop
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
After D-090 stopped the corrected H100 diagnostic at local result deserialization, the repository
still had independent local/UI/reproducibility checks available. These checks must be refreshed
without treating code presence or preliminary registry data as completed scientific evidence.

Decision:
Run the local frontend, browser, registry, figure, clean-room, release, protocol, schema, model
registry, and phase-status surfaces. Preserve their exact outcomes: frontend and browser gates
pass; registry verification passes; UI remains `PARTIAL`; final figures remain `BLOCKED` with zero
outputs; the preliminary figure bundle remains non-promotable; clean-room and release remain
`BLOCKED`; `modal-smoke` authenticates with zero GPU count and no remote invocation; and Phases
6/7/8/9/11/12/13/14/15/18/19 remain `BLOCKED`, Phase 10 remains `DEFERRED_BY_COMPUTE`, and
Phase 16 remains `PARTIAL`.

Consequences:
The repository has fresh evidence for every independently runnable control surface, but no local
refresh can satisfy the missing formal Evo2/CUDA result, full feature cache, downstream training,
locked evaluation, clean-room scientific reproduction, or final release gates. No status is
promoted and no new paid execution is started.

Validation:
The commands completed on 2026-09-21 at the current checkout. `make validate` remains green with
704 tests passed, 33 deselected, and 95.02% coverage; `git diff --check` is clean; and no active
Modal containers remain.

## D-092 — Accept the corrected H100 readiness ladder without promoting the formal study
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-090 for the corrected retry outcome; D-091 remains applicable to downstream gates

Context:
The prior corrected H100 attempt reached an H100 and imported remote PyTorch but failed when the
local client decoded a non-plain return value. Commit `e8ae239` coerced every diagnostic return
field to JSON-safe Python builtins. A fresh user approval,
`artifacts/approvals/modal_h100_jsonsafe_retry_20260921.json`, authorized only a bounded
diagnostic ladder with a `$0.50` hard cap and `$0.45` safety stop.

Decision:
Run the corrected ladder conditionally and stop before any formal 64-row preflight. The JSON-safe
H100 diagnostic, read-only `hf_cache` check, canonical Evo2 load-only check, one non-locked
development row, eight non-locked development rows, durable retrieval, shard persistence, and
resume/no-duplicate check all passed. The exact H100 result-deserialization failure did not recur.
Keep the formal protocol, model revision, context, orientation, score semantics, formal manifests,
locked-test boundary, and downstream phase gates unchanged. Record the single next recommendation
as `RETRY_FORMAL_64_PREFLIGHT`, but do not execute that retry from the current approval because
formal 64-row work is explicitly excluded and requires a separate approval.

Evidence:
`artifacts/modal_diagnostics/h100_jsonsafe_retry_20260921.json` records the app, function,
FunctionCall, container, model, GPU, runtime, billing, and bounded-cost evidence. The selected
development IDs were deterministic ascending normalized IDs from TRAIN only; labels were not sent
to Modal and no LOCKED_TEST row was accessed.

Consequences:
The H100/client readiness blocker is resolved for the corrected diagnostic path, and the existing
cache can load the pinned Evo2 checkpoint. The formal scientific gate remains
`FAIL_FORMAL_PREFLIGHT` until a separately authorized 64-row preflight returns and passes. No
full 4,000-row scoring, NT/Caduceus extraction, training, HPO, fine-tuning, locked evaluation,
Phase 14, deployment, release, or publication work is authorized by this decision.

Validation:
`make validate` and `git diff --check` passed at the verified HEAD before the ladder. The new
diagnostic scripts pass Ruff. All five remote apps are stopped; the estimated additional H100
  wall-rate cost is `$0.208895`; the workspace meter was `19.61` at baseline, `19.88` in the
  ladder artifact, and `19.94` at the final read-only inventory check. Workspace billed cost
  remained `$0.00`; workspace billing is not a per-run invoice.

## D-093 — Treat Evo2 source and Hugging Face snapshot revisions as separate reconciled namespaces
Status: ACCEPTED
Date: 2026-09-21
Supersedes: None

Context:
The successful JSON-safe H100/Evo2 ladder exposed source/code revision
`4b509ec2a22d6de472659f908bcb0714265ad3a7` and cache snapshot revision
`bda0089f92582d5baabf0f22d9fc85f3588f6b58`. A formal preflight must not silently treat those
different identifiers as either a mismatch or the same hash namespace.

Decision:
Record the source repository and pinned executable revision separately from the model repository
and Hugging Face snapshot. Accept the relationship as reconciled because the Modal image clones
the official source at the pinned source revision, constructs `Evo2("evo2_7b")`, mounts the
`arcinstitute/evo2_7b` cache snapshot, and the cache-hit load plus canonical one/eight-row
results confirm the same frozen scoring contract.

Evidence:
`artifacts/modal_diagnostics/evo2_provenance_reconciliation_20260921.json` records the source
repository, model repository, revisions, checkpoint path and size, cache blob identifier,
configuration identity, reconciliation rationale, and scientific boundary. The 13,766,621,200
byte checkpoint's cache blob identifier is retained without being misreported as an independently
recomputed content hash.

Consequence:
The provenance gate is `PASS`; it permits creation of the separately scoped formal 64-row
preflight approval but does not authorize the full 4,000-row run, NT/Caduceus extraction, locked
test, Phase 14, fine-tuning, context sweeps, deployment, or release.

## D-094 — Fail the formal study closed when the measured preflight exceeds the bounded plan
Status: ACCEPTED
Date: 2026-09-21
Supersedes: D-085 only for the measured outcome of this formal 64-row attempt; it does not alter
the frozen ML-DEV-BUDGETED-001 manifests or the locked-test boundary.

Context:
The successful JSON-safe H100/Evo2 ladder resolved infrastructure readiness and a fresh
formal-only approval authorized a hash-selected 64-row preflight at `$0.75` hard / `$0.65` safety.
The row-level execution returned 64 valid results and the persisted shards resumed without remote
recomputation, but the measured new-remote wall rate was higher than the planning rate.

Decision:
Accept the row-level sample as `PASS_FORMAL_SAMPLE`, then fail the formal precompute gate closed
because measured-rate scaling projects `$8.593340` for the 3,944 new Evo2 rows and `$9.198277`
for the frozen Phase 6/7 plan including NT/Caduceus. Both values exceed the intended `$7.75`
runner safety stop and `$8.00` bounded plan. Do not launch the 4,000-row run under this
approval, and do not manipulate batching, context, orientation, or scoring semantics to force a
lower projection.

Evidence:
`artifacts/phase6/phase6_formal_evo2_20260921_formal64_jsonsafe_retry.json` records 64 selected
and returned rows, TRAIN/VALIDATION coverage, exact model revision, finite scores, and the zero-
remote-call resume. `artifacts/phase6/formal_budgeted_preflight_gate_20260921_formal64_jsonsafe_retry.json`
records `FAIL_FORMAL_PREFLIGHT` and the single recommendation
`FORMAL_PREFLIGHT_FIX_REQUIRED`. Modal identities and billing observations are preserved in
`artifacts/modal_diagnostics/formal_64_preflight_modal_evidence_20260921.json`.

Consequences:
The formal Evo2 preflight is scientifically complete at sample scope but does not authorize the
full study. The full 4,000-row run, NT/Caduceus extraction, locked evaluation, Phase 14, training,
deployment, release, and publication remain unstarted or blocked. A future continuation needs a
new exact-scope decision that addresses the measured projection; this record does not widen the
budget.

Validation:
`make validate` and `git diff --check` passed before the paid run. The preflight approval,
provenance reconciliation, formal manifest hashes, and locked-test manifest were verified. Modal
reported `$0.00` billed at the available workspace snapshots and no active containers remained.

## D-095 — Permit only the verified chrY PAR hard-mask extraction alias for the remaining Phase 6 rows
Status: ACCEPTED
Date: 2026-09-22
Supersedes: D-063 only for the two explicitly verified chrY PAR1 context extractions; D-063 remains
unchanged for every other reference mismatch.

Context:
The resumed formal Evo2 run completed 3,968 of 4,000 development records and stopped before
submitting the final 32-row shard because `GRCh38:Y:1286043:T>C` and
`GRCh38:Y:1309674:G>T` resolved to `N` at their chrY central positions in the frozen Broad/GATK
GRCh38 analysis-set FASTA. The GATK reference documentation states that the analysis set
hard-masks the chrY PARs. The Genome Reference Consortium defines both loci as PAR1, and the
unmasked hg38 assembly has identical complete 8,192-bp X/Y windows at the same coordinates with
the expected manifest REF alleles.

Decision:
Adopt the dated additive reference-handling deviation `DEV-2026-001` for this continuation only.
For sequence-model context extraction, an eligible chrY variant may use its same-coordinate
homologous chrX PAR sequence only when all of the following hold:

1. The original locus is inside an official GRCh38 PAR.
2. The frozen chrY analysis-set reference is hard-masked.
3. The homologous chrX reference matches the manifest REF.
4. The complete 8,192-bp context is inside the homologous PAR and is unmasked.
5. The mapping is deterministic and independently validated against the unmasked assembly.

The original chrY normalized variant ID, chromosome, position, label, split, and provenance remain
unchanged. The output provenance must record `original_locus`, `extraction_locus`,
`par_alias_applied`, `reference_asset`, `expected_ref`, and `extracted_ref`. No generic
reference-mismatch fallback is permitted. The current formal amendment authorizes exactly the two
listed IDs; no additional chrY PAR records were found in the 4,000-row manifest.

The audit also found two mitochondrial records with a single `N` at `chrM:3107` inside their
8,192-bp context, but their central REF alleles match and they are not eligible for this PAR-only
alias. No PAR-boundary context crossings or other central reference mismatches were found.

Evidence:
`artifacts/reference/par_mask_resolution_20260922.json` records the frozen asset hashes, official
PAR definitions, both masked chrY windows, both matching chrX bases, complete X/Y unmasked-window
hash equality, the four-record masked-context audit, and unchanged formal identities. The
authoritative references are the GATK Reference Genome Components page, the Genome Reference
Consortium GRCh38 overview, and the UCSC hg38 sequence REST API.

Consequences:
The formal 4,000 record identities and estimand remain unchanged. Only the two model sequence
contexts may be extracted from chrX because the analysis-set chrY PAR representation is
intentionally masked. The remaining Phase 6 retry remains separately approval-gated at the new
HEAD with a `$0.50` hard cap and `$0.40` safety stop. NT, Caduceus, fine-tuning, locked-test
inference, and Phase 7 remain outside that approval.

Validation:
The PAR resolution artifact parses and hashes successfully. The canonical extractor's focused
tests cover both current variants, a normal chrY PAR locus, an ordinary non-PAR chrY locus, a
chrX locus, homologous-REF mismatch rejection, PAR-boundary rejection, and deterministic output.
Ruff and Python compilation pass for the touched files. Full local validation remains required
before the fresh paid approval is created.

## D-096 — Accept the formal Evo2 Phase 6 cohort and stop at the next allocation boundary
Status: ACCEPTED
Date: 2026-09-22
Supersedes: D-095 only for the execution outcome; the scoped chrY PAR alias and its guards remain
the governing reference-handling decision for the two affected records.

Context:
The D-095/DEV-2026-001 PAR resolution passed its focused tests and full local validation. A fresh
approval bound to HEAD `535d73e56d10ddea5d2ef0098bb7251a57d259d7` authorized only the remaining
32 formal Evo2 records with a `$0.50` hard cap and `$0.40` safety stop. The resumed run reused the
124 verified completed shards and submitted one new 32-row shard.

Decision:
Accept the formal Evo2 Phase 6 development cohort as `PASS` within its exact approved scope:
4,000/4,000 rows, 125 complete shards, 124 stored-shard cache hits, 32 newly scored remote rows,
zero pending rows, zero duplicates, zero unexpected IDs, zero reference mismatches, finite forward,
reverse-complement, and aggregate scores, no labels sent to Modal, and zero locked-test rows. The
final artifact and prediction stream are the authoritative outputs for this bounded Evo2 track.
Stop paid work at this allocation boundary. Do not launch NT, Caduceus, fine-tuning, Phase 7, or
locked-test inference without a separate explicit allocation and approval. Do not treat this
bounded Evo2 result as a PASS for the broader multi-model Phase 6 benchmark.

Evidence:
The final artifact is
`artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json`, SHA-256
`b04940b3b5845fd57144f54a9862da8d9d89fb1b98d9c79fc45364e7a21ef54d`. The prediction stream is
`research/runs/phase6_formal_evo2_20260921_full_overnight_20260922/predictions.jsonl`, SHA-256
`088e39fcfa45b2af9cd8f11cbb803213d9030c92036fc9f27f577c3912693751`. The approval is
`artifacts/approvals/formal_phase6_par_resume_20260922.json`, SHA-256
`f345f969f996a48ba33db9830d89c718d76fa64d7416e89209da5cef42758ae7`, and the preflight is
`artifacts/phase6/formal_phase6_par_resume_preflight_20260922.json`, SHA-256
`af8e052dde5f163d57951a0bdc7a41cef97da235c204f496597073d652beff17`. The PAR resolution artifact
is SHA-256 `2f71248d7a97329db24301a73bdd427a2673af7ebc62a29a2ee4467060815b42`.

Consequences:
The formal Evo2 subtrack is complete and its paid workers are shut down. The observed final app
usage was `$0.09374570`, with a runner wall-rate estimate of `$0.111328`; workspace billing stayed
at `$0.00` billed. The final container inventory was empty. Using the exact prior derived free
headroom of `$5.94229534`, the derived remaining headroom is approximately `$5.84854964` (about
`$5.85`). The broader Phase 6 multi-model benchmark remains partial/allocation-gated, and later
scientific phases remain at their documented statuses.

Validation:
The final no-spend integrity audit passed with exact manifest/order identity, 125 contiguous
shards, payload and plan hashes, 4,000 unique IDs, zero pending markers, finite score arithmetic,
the two exact PAR provenance records, and all scientific boundary checks. `make validate` passed
before paid execution with 715 tests passed, 33 deselected, and 95.01% coverage. No active Modal
containers remained after completion.

## D-097 — Stop narrow Phase 7 representation work at the authorized budget boundary
Status: ACCEPTED
Date: 2026-09-22
Supersedes: D-096 only for the post-Phase-6 NT/Caduceus allocation boundary; the completed Evo2
Phase 6 artifact remains immutable and accepted.

Context:
The fresh Phase 7 approval `artifacts/approvals/formal_phase7_representation_20260922.json`
authorized only formal Nucleotide Transformer and Caduceus representations for the exact 4,000-row
TRAIN/VALIDATION cohort, with a `$1.00` hard cap and `$0.85` safety stop. The approved HEAD was
`71a7c2d16148aecb99037f70439a57243153f6ca`. The runner first persisted 504 verified NT rows in
63 small shards, then switched to a committed cache-preserving 64-row/4-row-batch plan and added
1,928 more verified NT rows without recomputing the first 504.

Decision:
Stop paid Phase 7 work as `PARTIAL / ALLOCATION BLOCKED`. Do not launch another Modal call under
the current approval. The cumulative completed NT client wall-rate estimate is `$0.704889`; 2,072
NT rows and all 4,000 Caduceus rows remain unscored. The runner stopped fail-closed at the safety
gate before any unauthorized widening. The verified cache is resumable, and a future allocation
must bind a fresh approval to the then-current HEAD and reuse both completed cache layers.

Evidence:
`artifacts/phase7/formal_budgeted_representation_20260922_partial.json` records the exact cache
plan hashes, 2,432-row union, 1,568 remaining formal NT rows, zero Caduceus rows, zero duplicate or
unexpected IDs, zero locked overlap, finite packed features, reference-construction matches, and
the workspace billing snapshots. The small-shard plan is
`research/runs/phase7_formal_budgeted_20260922/nucleotide_transformer/execution_plan.json`; the
optimized plan is
`research/runs/phase7_formal_budgeted_optimized_20260922/nucleotide_transformer/execution_plan.json`.

Consequences:
No Caduceus features, complete Phase 7 artifact, or Phase 7 PASS is claimed. No labels were sent
to Modal; no locked-test rows, fine-tuning, Evo2 rerun, or Phase 14 work was started. Phase 8-13
model selection remains blocked on the complete approved representation matrix. The 946-row locked
test remains untouched and requires a separate future approval.

Validation:
The final no-spend audit revalidated every persisted NT shard payload and plan hash, rebuilt the
local 8,192-bp reference/alternate/forward/reverse-complement provenance for all 2,432 rows,
checked packed hidden states for finite values and all declared layers, and verified zero active
Modal containers. Workspace billing remained `$0.00` billed; the latest supporting metered snapshot
was `$30.59`. The partial artifact SHA-256 is recorded with the final report.

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

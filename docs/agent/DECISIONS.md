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

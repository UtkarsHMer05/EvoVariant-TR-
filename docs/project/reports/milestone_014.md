# Milestone 014 — Design the immutable experiment registry

- **MILESTONE:** 014
- **TITLE:** Design the immutable experiment registry
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- `src/evovariant_tr/` had `config.py` (M12) and `evidence.py` (M13); no run tracking existed.
- `experiments/` existed only as an empty skeleton directory (M8).
- No run-id convention, no JSON schema for runs, no dirty-tree FINAL guard in code (EVIDENCE_STAGES.md rule 7 deferred enforcement to this milestone).

## WHAT CHANGED

- Implemented `src/evovariant_tr/registry.py`:
  - `generate_run_id()` → `run_<UTC stamp>_<8 hex>` (collision-resistant, sortable, pattern-validated).
  - `RunRecord` (strict, frozen Pydantic model) recording: protocol hash, git commit, dirty flag, data manifests, reference checksum, model identity, scorer config, comparator versions, seed, hardware, command, created/updated timestamps, status, parent run id, output paths, output hashes, evidence stage.
  - `Registry`: append-only storage — one JSON file per run under `experiments/registry/runs/` plus an append-only `log.jsonl` event log; re-registering an existing run id raises.
  - Status lifecycle `REGISTERED → RUNNING → COMPLETED | FAILED | ABORTED`; terminal states are final and reject further transitions; FAILED/ABORTED carry reasons in the event log.
  - Parent/child relationships for sharded jobs: children reference `parent_run_id`; unknown or terminal parents are rejected; `children()` lists shards.
  - **Validation 1 guard:** `validate_final_gate` refuses FINAL registration when the git tree is dirty or when no commit exists; the only escape hatch is explicit — register under a non-final stage. No silent override flag exists.
  - **Validation 2 guard:** `COMPLETED` requires `output_paths`; SHA-256 hashes are computed at completion and `verify_output_hashes` recomputes them from disk, raising on any mismatch (tamper-evident).
- Created `research/schemas/experiment_run.schema.json` (JSON Schema 2020-12, `additionalProperties: false`) mirroring `RunRecord`, including run-id pattern, stage enum, status enum, and SHA-256 patterns.
- Created `experiments/registry/` with `.gitkeep`.
- Installed `jsonschema 4.26.0` into `.venv-baseline` for schema validation tests.

## FILES CREATED

- `src/evovariant_tr/registry.py`
- `research/schemas/experiment_run.schema.json`
- `tests/unit/test_registry.py`
- `experiments/registry/.gitkeep`
- `docs/project/reports/milestone_014.md` (this report)

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 014 → PASS)

## FILES REMOVED / MOVED

- None.

## COMMANDS RUN

- `mkdir -p experiments/registry`
- `python -m pytest tests/unit/test_registry.py -q` → **24 passed in 1.24s**
- `python -m pytest tests/unit -q` → **85 passed in 1.99s** (no regressions)

## TESTS

- `tests/unit/test_registry.py` — 24 tests covering:
  - run-id format/uniqueness and malformed-id rejection;
  - registration writes record + event log; disk round-trip; JSON-schema conformance of a real record; schema rejects invalid stages;
  - append-only enforcement; unknown-run load failure; unknown-field rejection; frozen instances;
  - **Validation 1:** FINAL refused on dirty tree (real temp git repo), FINAL refused without a git repo, FINAL allowed on clean tree, dirty tree fine for non-final stages, direct gate unit tests;
  - lifecycle to COMPLETED with output hashes; COMPLETED without outputs refused; FAILED/ABORTED terminal with reasons recorded;
  - **Validation 2:** hashes recomputable after completion; tampered output detected; missing output file raises; hashes-without-paths inconsistent;
  - parent/child shard relationships; terminal/unknown parent rejection; sorted listing.

## SCIENTIFIC VALIDATION

- Every future scientific run will be reproducible from metadata alone: protocol hash pins the frozen protocol (M11 hash `78799000…`), git commit + dirty flag pin the code state, and output hashes pin the artifacts.
- FINAL evidence cannot be minted from a dirty working tree — the dirty-tree guard from EVIDENCE_STAGES.md rule 7 is now enforced in code.
- No run was registered against real data; tests use synthetic temp repos only.

## ENGINEERING VALIDATION

- Append-only semantics proven (duplicate write raises; terminal transitions raise).
- Registry is filesystem-only: no network, no Modal, no torch (cloud-free core preserved).
- Full unit suite green: 85 tests.

## COST / EXTERNAL CALLS

- None. Zero external calls, zero GPU, zero spend.

## EVIDENCE GENERATED

- Test run outputs (24 passed; 85 passed).
- Stage: SYNTHETIC_TEST (registry behavior proven with synthetic temp repositories).

## GIT STATUS

- New files listed above; ledger updated. Local commit to follow; no remote configured, no push.

## RISKS / OPEN QUESTIONS

- `git_state` returns `(None, False)` for non-git directories; the FINAL gate separately requires a commit sha, so this cannot be exploited to mint FINAL runs.
- Data manifests are recorded as `{name: sha256}` strings; the manifest *generation* machinery is Milestone 15 — the registry already accepts its output shape.
- Registry writes are not file-locked; concurrent writers are out of scope until batch submission (M66) where sharding makes run ids disjoint by construction.

## NEXT MILESTONE

- 015 — Implement deterministic file manifests and hashing.

## DO NOT CONTINUE IF

- Any registry test fails or is skipped.
- A FINAL run can be registered with a dirty tree or without a commit.
- Output hashes cannot be recomputed from recorded paths.

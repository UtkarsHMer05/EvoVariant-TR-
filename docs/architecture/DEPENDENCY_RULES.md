# DEPENDENCY RULES — EvoVariant-TR (Milestone 008)

Import and coupling rules for the target architecture. These become executable
checks/tests as the corresponding modules land; they are stated now so every later
milestone is designed against them.

## 1. Core science must be cloud-free

Modules: `src/evovariant_tr/{sequence,scoring,calibration,evaluation,statistics,clinvar}/`,
`variants.py`, `reference.py`, `config.py`, `evidence.py`, `manifest.py`, `registry.py`.

- MUST NOT import `modal`.
- MUST NOT import `torch` (scorer *interface* is model-agnostic; torch belongs to
  the Modal adapter implementation).
- MUST NOT perform network I/O at import time or inside pure transforms. Network
  access (ClinVar/reference downloads) lives in explicitly-marked fetcher modules
  that are injected, and is never on the deterministic scoring path.
- MUST be importable and unit-testable on macOS/CPU.

Rationale: sequence semantics, cohort logic, calibration, and statistics must be
reproducible and testable without GPUs, cloud credentials, or network.

## 2. Transport may depend on core, never the reverse

Modules: `services/modal/**`, `src/evovariant_tr/api/**`.

- MAY import `modal`, `fastapi`, `torch`, and the core package.
- MUST keep scientific orchestration out of HTTP request handlers and Modal
  `@modal.enter()` hooks; handlers call validated core functions.
- MUST return provenance (scorer identity, evidence stage) with results.
- MUST NOT return a fake/synthetic score when the real model is unavailable
  (return an explicit unavailable/failure state instead).

## 3. UI depends on the API contract only

`apps/web`:

- MUST NOT import Python or call Modal directly for scientific scoring.
- MUST talk to the research API via a single typed client.
- MUST NOT expose secrets via `NEXT_PUBLIC_*` (URLs only).
- MUST render evidence stage + research-only boundary for every metric.

## 4. Data dependencies

- Deterministic science reads from **frozen local artifacts** (manifest-verified
  FASTA, parsed ClinVar parquet), never from live per-request network sources.
- Live UCSC/NCBI access is allowed only for UI browse convenience and for the
  one-time, manifest-recorded download steps — never inside final scoring.

## 5. Test-scope dependencies

- Default `pytest` run: unit + contract + integration on tiny fixtures. MUST NOT
  launch paid compute or require network.
- `modal` and `scientific` test markers: opt-in only, require explicit
  acknowledgement; may incur cost. Never run by default CI/local validation.

## 6. Enforcement plan

| Rule | Enforced at |
|---|---|
| No `modal`/`torch` import in core | M16/M17 (import-linter-style test) |
| No network in pure transforms | unit tests + code review |
| Fake scorer cannot register as FINAL | M13/M14 tests |
| Synthetic outputs blocked from final dirs | M13 writer guard test |
| Default test command never launches paid compute | M17 pytest config |
| No raw/large data in Git | M21 `check_large_files.sh` |

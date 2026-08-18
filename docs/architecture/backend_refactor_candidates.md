# BACKEND REFACTOR CANDIDATES — Proposed module boundaries (Milestone 004)

Date: 2026-08-18
Status: PROPOSAL ONLY — no code is moved or edited at this milestone.

Maps each legacy `evo2-backend/main.py` responsibility to its target home in the
EvoVariant-TR architecture (master prompt §15). Guiding rule: **deterministic
scientific logic must be importable and testable with no Modal, no GPU, and no
network.**

## 1. Responsibility → target module map

| Legacy responsibility (main.py) | Target module | Layer | Notes |
|---|---|---|---|
| Modal image creation (13-31) | `services/modal/image.py` | cloud adapter | pinned, patch-free, built from constraints file |
| Dependency install (17-30) | `services/modal/evo2_constraints.txt` + image.py | cloud adapter | exact pins; official light-install path preferred |
| Compatibility patch (29) | **deleted** unless justified at M51 | — | zero patches by default |
| Model init (57, 291-302) | `services/modal/model_service.py` | cloud adapter | `@modal.enter()` load; records checkpoint identity |
| Live UCSC download (224-257) | **removed from scoring path** | — | replaced by frozen local FASTA (`src/evovariant_tr/reference.py`); UCSC may remain a UI browse convenience only |
| Window construction (260-262, 319-335) | `src/evovariant_tr/sequence/window.py` | pure science | exact 8,192 even window; hard assertions; edge policy |
| Mutation (261-262) | `src/evovariant_tr/sequence/mutate.py` | pure science | Hamming==1 invariant |
| Reverse complement | `src/evovariant_tr/sequence/orientation.py` | pure science | NEW — legacy has none |
| Evo 2 scoring call (264-265) | `src/evovariant_tr/scoring/base.py` (interface) + `services/modal/` (implementation) | interface + adapter | scorer contract decoupled from transport |
| Threshold derivation/use (133-158, 269-271) | **deleted from scoring path**; calibration in `src/evovariant_tr/calibration/` | science | Platt on disjoint definitive-at-t0 cohort only |
| Confidence heuristic (273-278) | **deleted** | — | replaced by calibrated study probability + evidence stage |
| BRCA1 analysis (40-221) | not migrated as research code | — | LEGACY_BASELINE_ONLY; may inform docs/history only |
| HTTP endpoint (289-349) | `src/evovariant_tr/api/app.py` (research API) | service | typed, provenance-returning, no clinical labels |
| Variant identity/validation | `src/evovariant_tr/variants.py` | pure science | canonical GRCh38:chr:pos:ref:alt; early rejection |
| Reference access | `src/evovariant_tr/reference.py` | science I/O | indexed local FASTA; alias normalization |
| Cohort building | `src/evovariant_tr/clinvar/*` | science | parser/classification/review-status/eligibility/temporal |
| Metrics/statistics | `src/evovariant_tr/evaluation/`, `src/evovariant_tr/statistics/` | science | AUROC + gene-clustered bootstrap |
| Run provenance | `src/evovariant_tr/registry.py`, `manifest.py`, `evidence.py` | infra | run IDs, hashes, evidence stages |
| Config | `src/evovariant_tr/config.py` | infra | validated scientific vs deployment config split |

## 2. Dependency rules (enforced later by tests)

- `src/evovariant_tr/**` MUST NOT import `modal`, `torch`, or `requests` in pure
  science modules (`sequence/`, `variants.py`, `calibration/`, `statistics/`,
  `evaluation/`). Network I/O lives in explicitly marked adapter modules.
- `services/modal/**` MAY import `modal` and the core package, but scientific
  orchestration stays out of request handlers.
- `apps/web` talks to the research API; it never talks to Modal directly for
  scientific scoring.

## 3. Migration order (incremental, not a big-bang rewrite)

1. Scaffold package + config + evidence types (M12-16).
2. Variants/reference/window/mutate/orientation with exhaustive tests (M28-46).
3. Scorer interface + fake scorer + pipeline (M47-50).
4. Modal image/model/parity/pilots (M51-60).
5. Sharding/resume/failures/service/batch (M61-68).
6. Full run behind approval gate (M69-70).
7. Comparators/calibration/statistics/robustness (M71-90).
8. API/UI (M91-97).

Legacy `evo2-backend/` and `evo2-frontend/` remain in-tree as the migration baseline
until their replacements pass the relevant gates; removal happens incrementally with
attribution, never before the replacement is validated.

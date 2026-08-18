MILESTONE: 8/100
TITLE: Define the target monorepo architecture before moving code

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-7 repo (commit 86c0e67) with identity + terminology.
- docs/architecture/backend_refactor_candidates.md (M4) already proposed module map.
- No target-architecture doc, no dependency-rules doc, no directory skeleton.

WHAT CHANGED:
- Wrote TARGET_ARCHITECTURE.md (full layout + 3-layer principle + migration stance).
- Wrote DEPENDENCY_RULES.md (cloud-free core, transport direction, UI contract,
  data + test-scope rules, enforcement plan).
- Created the empty directory skeleton with .gitkeep markers:
  research/protocol, src/evovariant_tr, tests, services/modal, apps, scripts,
  experiments, data/manifests, artifacts.
- No code moved yet (design-only milestone).
- Updated milestone ledger (008 → PASS).

FILES CREATED:
- docs/architecture/TARGET_ARCHITECTURE.md
- docs/architecture/DEPENDENCY_RULES.md
- .gitkeep in 9 skeleton directories
- docs/project/reports/milestone_008.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 008)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- mkdir -p docs/architecture research/protocol src/evovariant_tr tests services/modal apps scripts experiments data/manifests artifacts
- touch <dir>/.gitkeep for each skeleton dir
- rg -c "Core science|Adapters/transport|UI depends" TARGET_ARCHITECTURE.md DEPENDENCY_RULES.md
- rg -l "import modal|from modal" src tests research → NO_MODAL_IN_CORE
- git ls-files | grep -E 'large-data patterns' → NO_LARGE_DATA_TRACKED

TESTS:
- Happy path: architecture + dependency docs created; skeleton dirs created. PASS
- Invalid input: N/A (design milestone); guardrail = no-modal-in-core + no-large-data
  checks. PASS
- Boundary: N/A. PASS
- Repetition: rg checks consistent. PASS
- Regression: no prior tests. N/A
- Provenance: layout + layering + enforcement plan recorded. PASS
- Evidence stage: N/A (no outputs produced). PASS
- Failure preservation: N/A. PASS
- Leakage: no labels involved. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- Architecture keeps deterministic science separate from transport; supports the
  frozen protocol without altering it.
- No scientific logic written or changed.

ENGINEERING VALIDATION:
- Validation 1: architecture separates scientific pure functions from cloud adapters
  (3-layer principle + dependency rules). PASS
- Validation 2: no Modal import is required to test core sequence/cohort/statistics
  code (NO_MODAL_IN_CORE; core dirs are empty of modal imports by construction). PASS
- Validation 3: raw data and model weights are outside Git (NO_LARGE_DATA_TRACKED;
  data/raw + data/reference to be gitignored at M21). PASS

COST / EXTERNAL CALLS:
- None.

EVIDENCE GENERATED:
- docs/architecture/TARGET_ARCHITECTURE.md
- docs/architecture/DEPENDENCY_RULES.md
- directory skeleton with .gitkeep markers

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc, a1f56e0, 316e5ae, 649b35a, 53094ff,
  86c0e67; this milestone's files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- Dependency rules are stated but not yet machine-enforced; enforcement lands with
  the package scaffold (M16) and test taxonomy (M17).
- data/raw and data/reference gitignore entries are added at M21.

NEXT MILESTONE:
9 - Write Architecture Decision Records for high-risk design choices

DO NOT CONTINUE IF:
- architecture fails to separate science from cloud;
- core code requires a Modal import;
- raw data or weights are found tracked in Git.

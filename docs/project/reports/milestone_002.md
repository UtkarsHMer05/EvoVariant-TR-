MILESTONE: 2/100
TITLE: Create an immutable baseline snapshot and repository inventory

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-1 repo: root commit 354e987 + report commit 4f7bc14; 65 tracked files.
- docs/bootstrap/NEW_REPOSITORY_ORIGIN.md, initial_file_inventory.txt,
  docs/project/MILESTONE_STATUS.md already present.
- No hash manifest, no architecture inventory.

WHAT CHANGED:
- Generated SHA-256 manifest for every tracked/source file (excludes .git/,
  .DS_Store, __pycache__/, *.pyc) → 66 entries.
- Generated sorted file list (all_files.txt, 66 entries).
- Wrote BASELINE_ARCHITECTURE.md classifying every component and flagging the
  8,193-base window defect and legacy-only evidence.
- Updated milestone ledger (002 → PASS).

FILES CREATED:
- docs/bootstrap/source_snapshot.sha256
- docs/bootstrap/all_files.txt
- docs/bootstrap/BASELINE_ARCHITECTURE.md
- docs/project/reports/milestone_002.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 002)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- pwd; git status --short; git remote -v; git log --oneline
- find . -type f -not -path './.git/*' -not -name '.DS_Store' -not -path '*/__pycache__/*' -not -name '*.pyc' -print0 | sort -z | xargs -0 shasum -a 256  (run 1 → /tmp)
- same find|shasum pipeline (run 2 → /tmp) ; diff run1 run2 → DETERMINISTIC_HASHES_MATCH
- find ... | sort > all_files.txt
- du -ah . | grep -v '/.git/' | sort -h | tail -25
- per-extension file/line counts (py/ts/tsx/js/json/md)
- wc -l evo2-backend/*.py evaluation/*.py
- Read evo2-backend/main.py (full), evaluation/evaluate_modal_endpoint.py (head),
  evaluation/results/final_100/{summary.txt,metrics.json}, evaluation/README.md,
  evo2-frontend/package.json, .env.example, src/env.js, src/utils/genome-api.ts
- cp manifests into docs/bootstrap/
- shasum -a 256 -c (spot-check 5 files) → all OK
- grep -c component presence in all_files.txt

TESTS:
- Happy path: manifest + inventory + architecture doc generated. PASS
- Invalid input: N/A (no parser yet); guardrail = shasum -c spot-check would fail
  on corruption (verified OK on 5 files). PASS
- Boundary: manifest excludes .git/.DS_Store/__pycache__/*.pyc deterministically;
  includes dotfiles and nested dirs. PASS
- Repetition: two independent shasum generations → byte-identical (diff clean). PASS
- Regression: no prior tests. N/A
- Provenance: manifest + retrieval date + evidence-stage labels recorded. PASS
- Evidence stage: all saved metrics labeled LEGACY_BASELINE_ONLY. PASS
- Failure preservation: no failures; nothing dropped. PASS
- Leakage: no temporal labels/model outputs involved. PASS
- Cost: no external/GPU/paid calls (git remote still empty; no network). PASS

SCIENTIFIC VALIDATION:
- No scientific logic changed; temporal question untouched.
- Legacy BRCA1 threshold and 8,193-base defect flagged as deprecated, not inherited.
- Legacy 100-row metrics explicitly NOT classified as new evidence.

ENGINEERING VALIDATION:
- Snapshot hashes deterministic on repeated execution (Validation 1). PASS
- Inventory contains old README, backend, frontend, evaluation (Validation 2). PASS
- No external old repository queried; git remote -v empty (Validation 3). PASS
- .gitmodules recorded but NOT initialized. PASS

COST / EXTERNAL CALLS:
- None. No network, no GPU, no Modal, no paid calls.

EVIDENCE GENERATED:
- docs/bootstrap/source_snapshot.sha256 (66 SHA-256 entries, deterministic)
- docs/bootstrap/all_files.txt (66 sorted paths)
- docs/bootstrap/BASELINE_ARCHITECTURE.md

GIT STATUS:
- branch main; commits 354e987, 4f7bc14; this milestone's files staged in next commit;
  remotes: none; no push.

RISKS / OPEN QUESTIONS:
- The four ~60 KB patched_attn_interface*.py / local_attn_interface.py files are
  large near-duplicates; kept for audit (Milestone 4) but candidates for removal
  after the old stack is superseded.
- Legacy evaluation/results PNGs are tracked; they are LEGACY_BASELINE_ONLY and may
  be relocated/removed with attribution in a later migration milestone.

NEXT MILESTONE:
3 - Audit the legacy scientific behavior without accepting it as the new design

DO NOT CONTINUE IF:
- snapshot hashes become non-deterministic;
- an external old repository is queried;
- any saved legacy metric is promoted to EvoVariant-TR evidence.

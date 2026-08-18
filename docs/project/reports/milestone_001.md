MILESTONE: 1/100
TITLE: Create a genuinely new repository from the supplied source snapshot

STATUS:
PASS

WHAT EXISTED BEFORE:
- Local snapshot at /Users/utkarshkhajuria/Desktop/EvoVariant with 66 files:
  legacy README, PPT material, .gitignore, .gitmodules (declares ArcInstitute/evo2
  submodule, not present on disk), evaluation/ (legacy 100-row BRCA1 eval outputs),
  evo2-backend/ (15 files incl. main.py, debug/patch scripts), evo2-frontend/
  (Next.js app, 30 files).
- No .git directory, no worktree metadata, no remotes (verified).
- No docs/, no milestone ledger.

WHAT CHANGED:
- Initialized a brand-new Git repository (git init -b main) in the snapshot dir.
- Recorded pre-refactor file inventory (66 files).
- Documented repository origin and isolation policy.
- Created the 100-milestone status ledger.
- Extended .gitignore with global Python cache rules so snapshot __pycache__/.pyc
  and .DS_Store cannot be committed.
- Created first local commit (root commit 354e987, 65 tracked files).

FILES CREATED:
- docs/bootstrap/NEW_REPOSITORY_ORIGIN.md
- docs/bootstrap/initial_file_inventory.txt
- docs/project/MILESTONE_STATUS.md
- docs/project/reports/milestone_001.md (this report)

FILES MODIFIED:
- .gitignore (added global __pycache__/*.pyc/*.pyo/*.pyd rules)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- pwd
- ls -la /Users/utkarshkhajuria/Desktop/EvoVariant
- git rev-parse --is-inside-work-tree (→ not a work tree, pre-init)
- git remote -v (→ empty, pre-init and post-init)
- find . -type f -not -path './.git/*' | sort (inventory)
- git init -b main
- git symbolic-ref HEAD (→ refs/heads/main)
- cat .git/objects/info/alternates (→ none), cat .git/HEAD, git config --local --list
- git status --short; git add -A; git diff --check; git ls-files | grep junk-check
- git commit -m "chore(milestone-1): ..."
- git log --oneline; git status --short (→ clean)

TESTS:
- Happy path: git init + inventory + docs creation succeeded. PASS
- Invalid input: N/A for this milestone (no parser/scientific logic yet); the
  guardrail equivalent is the junk-staged check (git ls-files grep for
  .DS_Store/__pycache__/.pyc) which correctly found NO_JUNK_STAGED. PASS
- Boundary: inventory includes dotfiles and nested dirs (66 files incl. hidden). PASS
- Repetition: `find` inventory run once and copied verbatim; git remote -v checked
  twice (pre/post init) with identical empty result. PASS
- Regression: no prior tests exist. N/A
- Provenance: origin doc records snapshot→new-repo chain and date. PASS
- Evidence stage: legacy evaluation outputs labeled LEGACY_BASELINE_ONLY in origin doc. PASS
- Failure preservation: no failures occurred; nothing dropped. PASS
- Leakage: no temporal labels or model outputs involved. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- No scientific logic touched; temporal question untouched.
- Legacy BRCA1 threshold NOT inherited (documented as legacy-only).
- No clinical claims introduced.

ENGINEERING VALIDATION:
- Fresh .git belongs only to this project (no alternates, no worktree link).
- git remote -v empty → no old origin.
- No command modified or pushed the original repository (no old repo path touched;
  snapshot had no .git to modify).
- git diff --check passed; working tree clean after commit.

COST / EXTERNAL CALLS:
- None. No network, no GPU, no Modal, no paid calls.

EVIDENCE GENERATED:
- docs/bootstrap/initial_file_inventory.txt (66-line pre-refactor inventory)
- docs/bootstrap/NEW_REPOSITORY_ORIGIN.md
- Root commit 354e987 on branch main

GIT STATUS:
- branch: main; root commit 354e987; working tree clean; remotes: none; no push performed.

RISKS / OPEN QUESTIONS:
- No NEW remote URL has been provided by the user → all work stays local; push is
  blocked until the user explicitly supplies and authorizes the new repository URL.
- Snapshot .gitmodules still declares the ArcInstitute/evo2 submodule; it is NOT
  initialized and will be handled deliberately at Milestone 51 (official Evo 2 pin).
- Legacy evaluation/results outputs are tracked in this first commit as migration
  input; they are labeled LEGACY_BASELINE_ONLY and must never be cited as
  EvoVariant-TR evidence.

NEXT MILESTONE:
2 - Create an immutable baseline snapshot and repository inventory

DO NOT CONTINUE IF:
- an unexpected old Git remote appears;
- any command targets the old repository path;
- the user wants the snapshot files excluded from the new repo before Milestone 2.

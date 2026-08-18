MILESTONE: 6/100
TITLE: Reproduce the old project locally only as a baseline smoke test

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-5 repo (commit 649b35a) with frontend/backend/scientific audits.
- Legacy source: evo2-backend/, evaluation/, evo2-frontend/ (node_modules already
  installed from Milestone 5).
- No artifacts/baseline/, no BASELINE_SMOKE_TEST.md.

WHAT CHANGED:
- Ran Python compileall on backend + evaluation (PASS).
- Probed local availability of backend/evaluator deps (several missing on system python3).
- Created a disposable CPU venv (.venv-baseline, gitignored) and installed evaluator
  CPU deps (pandas, numpy, matplotlib, seaborn, scikit-learn, openpyxl, requests).
- Exercised evaluator static behavior with a harness: import, compute_metrics on
  synthetic data, repetition determinism, failure preservation, and two invalid-input
  paths. All behaved explicitly/deterministically.
- Re-verified npm ci + typecheck (PASS).
- Ran npm run build as-is (FAIL: env) and with placeholder env (FAIL: ESLint 158
  error/warning lines). Recorded verbatim, categorized, NOT repaired.
- Did NOT run paid Modal GPU work; did NOT contact the old endpoint; did NOT promote
  any old result to evidence.
- Extended .gitignore with global venv rules.
- Updated milestone ledger (006 → PASS).

FILES CREATED:
- artifacts/baseline/command_log.txt
- docs/bootstrap/BASELINE_SMOKE_TEST.md
- docs/project/reports/milestone_006.md (this report)

FILES MODIFIED:
- .gitignore (added global venv ignore rules)
- docs/project/MILESTONE_STATUS.md (ledger row 006)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- python3 -m compileall evo2-backend evaluation  → exit 0
- python3 -m compileall -f -q evo2-backend evaluation  → exit 0
- python3 -c "import <dep>" for modal/pydantic/pandas/numpy/matplotlib/seaborn/requests/openpyxl/fastapi/sklearn
- python3.12 -m venv .venv-baseline
- . .venv-baseline/bin/activate && python -m pip install -U pip
- python -m pip install pandas numpy matplotlib seaborn scikit-learn openpyxl requests
- python -c "import pandas,numpy,matplotlib,seaborn,sklearn,openpyxl,requests" → OK
- python harness (import evaluator; compute_metrics; repetition; build_diagnostics;
  empty-input RuntimeError; missing-xlsx FileNotFoundError)
- cd evo2-frontend && npm ci  → success
- cd evo2-frontend && npm run typecheck  → exit 0
- cd evo2-frontend && npm run build  → FAIL (env)
- NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL=<placeholder> npm run build  → FAIL (ESLint)
- git check-ignore .venv-baseline → IGNORED_OK

TESTS:
- Happy path: compileall, venv install, evaluator import + compute_metrics, npm ci,
  typecheck. PASS
- Invalid input: evaluator empty-predictions → RuntimeError; missing xlsx →
  FileNotFoundError. Both fail safely and explicitly. PASS
- Boundary: evaluator with a failure row → diagnostics retains it ({'500':1}). PASS
- Repetition: compute_metrics run twice → identical. PASS
- Regression: no prior tests. N/A
- Provenance: every command + result recorded in command_log.txt. PASS
- Evidence stage: all labeled LEGACY_BASELINE_ONLY; synthetic metrics marked as
  harness self-checks, not results. PASS
- Failure preservation: build failures recorded verbatim, not hidden; evaluator
  failure row preserved. PASS
- Leakage: no labels used to tune anything. PASS
- Cost: npm registry downloads only (free). No GPU, no Modal, no endpoint. PASS

SCIENTIFIC VALIDATION:
- No scientific behavior repaired or changed.
- Temporal question, GRCh38 scope, >=2-star rule, 8,192 contract all untouched.
- No clinical claims introduced; no old result promoted.

ENGINEERING VALIDATION:
- Validation 1: a baseline status report exists even though some tests fail. PASS
- Validation 2: every failure categorized as environment / code / dependency /
  external-service. PASS
- .venv-baseline confirmed gitignored; not staged.

COST / EXTERNAL CALLS:
- npm ci / pip install: public package registries (free).
- No GPU, no Modal, no paid calls, no old endpoint contacted.

EVIDENCE GENERATED:
- artifacts/baseline/command_log.txt
- docs/bootstrap/BASELINE_SMOKE_TEST.md (15-check results table + categorization)

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc, a1f56e0, 316e5ae, 649b35a; this
  milestone's files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- The old frontend does not pass its own lint gate (158 ESLint findings). The new
  apps/web (M18) starts from this code, so the lint debt must be resolved or the
  gate redefined during the frontend migration.
- The old frontend requires a build-time endpoint URL; the new workbench must support
  a safe no-model/offline mode (M91).
- The evaluator's live-endpoint path and the backend GPU path remain NOT RUN by design.

NEXT MILESTONE:
7 - Establish the new project identity and scientific naming

DO NOT CONTINUE IF:
- a baseline failure cannot be categorized;
- any old result is promoted to EvoVariant-TR evidence;
- paid GPU work was executed.

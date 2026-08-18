MILESTONE: 5/100
TITLE: Audit the legacy frontend and public-data interaction model

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-4 repo (commit 316e5ae) with backend audit + refactor candidates.
- Legacy evo2-frontend/: Next.js 15 app, 14 tsx + 3 ts + config files, package-lock.json.
- No docs/audit/FRONTEND_AUDIT.md, no frontend_data_flow.md.

WHAT CHANGED:
- Traced page.tsx and all components.
- Traced every genome-api.ts network call (6 GET to UCSC/NCBI + 1 POST to Modal).
- Identified env vars and browser-visible endpoint configuration.
- Identified direct browser calls to external genomic services.
- Identified current error/loading states (present but basic; no timeout/retry/AbortSignal).
- Identified assumptions that a model result is a clinical classification.
- Recorded accessibility, responsiveness, and reproducibility limitations.
- Did NOT redesign.
- Updated milestone ledger (005 → PASS).

FILES CREATED:
- docs/audit/FRONTEND_AUDIT.md
- docs/audit/frontend_data_flow.md
- docs/project/reports/milestone_005.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 005)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- cd evo2-frontend && npm ci  → success (external call: npm public registry)
- cd evo2-frontend && npm run typecheck  → tsc --noEmit, EXIT_CODE=0
- rg -n "fetch(|NEXT_PUBLIC|ClinVar|UCSC|prediction|confidence|pathogenic|benign" evo2-frontend/src  → 50 matches
- rg -n "NEXT_PUBLIC" evo2-frontend/src  → 1 client var (endpoint URL)
- npm audit  → 12 vulnerabilities (2 low, 1 moderate, 8 high, 1 critical)
- rg -n "isLoading|setError|error|Loading|disabled" page.tsx
- rg -n "prediction|Likely|confidence|delta" variant-analysis.tsx
- rg -n "agrees|differs|Assessment|prediction" variant-comparison-modal.tsx
- sed -n '355,395p' genome-api.ts (variant POST body)
- rg -n "AbortSignal|signal|timeout|retry" evo2-frontend/src → NO_TIMEOUT_OR_RETRY_IN_FRONTEND
- git check-ignore evo2-frontend/node_modules → IGNORED_OK

TESTS:
- Happy path: npm ci + typecheck pass; audit docs generated. PASS
- Invalid input: N/A (audit milestone); guardrail = NEXT_PUBLIC secret check found
  only a non-secret URL. PASS
- Boundary: N/A for coordinates; boundary analog = complete enumeration of all 7
  data flows. PASS
- Repetition: typecheck run once (deterministic tsc); rg searches consistent. PASS
- Regression: no prior tests. N/A
- Provenance: every data flow recorded with file:line + destination URL. PASS
- Evidence stage: no metric promoted. PASS
- Failure preservation: npm audit findings recorded, not hidden. PASS
- Leakage: no labels involved. PASS
- Cost: npm ci + npm audit hit the public npm registry (free, no GPU, no Modal). PASS

SCIENTIFIC VALIDATION:
- Temporal question untouched; GRCh38 scope untouched; >=2-star rule untouched.
- 8,192 contract untouched (frontend does not build windows).
- No threshold tuning; no clinical claims introduced (clinical framing documented
  as legacy and slated for removal at M93).

ENGINEERING VALIDATION:
- Validation 1: frontend dependency installation is reproducible (npm ci success). PASS
- Validation 2: all browser/server data flows are documented (7 flows). PASS
- Validation 3: no secret is exposed through NEXT_PUBLIC variables (only a URL). PASS
- node_modules confirmed gitignored (not staged).

COST / EXTERNAL CALLS:
- npm ci: downloaded packages from the public npm registry (free). No GPU, no Modal,
  no paid calls.
- npm audit: queried the npm advisory database (free).

EVIDENCE GENERATED:
- docs/audit/FRONTEND_AUDIT.md
- docs/audit/frontend_data_flow.md (7 data flows, env-var analysis, contract)

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc, a1f56e0, 316e5ae; this milestone's
  files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- 12 npm audit vulnerabilities (incl. 1 critical via sharp/libvips) must be resolved
  or accepted with justification at M97.
- The app is not reproducible offline (depends on live UCSC/NCBI + a deployed Modal
  URL); the new workbench must support a safe no-model mode (M91).
- Accessibility and mobile responsiveness are unverified; scheduled for M97.

NEXT MILESTONE:
6 - Reproduce the old project locally only as a baseline smoke test

DO NOT CONTINUE IF:
- a secret is found exposed via NEXT_PUBLIC;
- frontend installation becomes non-reproducible;
- any scientific behavior is accidentally changed during this audit.

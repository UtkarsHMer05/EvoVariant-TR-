MILESTONE: 7/100
TITLE: Establish the new project identity and scientific naming

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-6 repo (commit 53094ff) with baseline smoke test.
- Legacy naming present in snapshot files (README "Evo2 Variant Analysis",
  package/modal names "variant-analysis-evo2*").
- No docs/project/PROJECT_IDENTITY.md, no docs/terminology/.

WHAT CHANGED:
- Defined canonical project title EvoVariant-TR and short package name evovariant_tr.
- Defined a NEW Modal app name (evovariant-tr-v2) and volume (evovariant-tr-model-cache),
  distinct from the old deployment identity.
- Defined research-only product wording and a banned-claims list.
- Defined five evidence stages (SYNTHETIC_TEST, LEGACY_BASELINE, ENGINEERING_PILOT,
  PRELIMINARY, FINAL) with promotion rules.
- Banned clinical-decision wording from default UI/API.
- Created terminology and abbreviation files (GLOSSARY.md, EVIDENCE_STAGES.md).
- Did NOT modify saved baseline artifacts.
- Updated milestone ledger (007 → PASS).

FILES CREATED:
- docs/project/PROJECT_IDENTITY.md
- docs/terminology/GLOSSARY.md
- docs/terminology/EVIDENCE_STAGES.md
- docs/project/reports/milestone_007.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 007)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- mkdir -p docs/terminology
- rg -n "Evo2 Variant Analysis|variant-analysis-evo2" . (excluding .git/node_modules/lock)
- rg -c "evovariant_tr|evovariant-tr-v2|EvoVariant-TR" docs/project/PROJECT_IDENTITY.md → 10
- rg -l "variant-analysis-evo2" src services apps pyproject.toml Makefile → NO_OLD_NAME_IN_NEW_CODE
- rg -c "Banned default wording|Deprecated legacy terms" identity + glossary → present
- rg -c "research-only|Research-only" docs/project/PROJECT_IDENTITY.md → 2

TESTS:
- Happy path: identity + glossary + evidence-stage docs created. PASS
- Invalid input: N/A (documentation milestone); guardrail = old-name leak check
  confirms no new source/config carries legacy names. PASS
- Boundary: N/A. PASS
- Repetition: rg searches consistent. PASS
- Regression: no prior tests. N/A
- Provenance: naming decisions recorded with legacy→new mapping table. PASS
- Evidence stage: five stages defined with enforcement rules. PASS
- Failure preservation: N/A. PASS
- Leakage: no labels involved. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- Temporal question restated precisely in glossary; not changed.
- GRCh38 SNV scope restated; not widened.
- >=2-star rule restated as primary gate.
- 8,192 contract referenced; intact.
- No clinical-use claim introduced; clinical wording explicitly banned.

ENGINEERING VALIDATION:
- Validation 1: new naming is distinct from the source snapshot (mapping table +
  leak check). PASS
- Validation 2: clinical-sounding terms have an explicit deprecation plan
  (banned list + deprecated-terms section). PASS
- Validation 3: research-only boundary is documented. PASS

COST / EXTERNAL CALLS:
- None.

EVIDENCE GENERATED:
- docs/project/PROJECT_IDENTITY.md
- docs/terminology/GLOSSARY.md
- docs/terminology/EVIDENCE_STAGES.md

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc, a1f56e0, 316e5ae, 649b35a, 53094ff;
  this milestone's files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- The Modal app name evovariant-tr-v2 is a proposal; final confirmation with the user
  happens at Milestone 52 before any deployment.
- Evidence-stage enforcement is specified here but only becomes executable code at
  Milestone 13.

NEXT MILESTONE:
8 - Define the target monorepo architecture before moving code

DO NOT CONTINUE IF:
- new naming collides with the source snapshot;
- clinical-sounding terms lack a deprecation plan;
- the research-only boundary is undocumented.

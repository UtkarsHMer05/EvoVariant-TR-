MILESTONE: 9/100
TITLE: Write Architecture Decision Records for high-risk design choices

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-8 repo (commit c973fac) with target architecture + dependency rules.
- No docs/adr/ directory.

WHAT CHANGED:
- Wrote 10 ADRs covering the high-risk decisions: fresh-repository isolation,
  archived ClinVar, exact GRCh38 reference, zero-shot policy, exact 8,192-base
  windows, forward/RC retention, disjoint calibration, Modal cost gates,
  no test-label threshold tuning, evidence-stage UI labels.
- Each ADR has Context, Decision, Alternatives, Consequences, Validation sections.
- Wrote docs/adr/README.md index with an explicit OPEN-items list (not guessed).
- Updated milestone ledger (009 → PASS).

FILES CREATED:
- docs/adr/0001-fresh-repository.md
- docs/adr/0002-temporal-clinvar.md
- docs/adr/0003-grch38-reference.md
- docs/adr/0004-zero-shot-policy.md
- docs/adr/0005-exact-8192-windows.md
- docs/adr/0006-forward-rc-retention.md
- docs/adr/0007-disjoint-calibration.md
- docs/adr/0008-modal-cost-gates.md
- docs/adr/0009-no-test-label-tuning.md
- docs/adr/0010-evidence-stage-ui.md
- docs/adr/README.md
- docs/project/reports/milestone_009.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 009)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- mkdir -p docs/adr
- ls docs/adr/0*.md | wc -l → 10
- per-ADR grep for the 5 required sections → SECTION_CHECK_DONE (none missing)
- grep -c "OPEN" docs/adr/README.md → 2

TESTS:
- Happy path: 10 ADRs + index created. PASS
- Invalid input: N/A (documentation milestone); guardrail = section-presence check
  confirms no ADR is missing a required section. PASS
- Boundary: N/A. PASS
- Repetition: section check deterministic. PASS
- Regression: no prior tests. N/A
- Provenance: each decision records rationale + validation gate. PASS
- Evidence stage: N/A (no outputs produced). PASS
- Failure preservation: N/A. PASS
- Leakage: no labels involved. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- Temporal question, GRCh38 scope, >=2-star rule, 8,192 contract, fwd/RC retention,
  disjoint calibration, and no-test-tuning are all codified as explicit decisions.
- No clinical-use claim introduced; evidence-stage labeling codified.

ENGINEERING VALIDATION:
- Validation 1: at least ten ADRs exist with Context/Decision/Alternatives/
  Consequences/Validation sections (10 ADRs, all sections present). PASS
- Validation 2: unknown decisions are marked OPEN rather than guessed (GRCh38 bytes,
  Modal app name, checkpoint choice, edge policy). PASS

COST / EXTERNAL CALLS:
- None.

EVIDENCE GENERATED:
- docs/adr/*.md (10 ADRs + README index)

GIT STATUS:
- branch main; this milestone's files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- OPEN: exact GRCh38 source bytes (M31), Modal app name confirmation (M52),
  checkpoint choice (M49), edge-window policy (M43). These are deliberately deferred
  to their milestones rather than guessed.

NEXT MILESTONE:
10 - Commit the untouched baseline audit and freeze the migration plan

DO NOT CONTINUE IF:
- fewer than ten ADRs exist or any lacks a required section;
- an unknown decision was guessed instead of marked OPEN.

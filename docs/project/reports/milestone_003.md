MILESTONE: 3/100
TITLE: Audit the legacy scientific behavior without accepting it as the new design

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-2 repo (commit be87edc) with baseline snapshot + architecture inventory.
- Legacy source: evo2-backend/main.py (376 lines), evaluation/evaluate_modal_endpoint.py
  (491 lines), evo2-frontend/src, legacy README/PPT, evaluation/results/final_100.
- No docs/audit/ directory.

WHAT CHANGED:
- Traced the full frontend→backend request path.
- Located every hard-coded threshold, std, confidence formula, model name, genome
  assembly, window length, and endpoint URL.
- Identified binary "Likely pathogenic"/"Likely benign" language and the
  classification_confidence heuristic.
- Identified all BRCA1-specific assumptions (dataset, GRCh37 FASTA, first-500 subset,
  ROC-Youden threshold derivation).
- Identified live UCSC/NCBI network dependencies in the inference path.
- Documented threshold-selection leakage (threshold + stds derived on the same rows
  later used for the 100-row evaluation).
- Documented the 8,193-base window defect.
- Wrote LEGACY_SCIENTIFIC_AUDIT.md and HARDCODED_ASSUMPTIONS.csv (33 rows).
- Updated milestone ledger (003 → PASS).

FILES CREATED:
- docs/audit/LEGACY_SCIENTIFIC_AUDIT.md
- docs/audit/HARDCODED_ASSUMPTIONS.csv
- docs/project/reports/milestone_003.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 003)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- rg -n "threshold|confidence|BRCA1|8192|evo2_7b|UCSC|ClinVar|Likely pathogenic|Likely benign|modal" . (repo-wide, excluding .git/docs/png/lock)
- rg -n same-pattern evo2-backend/main.py evo2-frontend/src
- Read evo2-backend/main.py (full), evaluation/evaluate_modal_endpoint.py (lines 1-300)
- python3 csv.DictReader validation of HARDCODED_ASSUMPTIONS.csv → 33 rows, CSV_OK
- rg -l "0.0009178519" (threshold constant location check)
- rg -c "LEGACY_BASELINE_ONLY" docs/audit + docs/bootstrap

TESTS:
- Happy path: audit + CSV generated and CSV parses cleanly. PASS
- Invalid input: N/A (documentation milestone); guardrail = CSV schema check
  (every row has non-empty disposition). PASS
- Boundary: threshold constant confirmed present only in legacy code + legacy docs +
  new audit docs (not in any new scientific module). PASS
- Repetition: rg searches run twice with consistent results. PASS
- Regression: no prior tests. N/A
- Provenance: every assumption has file:line + disposition. PASS
- Evidence stage: all legacy metrics labeled LEGACY_BASELINE_ONLY. PASS
- Failure preservation: no failures; nothing dropped. PASS
- Leakage: leakage itself is the subject of the audit and is documented. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- Temporal t0/t1 question untouched.
- GRCh38 SNV scope not widened (legacy hg19 flagged as legacy-only).
- >=2-star rule not touched (not yet implemented).
- Final temporal labels NOT used to tune anything.
- 8,192-base contract intact as the target; legacy 8,193 defect flagged, not inherited.
- Raw forward/RC retention: legacy code has NO RC path (forward only) — noted as a
  gap the new design must fill.
- Calibration/test overlap: legacy leakage documented; new design requires zero overlap.
- Missing predictor values: not applicable yet.
- Evidence-stage language correct; no clinical-use claim introduced.

ENGINEERING VALIDATION:
- Core logic not coupled to Modal in any new code (no new code written).
- No secrets logged; no paths hard-coded in new artifacts.
- No large data added to Git.

COST / EXTERNAL CALLS:
- None. No network, no GPU, no Modal, no paid calls.

EVIDENCE GENERATED:
- docs/audit/LEGACY_SCIENTIFIC_AUDIT.md
- docs/audit/HARDCODED_ASSUMPTIONS.csv (33 hard-coded assumptions, categorized)

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc; this milestone's files in next commit;
  remotes: none; no push.

RISKS / OPEN QUESTIONS:
- Legacy code has no reverse-complement scoring path at all; the new orientation-aware
  contract (delta_primary = mean of fwd + RC) is entirely new work.
- The old README and PPT still contain the deprecated threshold/label language; they
  are legacy docs and will be superseded by the new project identity (Milestone 7).

NEXT MILESTONE:
4 - Audit the legacy backend implementation and identify unsafe coupling

DO NOT CONTINUE IF:
- any hard-coded scientific assumption is found that is not listed;
- the new project silently inherits the BRCA1 cutoff;
- baseline metrics are mislabeled as new evidence.

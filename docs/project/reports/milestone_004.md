MILESTONE: 4/100
TITLE: Audit the legacy backend implementation and identify unsafe coupling

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-3 repo (commit a1f56e0) with scientific audit + assumptions CSV.
- Legacy evo2-backend/: main.py (376 lines), requirements.txt (unpinned), 13
  debug/patch/test experiment files incl. four ~1,630-line attn_interface copies.
- No docs/audit/BACKEND_AUDIT.md, no docs/architecture/.

WHAT CHANGED:
- Read complete backend main.py; listed all 11 responsibilities.
- Documented the in-image vortex/attention monkey patch and its duplication across
  5+ debug files.
- Recorded old CUDA 12.4 / PyTorch 2.4.0 / Transformer Engine 1.13 / FlashAttention
  2.6.3 (cu123 wheel on cu124 torch) assumptions.
- Identified unpinned evo2 git clone and 'evo2_7b' checkpoint ambiguity.
- Identified inference-path network call (UCSC, no timeout/retry/provenance).
- Catalogued missing timeouts, retry policy, provenance fields, batch semantics,
  failure taxonomy, input validation, cost control.
- Proposed module boundaries (no code edited).
- Updated milestone ledger (004 → PASS).

FILES CREATED:
- docs/audit/BACKEND_AUDIT.md
- docs/architecture/backend_refactor_candidates.md
- docs/project/reports/milestone_004.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 004)

FILES REMOVED/MOVED:
- none

COMMANDS RUN:
- python3 -m py_compile evo2-backend/main.py → PY_COMPILE_OK
- rg -n "run_commands|flash|transformer|requests|get_genome_sequence|score_sequences|fastapi|modal" evo2-backend (excluding large patch copies)
- Read evo2-backend/main.py (full, at Milestone 3), debug_returns.py / test_import.py /
  debug_flash_attn*.py excerpts via rg
- grep -c "cannot be final research infrastructure" docs/audit/BACKEND_AUDIT.md → 1
- rg -l "flash_attn_gpu|attn_interface" src services apps → NO_PATCH_IN_NEW_CODE

TESTS:
- Happy path: py_compile passes; audit + refactor-candidate docs generated. PASS
- Invalid input: N/A (audit milestone); guardrail = patch-leak check confirms no
  patch code exists in any new-code directory. PASS
- Boundary: N/A for coordinates; boundary analog = explicit enumeration of all 11
  responsibilities (complete coverage of main.py). PASS
- Repetition: rg coupling search consistent with Milestone-3 search. PASS
- Regression: no prior tests. N/A
- Provenance: every stack assumption recorded with file:line. PASS
- Evidence stage: no legacy metric promoted. PASS
- Failure preservation: N/A (no runs). PASS
- Leakage: no labels involved. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- Temporal question untouched; GRCh38 scope untouched; >=2-star rule untouched.
- 8,192 contract intact as target; legacy defect documented.
- Raw fwd/RC retention: legacy has no RC path — gap documented for new design.
- No threshold tuning on temporal labels (nothing tuned at all this milestone).
- No clinical claims introduced.

ENGINEERING VALIDATION:
- Validation 1: audit explains why the monolith cannot be final research
  infrastructure (7 enumerated reasons). PASS
- Validation 2: no compatibility patch copied into the new architecture
  (NO_PATCH_IN_NEW_CODE; src/services/apps do not exist yet). PASS
- py_compile syntax check passes on Python 3.12.8.

COST / EXTERNAL CALLS:
- None. No network, no GPU, no Modal, no paid calls.

EVIDENCE GENERATED:
- docs/audit/BACKEND_AUDIT.md (responsibility map, patch analysis, stack table,
  missing-properties catalogue)
- docs/architecture/backend_refactor_candidates.md (responsibility→module map,
  dependency rules, migration order)

GIT STATUS:
- branch main; commits 354e987, 4f7bc14, be87edc, a1f56e0; this milestone's files in
  next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- Whether the vortex/flash-attn patch is still needed can only be answered at M51
  against current official Evo 2 docs; current evidence (7B light-install path)
  suggests it is not.
- The cu123 wheel on cu124 torch mismatch is a latent instability; the new image
  will use officially recommended versions instead.
- Legacy debug files remain in-tree until the old stack is superseded; they are
  audit input only.

NEXT MILESTONE:
5 - Audit the legacy frontend and public-data interaction model

DO NOT CONTINUE IF:
- a compatibility patch is found copied into new code;
- the audit cannot account for every main.py responsibility;
- model/checkpoint identity questions are silently ignored instead of routed to M49/M51.

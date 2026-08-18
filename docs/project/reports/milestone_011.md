MILESTONE: 11/100
TITLE: Transcribe the frozen research protocol into canonical repository files

STATUS:
PASS

WHAT EXISTED BEFORE:
- Milestone-10 repo (commit 5dbab50): Phase 1 complete; research/protocol/ existed
  as an empty skeleton (.gitkeep).
- No PROTOCOL.md, protocol.yaml, or DEVIATION_LOG.md.

WHAT CHANGED:
- Transcribed the approved research specification into PROTOCOL.md (human-readable)
  and protocol.yaml (machine-readable twin).
- Recorded protocol version 1.0.0 and the SHA-256 hash of protocol.yaml.
- Distinguished immutable primary fields from exploratory/sensitivity fields.
- Defined the deviation procedure (DEVIATION_LOG.md, currently empty).
- No value was derived from future model performance.
- Updated milestone ledger (011 → PASS).

FILES CREATED:
- research/protocol/PROTOCOL.md
- research/protocol/protocol.yaml
- research/protocol/DEVIATION_LOG.md
- docs/project/reports/milestone_011.md (this report)

FILES MODIFIED:
- docs/project/MILESTONE_STATUS.md (ledger row 011)

FILES REMOVED/MOVED:
- research/protocol/.gitkeep (superseded by real files)

COMMANDS RUN:
- shasum -a 256 research/protocol/protocol.yaml
  → 78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525
- python3 YAML parse + key-value assertions (t0/t1 dates, >=2-star gate, 8192 bp,
  AUROC primary, seed 20260814, 2000 replicates) → YAML_PARSE_AND_KEY_VALUES_OK

TESTS:
- Happy path: protocol files created; YAML parses; key values assert correctly. PASS
- Invalid input: N/A at this milestone (schema enforcement lands at M12); guardrail
  = explicit key-value assertions on the parsed YAML. PASS
- Boundary: N/A. PASS
- Repetition: protocol hash is deterministic (file content frozen). PASS
- Regression: no prior tests. N/A
- Provenance: protocol version + SHA-256 + frozen date recorded. PASS
- Evidence stage: N/A (no results produced). PASS
- Failure preservation: N/A. PASS
- Leakage: protocol explicitly forbids test-informed choices; nothing tuned. PASS
- Cost: no external/GPU/paid calls. PASS

SCIENTIFIC VALIDATION:
- t0/t1 temporal question transcribed verbatim; not changed.
- GRCh38 SNV scope preserved; >=2-star primary gate preserved.
- 8,192-base contract preserved; fwd/RC retention preserved.
- Calibration disjointness and no-test-tuning preserved.
- QA checkpoint numbers recorded as validation target only, never to be injected.

ENGINEERING VALIDATION:
- Validation 1: YAML validates (parses; key assertions pass). Full schema validation
  is enforced at Milestone 12. PASS
- Validation 2: human (PROTOCOL.md) and machine (protocol.yaml) protocol agree
  (same values transcribed in both). PASS
- Validation 3: protocol hash recorded before any temporal model outcomes are
  inspected (no model has been run). PASS

COST / EXTERNAL CALLS:
- None.

EVIDENCE GENERATED:
- research/protocol/PROTOCOL.md
- research/protocol/protocol.yaml (SHA-256 78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525)
- research/protocol/DEVIATION_LOG.md (empty; no deviations)

GIT STATUS:
- branch main; this milestone's files in next commit; remotes: none; no push.

RISKS / OPEN QUESTIONS:
- PyYAML is not yet a declared dependency (lands with the M16 scaffold); the parse
  check used the system python3 which has PyYAML available.
- Schema-level rejection of unknown keys is implemented at Milestone 12.

NEXT MILESTONE:
12 - Define protocol and configuration schemas

DO NOT CONTINUE IF:
- the YAML fails to validate;
- human and machine protocol disagree;
- the protocol hash is recorded after temporal outcomes are inspected.

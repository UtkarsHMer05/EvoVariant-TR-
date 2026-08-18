# MIGRATION PLAN — EvoVariant-TR

Frozen at Milestone 10 (2026-08-18). This plan governs the incremental conversion of
the supplied EvoVariant source snapshot into the research-grade EvoVariant-TR
repository across 100 gated milestones. Changes to this plan require a dated note in
`research/protocol/DEVIATION_LOG.md` when they affect the scientific protocol.

## 1. Principles

1. **One milestone at a time.** No combining milestones to move faster. No starting
   the next milestone before the current gate passes.
2. **Incremental migration.** No big-bang rewrite. Legacy code stays in-tree as the
   baseline until its replacement passes the relevant gate; removal happens with
   attribution.
3. **Science before infrastructure before scale.** Protocol → data → sequence
   semantics → fake-scorer integration → official parity → small pilots → resumable
   scoring → full run only after explicit approval → analysis → UI → release.
4. **No fabrication.** Null/negative/unavailable results are valid; fabricated
   success is never valid. GPU work not run is marked NOT RUN.
5. **No leakage.** Temporal-test outcomes never influence thresholds, calibrators,
   checkpoints, context, centering, comparators, subgroups, score sign, or
   abstention cutoffs.
6. **Fresh identity.** No old-repository remote, history, deployment identity,
   endpoint URL, or saved output is reused as new evidence.

## 2. Phase map (100 milestones)

| Phase | Milestones | Deliverable summary |
|---|---|---|
| 1. New repo + baseline audit | 1–10 | Fresh repo, immutable snapshot inventory, scientific/backend/frontend audits, baseline smoke test, identity, architecture, ADRs, this plan |
| 2. Research contract + quality foundation | 11–21 | Frozen protocol (md+yaml+hash), config/evidence/registry/manifest modules, Python scaffold, test taxonomy, frontend move to apps/web, secrets/cost policy, Makefile, data-layout policy |
| 3. Deterministic data | 22–40 | ClinVar t0/t1 archive discovery/download/parse, classification + review-status normalization, variant identity, eligibility, temporal join, GRCh38 reference freeze + indexed FASTA, coordinate tests, reference QC, dedup policy, primary + calibration cohorts, zero-overlap guard, cohort freeze |
| 4. Exact sequence semantics | 41–46 | 8,192-base window contract, window builder, edge policy, mutation invariants, reverse-complement transform, sequence cache |
| 5. Scoring core (no GPU) | 47–50 | Scorer interface, deterministic fake scorer (SYNTHETIC_TEST only), Evo 2 parity spec, end-to-end fake-scorer pipeline |
| 6. Official Evo 2 runtime + parity | 51–59 | Clean pinned Modal environment, new Modal app identity, clean image, model-cache volume, model-load smoke, official self-test, tiny-sequence parity, one-variant pilot, RC pilot |
| 7. Throughput + resumability | 60–68 | Multi-gene pilot + cost projection, shard format, deterministic sharding, idempotent resume, failure taxonomy, persistent scoring service, detached batch submission, 25-variant resume pilot, 100-variant throughput pilot |
| 8. Full run (approval-gated) | 69–70 | Approval gate artifact; full 1,024-variant primary scoring, frozen raw table |
| 9. Comparators + calibration + statistics | 71–80 | Comparator contract, PhyloP, CADD, GPN feasibility, AlphaMissense subset, calibration scoring plan, Platt fit, isotonic sensitivity, metrics + gene-clustered bootstrap, frozen primary + paired comparator analysis |
| 10. Robustness + validity | 81–90 | Orientation disagreement, context-length + center-shift robustness, review-status sensitivity, gene-held-out transport, consequence subgroups, coverage/missingness, risk-coverage/abstention, error analysis, bias/validity audit |
| 11. Research API + UI | 91–97 | FastAPI research service, async job API, research workbench UI, single-variant UI, benchmark dashboard, methods/provenance mode, security/a11y/E2E validation |
| 12. Reproduction + release | 98–100 | Clean-room reproduction from fresh clone, paper/report generation from registered outputs, final release gate + release |

## 3. Hard gates (stop conditions)

Work stops and is investigated if any of these occur (master prompt §16):

- unexpected old Git remote, or a command targets the old repository path;
- a real secret appears in tracked files;
- calibration/test cohort overlap is non-zero;
- unexpected GRCh38 reference mismatch;
- the exact 8,192-base invariant fails;
- model package self-test fails, or the project scorer does not match the official scorer;
- forward/RC mapping test fails;
- a full GPU run is requested before approval;
- output row counts change because failures were dropped;
- model/checkpoint identity cannot be established;
- results are produced with a dirty/unregistered configuration;
- a comparator's version/license/assembly is unknown;
- code substitutes fake output after real model failure;
- a final result table contains synthetic or legacy evidence.

## 4. Cost policy summary

No paid GPU work until: image smoke → official self-test → parity → pilots all pass.
Full primary scoring and calibration scoring each require the explicit approval gate
(Milestone 69) and are submitted only via Modal-native detached execution with
registered run IDs and cost projection on file.

## 5. Completion definition

The migration is complete when Milestone 100 passes: the repository is reproducible
from a clean clone, scientifically honest, fully tested, documented, isolated from
the original repository, and released only after explicit user approval.

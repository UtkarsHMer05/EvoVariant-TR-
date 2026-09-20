# Decisions — EvoVariant-TR ML Extension

This file is append-only in spirit. Change a decision by adding a new superseding entry,
not by erasing history.

## D-001 — Preserve the original frozen zero-shot protocol
Status: ACCEPTED

The original temporal Evo2 zero-shot study remains untouched as the baseline scientific
study. Training/fine-tuning/ensemble work is a separate ML-extension protocol.

Reason:
Retrospective tuning of the original test outcomes would invalidate the original zero-shot
estimand.

## D-002 — Modal is the default GPU provider
Status: ACCEPTED

Modal will host GPU inference, embedding extraction, selected training/fine-tuning, and
research serving. CPU-capable work remains local where practical to preserve credits.

## D-003 — Cache expensive foundation-model outputs
Status: ACCEPTED

Scores and embeddings are computed once per immutable `(model, checkpoint, preprocessing,
variant, orientation, context, layer)` key and reused by downstream ML/HPO.

## D-004 — HPO is performed on frozen features where possible
Status: ACCEPTED

Repeated foundation-model inference per trial is forbidden unless the hyperparameter
actually changes foundation-model computation (e.g. context or layer extraction).

## D-005 — Full Evo2 fine-tuning is not a completion requirement
Status: ACCEPTED

A scientifically valid project can be complete with frozen Evo2 representations,
trainable downstream classifiers, and ensembles. Full large-model fine-tuning is attempted
only if official tooling, stability, and compute budget allow.

## D-006 — Ensemble selection uses error diversity, not accuracy similarity
Status: ACCEPTED

Candidates require validation performance plus complementary error evidence.

## D-007 — Final figures are generated from registry outputs
Status: ACCEPTED

No presentation number is manually inserted if it purports to be an experimental result.

## D-008 — Research-only language
Status: ACCEPTED

Outputs are computational research evidence, not diagnosis or clinical certainty.

## D-009 — Model list is feasibility-gated
Status: ACCEPTED

Preferred candidates are Evo2, Nucleotide Transformer, Caduceus, and appropriate GPN
variants, with CADD/PhyloP and AlphaMissense subset as comparators. The exact final list may
change only after an official-source feasibility/license/compute review.

## D-010 — Locked test policy
Status: ACCEPTED

Final test labels are not used for configuration selection. Post-test changes produce a
new exploratory version and may not be promoted as the original confirmatory result.

## D-011 — Canonical current Modal application identity
Status: ACCEPTED
Date: 2026-09-21
Supersedes: the unresolved `evovariant-tr-v2` proposal/confirmation in historical ADR/project-identity text for the current ML-extension worktree

Context:
Phase 0 found three competing identity states: the active root Modal entrypoint and cost
policy use `evovariant-tr`; `RuntimeConfig`, ADR 0008, and the historical project identity
use `evovariant-tr-v2`; legacy backend/evaluation assets use `variant-analysis-evo2`. The
current root entrypoint is not yet a verified deployment, and this decision does not authorize
deployment or paid compute.

Decision:
Use `evovariant-tr` as the canonical new Modal application/environment identity for the
current EvoVariant-TR ML-extension worktree. Treat `variant-analysis-evo2` as legacy and
forbidden for new infrastructure. Treat `evovariant-tr-v2` as stale historical documentation
until later control-plane reconciliation updates it additively with fresh evidence. Do not
assume the currently referenced `hf_cache` volume is an approved dedicated cache; resolve
the volume identity separately before any paid deployment.

Alternatives:
- Keep `evovariant-tr-v2`: rejected for the current worktree because active code, approval
  policy, and the root app already use `evovariant-tr`.
- Reuse `variant-analysis-evo2`: rejected by the existing cost/security policy and legacy
  evidence boundary.

Consequences:
Later phases must reconcile `RuntimeConfig`, ADR/project-identity references, cache volume,
frontend environment, and deployment manifests without silently claiming that a deployment
exists. No code or deployment was changed in Phase 0.

Validation:
`evo2_scorer_app.py`, `src/evovariant_tr/cost_policy.py`, `artifacts/approvals/full_run_approval.json`,
and the identity search recorded in `docs/agent/BASELINE_AUDIT.md`.

## Template for new decisions

### D-XXX — Title
Status: PROPOSED | ACCEPTED | SUPERSEDED | REJECTED
Date:
Supersedes:
Context:
Decision:
Alternatives:
Consequences:
Validation:

# ADR 0010 — Evidence-stage UI labels

- Status: ACCEPTED
- Date: 2026-08-18

## Context

The legacy UI displayed raw model deltas as "Likely pathogenic"/"Likely benign"
with a "classification_confidence" bar, presenting research output as a clinical
classification. This invites misuse and violates the claim-safety policy.

## Decision

Every user-facing surface (UI, API responses, reports, figures) labels results with
their evidence stage (SYNTHETIC_TEST, LEGACY_BASELINE, ENGINEERING_PILOT,
PRELIMINARY, FINAL) and a research-only disclaimer. Default UI/API never emits
clinical-decision wording. Raw scores are shown as raw scores; calibrated outputs
are shown as study probabilities with the protocol context; unavailable/failure
states are explicit. Synthetic output is opt-in and unmistakably labeled.

## Alternatives

1. Keep clinical labels with a disclaimer — rejected: the labels themselves are the
   claim; a disclaimer does not neutralize them.
2. Hide all metrics from the UI — rejected: the workbench must display registered
   results; the fix is labeling, not concealment.
3. Let each view choose its own labeling — rejected: stage labeling is global and
   enforced by shared components/types.

## Consequences

- API responses include `evidence_stage` and provenance (Milestone 91).
- Workbench shows stage globally and per-metric (Milestones 93-96).
- Tests assert synthetic results cannot be presented or registered as final
  (Milestones 13, 48).

## Validation

- UI acceptance: no label presents a raw delta as a calibrated probability or a
  diagnosis (Milestones 93-94 gates).
- Forbidden-promotion tests pass (Milestone 13).

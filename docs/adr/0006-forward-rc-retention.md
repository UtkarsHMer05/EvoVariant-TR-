# ADR 0006 — Forward and reverse-complement retention

- Status: ACCEPTED
- Date: 2026-08-18

## Context

DNA is double-stranded; a strand-agnostic model should score a sequence and its
reverse complement consistently, but real models can disagree. The primary
orientation-aware score is `delta_primary = (delta_fwd + delta_rc) / 2`. Retaining
only a mean would hide orientation disagreement, which is itself a robustness
signal.

## Decision

For every variant, compute and retain all raw components: reference/alternate
scores and delta on the forward strand, the same on the reverse-complement
representation, the primary mean delta, the absolute forward/RC disagreement, and
an orientation disagreement flag/summary — plus full provenance (hashes, window
coordinates, mutation index, model identity, runtime). The mean is never the only
retained value. Raw scores are never converted directly to a clinical label.

## Alternatives

1. Forward-only scoring (legacy behavior) — rejected: ignores strand effects and
   the protocol's orientation-aware primary score.
2. Retain only delta_primary — rejected: hides disagreement needed for robustness
   analysis (Milestone 81).
3. Choose the better-performing orientation after seeing outcomes — rejected:
   orientation policy is predeclared; post-hoc selection is forbidden.

## Consequences

- Four sequence scores per variant (ref/alt × fwd/RC) → doubles compute vs
  forward-only; accepted.
- Requires correct RC transformation with allele/index mapping (Milestone 45) and
  RC parity validation (Milestone 59).
- Orientation disagreement becomes a first-class analysis (Milestone 81).

## Validation

- RC round-trip and index-mapping tests (Milestone 45).
- Pilot asserts delta_primary equals the arithmetic mean of delta_fwd and delta_rc
  (Milestone 59).

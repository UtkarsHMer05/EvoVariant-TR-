# ADR 0005 — Exact 8,192-base sequence windows

- Status: ACCEPTED (exact convention frozen at Milestone 41)
- Date: 2026-08-18

## Context

The primary context length is exactly 8,192 bases. The legacy window formula
produced 8,193 bases for ordinary interior positions (`end - start == 8193`), an
off-by-one that silently changes model input length. Even-length windows require an
explicit, documented centering convention because an SNV cannot sit at the exact
center of an even-length interval.

## Decision

Define one precise even-window convention with hard runtime assertions:
`end - start == 8192`, `len(sequence) == 8192`,
`sequence[variant_local_index] == declared_reference`, and
`HammingDistance(ref_context, alt_context) == 1`. The one-based genomic position to
zero-based half-open interval conversion is documented and exhaustively tested. The
legacy formula is not reused. Chromosome-edge behavior is predeclared and
outcome-blind (Milestone 43).

## Alternatives

1. Keep the legacy formula — rejected: produces 8,193-base contexts.
2. Odd-length window (e.g., 8,191 or 8,193) centered exactly on the variant —
   rejected: protocol fixes 8,192.
3. Variable-length windows near edges — rejected for primary rows: no primary row
   may receive an 8,191/8,193-length context; edge policy is exclude-or-shift,
   predeclared (Milestone 43).

## Consequences

- Requires coordinate-convention tests (Milestone 33), window builder (Milestone 42),
  edge policy (Milestone 43), mutation invariants (Milestone 44).
- The exact centering rule (which of the two middle positions holds the variant) is
  fixed at Milestone 41 and never tuned on outcomes.

## Validation

- `tests/unit/scoring/test_window_contract.py` asserts all four invariants
  (Milestone 41).
- Edge tests confirm no 8,191/8,193 primary contexts (Milestone 43).

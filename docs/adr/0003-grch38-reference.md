# ADR 0003 — Exact GRCh38 reference source and checksum

- Status: ACCEPTED (source selection to be finalized with checksum at Milestone 31)
- Date: 2026-08-18

## Context

Scoring requires exact 8,192-base reference contexts. The legacy backend fetched
sequence live from UCSC per request (unversioned, non-reproducible) and the legacy
BRCA1 analysis used GRCh37. Mixing assemblies or live retrieval breaks
reproducibility and reference-allele validation.

## Decision

Use exactly one versioned GRCh38 reference FASTA from an authoritative source,
downloaded once, SHA-256 checksummed, and manifested before any cohort reference QC
or scoring. Chromosome naming mapping is documented. No hg19/GRCh37 substitution. No
per-request network sequence retrieval for final experiments. The exact source
accession/URL and checksum are recorded at Milestone 31; this ADR fixes the policy,
not the bytes.

## Alternatives

1. Live UCSC retrieval at scoring time (legacy behavior) — rejected: unversioned,
   non-reproducible, no checksum, network in the deterministic path.
2. GRCh37/hg19 — rejected: protocol specifies GRCh38; no silent liftover.
3. Multiple references for different analyses — rejected: one frozen reference for
   the primary study to keep a single coordinate/allele contract.

## Consequences

- Requires indexed local FASTA access (Milestone 32) and exhaustive coordinate tests
  (Milestone 33).
- Reference checksum becomes part of every run's provenance and cache keys.
- Variants whose declared ref allele mismatches the frozen reference are excluded
  with reason codes (Milestone 34), never auto-swapped.

## Validation

- `data/manifests/grch38.json` records source, accession/version, retrieval date,
  SHA-256 (Milestone 31).
- Reference-allele QC reports zero mismatches among retained primary variants
  (Milestone 34).

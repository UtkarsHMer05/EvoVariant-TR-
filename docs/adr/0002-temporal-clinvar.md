# ADR 0002 — Archived ClinVar releases rather than live labels

- Status: ACCEPTED
- Date: 2026-08-18

## Context

The primary scientific question is temporal: among variants classified as VUS in a
fixed historical ClinVar release (t0 = 2025-01-02 archived `variant_summary`), how
well does a frozen zero-shot Evo 2 score distinguish the direction of later
resolution in a later release (t1 = 2026-08-06 archived `variant_summary`)? Live
ClinVar queries change daily and would make the cohort non-reproducible and
susceptible to inadvertent label leakage from the future.

## Decision

Use only the two official NCBI archived releases, downloaded once, checksummed, and
manifested (Milestones 22-24). All cohort logic operates on these frozen files. Live
ClinVar access is permitted only as a UI convenience clearly separated from the
research pipeline, never as a cohort source.

## Alternatives

1. Live ClinVar API at analysis time — rejected: non-reproducible, rolling target,
   leakage risk, no fixed denominator.
2. Nearest-date archived release substitution — rejected without a recorded protocol
   deviation; exact requested releases are required (Milestone 22 gate).
3. Third-party ClinVar mirrors — rejected for primary data; official NCBI sources only.

## Consequences

- Cohort construction is fully reproducible from public archives.
- Requires implementing archive discovery, streaming download, checksumming, and
  version-aware parsing (Milestones 22-25).
- If an exact archived file is unavailable, the milestone stops rather than
  substituting.

## Validation

- Manifests `data/manifests/clinvar_t0.json` and `clinvar_t1.json` record exact
  source URL, release date, retrieval date, and SHA-256 (Milestones 23-24).
- Parser rejects schema drift (Milestone 25).

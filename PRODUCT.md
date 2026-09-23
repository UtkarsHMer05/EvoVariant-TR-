# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Researchers, reviewers, and technical judges who need to inspect EvoVariant-TR
variant-analysis evidence, benchmark scope, provenance, and limitations.

## Product Purpose

EvoVariant-TR is a research-only web surface for GRCh38 temporal variant
analysis. It makes registered model signals, benchmark artifacts, and their
evidence boundaries inspectable without presenting a clinical classification.

## Positioning

The product joins a working variant-analysis workflow to an immutable,
stage-qualified benchmark record: every scientific headline is linked to a
source artifact, cohort, protocol, or explicit blocked state.

## Operating Context

The existing app supports genome selection, gene search, chromosome browsing,
and variant research inspection. The benchmark hub is a mostly static,
manifest-driven research presentation for judge and review workflows.

## Capabilities and Constraints

- The frozen 946-row temporal result is immutable.
- The development cohort contains 4,000 rows and remains separate from the
  locked cohort.
- New fine-tuning and new paid inference are not silently implied by the
  benchmark hub.
- Unavailable data or compute is shown as DATA_BLOCKED or COMPUTE_BLOCKED.
- The app uses the existing Next.js, React, Tailwind, Radix, and Lucide stack.

## Evidence on Hand

- Frozen Phase 14 artifacts under artifacts/phase14 and research/runs.
- ClinVar T0/T1 snapshots under data/raw/clinvar.
- Generated benchmark registry and manifest under research/benchmarks,
  artifacts/benchmarks, docs/benchmarks, and apps/web/public/benchmarks.
- Existing variant-analysis UI under apps/web/src.

## Product Principles

1. Preserve the scientific stage boundary.
2. Link claims to inspectable evidence.
3. Prefer explicit limitations to unsupported completeness.
4. Keep the normal variant workflow working while adding research navigation.

## Accessibility & Inclusion

The benchmark hub must use semantic headings, keyboard-accessible tabs, visible
focus states, accessible tables and links, responsive layouts, and useful
empty or blocked states.

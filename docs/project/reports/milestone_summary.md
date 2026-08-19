# EvoVariant-TR Milestone Summary

## Completed (PASS)
- **M001-M019**: Project setup, validation gates, cost control, security policy
- **M020**: Makefile and command reference
- **M021-M024**: Data directory structure, ClinVar archive discovery and download
- **M025-M030**: ClinVar parsing, normalization, cohort construction
- **M031-M032**: GRCh38 reference genome
- **M033-M037**: Cohort validation, coordinate tests
- **M038-M040**: Calibration cohort, disjointness, QC package
- **M041-M043**: Sequence window convention (8,192 bp)
- **M044-M045**: Alternate sequence mutation, reverse-complement transformation
- **M046**: Deterministic sequence cache
- **M047**: Model-agnostic scorer interface
- **M048**: Deterministic fake scorer for tests
- **M049**: Evo 2 parity requirements
- **M051-M054**: Modal configuration and model cache
- **M061-M066**: Scoring record format, deterministic sharding, batch submission
- **M063-M064**: Resume/retry, failure taxonomy
- **M069**: Full-run approval gate (cost control)
- **M071-M075**: Comparator adapter contract, PhyloP, CADD, GPN-MSA, AlphaMissense
- **M079**: Full metrics and gene-clustered uncertainty engine
- **M088**: Risk-coverage and abstention analysis
- **M089-M090**: Structured error analysis, bias audit
- **M091-M092**: Research FastAPI service, async batch API
- **M093-M096**: Next.js research workbench, single-variant UI, methods/provenance

## Blocked (WAIT - requires GPU/Modal runtime)
- **M055-M060**: Evo 2 model load, inference self-test, sequence-score validation — requires GPU
- **M065**: Persistent Modal scoring service — requires Modal deployment
- **M067-M068**: Resumability/throughput pilots — requires GPU
- **M070**: Full primary Evo 2 scoring — requires GPU + approval

## Pending (requires Evo 2 scores or downstream work)
- **M076-M078**: Score calibration cohort, Platt fit, isotonic calibration — requires scores
- **M080-M087**: Primary analysis, RC disagreement, context-length/robustness, sensitivity analyses — requires scores
- **M097**: Security, accessibility, E2E validation — requires full deployment
- **M098**: Clean-room reproduction — requires full deployment
- **M099**: Paper figures — requires analysis results
- **M100**: Final release gate — requires all prior work

## Software Infrastructure Status
All core Python modules implemented and validated:
- `calibration.py` — calibration cohort (549,427 variants)
- `cohort_fast.py` — primary cohort (380,776 VUS)
- `sequence_window.py` — 8,192 bp window generation
- `sequence_mutate.py` — SNV/indel mutation, reverse-complement
- `sequence_cache.py` — content-addressed sequence cache
- `scorer.py` — abstract scorer interface
- `fake_scorer.py` — deterministic hash-based scorer for tests
- `evo2_scorer.py` — Evo 2 adapter (importable when torch available)
- `metrics.py` — AUC, ECE, Brier, bootstrap CIs, gene-clustered metrics
- `abstention.py` — risk-coverage curves, abstention analysis
- `batch.py` — sharding, failure taxonomy, resume/retry
- `scoring_record.py` — scoring record and shard format
- `comparator.py` — abstract comparator adapter contract
- `comparator_baselines.py` — PhyloP, CADD, GPN-MSA, AlphaMissense adapters
- `error_analysis.py` — FP/FN analysis, stratified error segments, bias audit
- `api.py` — FastAPI service (health, score/variant, batch, metrics)
- `modal_config.py` — Modal deployment configuration

## Test Results
- **Tests**: 409 total (unit/contract/integration)
- **Coverage**: 95.21% (exceeds 95% gate)
- **Lint**: ruff clean (100 cols)
- **Types**: mypy strict clean (34 source files)

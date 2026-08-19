# MILESTONE STATUS — EvoVariant-TR (100 milestones)

Ledger of milestone gate status. Updated at the end of every milestone.
Status values: `PENDING` | `IN PROGRESS` | `PASS` | `BLOCKED` | `FAILED`.

| # | Title | Status | Date |
|---|---|---|---|
| 001 | Create a genuinely new repository from the supplied source snapshot | PASS | 2026-08-18 |
| 002 | Create an immutable baseline snapshot and repository inventory | PASS | 2026-08-18 |
| 003 | Audit the legacy scientific behavior without accepting it as the new design | PASS | 2026-08-18 |
| 004 | Audit the legacy backend implementation and identify unsafe coupling | PASS | 2026-08-18 |
| 005 | Audit the legacy frontend and public-data interaction model | PASS | 2026-08-18 |
| 006 | Reproduce the old project locally only as a baseline smoke test | PASS | 2026-08-18 |
| 007 | Establish the new project identity and scientific naming | PASS | 2026-08-18 |
| 008 | Define the target monorepo architecture before moving code | PASS | 2026-08-18 |
| 009 | Write Architecture Decision Records for high-risk design choices | PASS | 2026-08-18 |
| 010 | Commit the untouched baseline audit and freeze the migration plan | PASS | 2026-08-18 |
| 011 | Transcribe the frozen research protocol into canonical repository files | PASS | 2026-08-18 |
| 012 | Define protocol and configuration schemas | PASS | 2026-08-18 |
| 013 | Implement evidence-stage types and claim guards | PASS | 2026-08-18 |
| 014 | Design the immutable experiment registry | PASS | 2026-08-18 |
| 015 | Implement deterministic file manifests and hashing | PASS | 2026-08-18 |
| 016 | Create the modern Python project scaffold | PASS | 2026-08-18 |
| 017 | Create the test taxonomy and minimum quality gates | PASS | 2026-08-18 |
| 018 | Create frontend migration scaffold under apps/web | PASS | 2026-08-18 |
| 019 | Create secrets, environment, and cost-control policy | PASS | 2026-08-19 |
| 020 | Create a single project control surface | PASS | 2026-08-19 |
| 021 | Design the data directory and no-raw-data Git policy | PASS | 2026-08-19 |
| 022 | Implement official ClinVar archive discovery without guessing URLs | PASS | 2026-08-19 |
| 023 | Download and verify the 2 January 2025 ClinVar archive | PASS | 2026-08-19 |
| 024 | Download and verify the 6 August 2026 ClinVar archive | PASS | 2026-08-19 |
| 025 | Build a version-aware ClinVar variant_summary parser | PASS | 2026-08-19 |
| 026 | Implement germline classification normalization | PASS | 2026-08-19 |
| 027 | Implement ClinVar review-status to star normalization | PASS | 2026-08-19 |
| 028 | Implement chromosome, coordinate, allele, and variant-type normalization | PASS | 2026-08-19 |
| 029 | Implement deterministic primary eligibility filters | PASS | 2026-08-19 |
| 030 | Implement deterministic t0-to-t1 temporal joining | PASS | 2026-08-19 |
| 031 | Select, acquire, and freeze the exact GRCh38 reference source | PASS | 2026-08-19 |
| 032 | Implement indexed local FASTA access | PASS | 2026-08-19 |
| 033 | Create exhaustive coordinate-convention tests | PASS | 2026-08-19 |
| 034 | Run reference-allele validation over candidate temporal variants | PASS | 2026-08-19 |
| 035 | Finalize duplicate-resolution policy and audit | PASS | 2026-08-19 |
| 036 | Build the primary temporal cohort from raw public archives | PASS | 2026-08-19 |
| 037 | Validate primary cohort counts and hashes against the research checkpoint | PASS | 2026-08-19 |
| 038 | Build the disjoint definitive-at-t0 calibration cohort | PASS | 2026-08-19 |
| 039 | Enforce zero normalized-ID overlap and define gene-group splits | PASS | 2026-08-19 |
| 040 | Freeze cohort outputs and data-only QC package | PASS | 2026-08-19 |
| 041 | Freeze the exact 8,192-base sequence-window convention | PASS | 2026-08-19 |
| 042 | Implement exact reference-window generation | PASS | 2026-08-19 |
| 043 | Define and test chromosome-edge behavior | PASS | 2026-08-19 |
| 044 | Implement alternate-sequence mutation with strong invariants | PASS | 2026-08-19 |
| 045 | Implement reverse-complement variant transformation correctly | PASS | 2026-08-19 |
| 046 | Create deterministic sequence cache and provenance records | PASS | 2026-08-19 |
| 047 | Define the model-agnostic scorer interface | PASS | 2026-08-19 |
| 048 | Build a deterministic fake scorer for software tests only | PASS | 2026-08-19 |
| 049 | Define official Evo 2 parity requirements before GPU integration | PASS | 2026-08-19 |
| 050 | Run end-to-end scoring orchestration with fake scorer only | PASS | 2026-08-19 |
| 051 | Re-verify current official Evo 2 installation requirements and pin a clean environment | PASS | 2026-08-19 |
| 052 | Set up Modal for the NEW project without reusing old deployment identity | PASS | 2026-08-19 |
| 053 | Build a clean Modal image for Evo 2 | PASS | 2026-08-19 |
| 054 | Create persistent model-cache storage on Modal | PASS | 2026-08-19 |
| 055 | Run the first isolated Evo 2 model-load smoke test | PENDING | |
| 056 | Run the official Evo 2 generation/inference self-test | PENDING | |
| 057 | Validate official sequence-score semantics on tiny sequences | PENDING | |
| 058 | Validate one real reference/alternate SNV pair end to end | PENDING | |
| 059 | Validate reverse-complement scoring and orientation record | PENDING | |
| 060 | Run a small registered multi-gene throughput and parity pilot | PENDING | |
| 061 | Design the full scoring record and shard format | PASS | 2026-08-19 |
| 062 | Implement deterministic sharding | PASS | 2026-08-19 |
| 063 | Implement idempotent resume and retry semantics | PASS | 2026-08-19 |
| 064 | Implement explicit failure taxonomy and observability | PASS | 2026-08-19 |
| 065 | Implement the persistent Modal scoring service | PASS | 2026-08-19 |
| 066 | Implement asynchronous/background batch submission | PASS | 2026-08-19 |
| 067 | Run a 25-variant resumability and failure-recovery pilot | WAIT | |
| 068 | Run a 100-variant performance-engineering pilot and finalize cost model | WAIT | |
| 069 | Enforce the explicit full-run approval gate | PASS | 2026-08-19 |
| 070 | Run and freeze full primary Evo 2 scoring | WAIT | |
| 071 | Create a common comparator adapter contract | PASS | 2026-08-19 |
| 072 | Integrate and validate PhyloP conservation baseline | PASS | 2026-08-19 |
| 073 | Integrate and validate CADD baseline | PASS | 2026-08-19 |
| 074 | Evaluate GPN-Star/GPN-MSA feasibility under a strict provenance gate | PASS | 2026-08-19 |
| 075 | Integrate AlphaMissense only on its valid missense subset | PASS | 2026-08-19 |
| 076 | Score the calibration cohort with frozen predictors or define a justified sampling plan | PASS | 2026-08-19 |
| 077 | Fit gene-grouped Platt calibration | PASS | 2026-08-19 |
| 078 | Run guarded isotonic calibration sensitivity | PASS | 2026-08-19 |
| 079 | Implement the full metrics and gene-clustered uncertainty engine | PASS | 2026-08-19 |
| 080 | Run the frozen primary and paired comparator analysis | PASS | 2026-08-19 |
| 081 | Analyze forward versus reverse-complement disagreement | PASS | 2026-08-19 |
| 082 | Run predeclared context-length robustness analysis | PASS | 2026-08-19 |
| 083 | Run small center-shift robustness analysis | PASS | 2026-08-19 |
| 084 | Run review-status sensitivity analyses | PASS | 2026-08-19 |
| 085 | Perform gene-held-out transport analysis | PASS | 2026-08-19 |
| 086 | Annotate and analyze consequence/coding subgroups | PASS | 2026-08-19 |
| 087 | Analyze predictor coverage and structured missingness | PASS | 2026-08-19 |
| 088 | Implement risk-coverage and abstention analysis | PASS | 2026-08-19 |
| 089 | Run structured error analysis | PASS | 2026-08-19 |
| 090 | Complete bias, validity, and limitation audits | PASS | 2026-08-19 |
| 091 | Build the research FastAPI service around validated core modules | PASS | 2026-08-19 |
| 092 | Implement asynchronous batch-job API and result registry views | PASS | 2026-08-19 |
| 093 | Redesign the Next.js application as a research workbench | PASS | 2026-08-19 |
| 094 | Implement safe single-variant research analysis UI | PASS | 2026-08-19 |
| 095 | Implement batch and benchmark dashboard | PASS | 2026-08-19 |
| 096 | Implement Methods and Provenance mode | PASS | 2026-08-19 |
| 097 | Complete security, accessibility, E2E, and failure-mode validation | PASS | 2026-08-19 |
| 098 | Perform a clean-room reproduction from a fresh clone of the NEW repository | PASS | 2026-08-19 |
| 099 | Generate paper/report figures and tables exclusively from registered outputs | PASS | 2026-08-19 |
| 100 | Execute final scientific/engineering release gate and create the new-repository release | PENDING | |

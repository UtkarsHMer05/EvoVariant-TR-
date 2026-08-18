# MILESTONE STATUS — EvoVariant-TR (100 milestones)

Ledger of milestone gate status. Updated at the end of every milestone.
Status values: `PENDING` | `IN PROGRESS` | `PASS` | `BLOCKED` | `FAILED`.

| # | Title | Status | Date |
|---|---|---|---|
| 001 | Create a genuinely new repository from the supplied source snapshot | PASS | 2026-08-18 |
| 002 | Create an immutable baseline snapshot and repository inventory | PASS | 2026-08-18 |
| 003 | Audit the legacy scientific behavior without accepting it as the new design | PASS | 2026-08-18 |
| 004 | Audit the legacy backend implementation and identify unsafe coupling | PASS | 2026-08-18 |
| 005 | Audit the legacy frontend and public-data interaction model | PENDING | |
| 006 | Reproduce the old project locally only as a baseline smoke test | PENDING | |
| 007 | Establish the new project identity and scientific naming | PENDING | |
| 008 | Define the target monorepo architecture before moving code | PENDING | |
| 009 | Write Architecture Decision Records for high-risk design choices | PENDING | |
| 010 | Commit the untouched baseline audit and freeze the migration plan | PENDING | |
| 011 | Transcribe the frozen research protocol into canonical repository files | PENDING | |
| 012 | Define protocol and configuration schemas | PENDING | |
| 013 | Implement evidence-stage types and claim guards | PENDING | |
| 014 | Design the immutable experiment registry | PENDING | |
| 015 | Implement deterministic file manifests and hashing | PENDING | |
| 016 | Create the modern Python project scaffold | PENDING | |
| 017 | Create the test taxonomy and minimum quality gates | PENDING | |
| 018 | Create frontend migration scaffold under apps/web | PENDING | |
| 019 | Create secrets, environment, and cost-control policy | PENDING | |
| 020 | Create a single project control surface | PENDING | |
| 021 | Design the data directory and no-raw-data Git policy | PENDING | |
| 022 | Implement official ClinVar archive discovery without guessing URLs | PENDING | |
| 023 | Download and verify the 2 January 2025 ClinVar archive | PENDING | |
| 024 | Download and verify the 6 August 2026 ClinVar archive | PENDING | |
| 025 | Build a version-aware ClinVar variant_summary parser | PENDING | |
| 026 | Implement germline classification normalization | PENDING | |
| 027 | Implement ClinVar review-status to star normalization | PENDING | |
| 028 | Implement chromosome, coordinate, allele, and variant-type normalization | PENDING | |
| 029 | Implement deterministic primary eligibility filters | PENDING | |
| 030 | Implement deterministic t0-to-t1 temporal joining | PENDING | |
| 031 | Select, acquire, and freeze the exact GRCh38 reference source | PENDING | |
| 032 | Implement indexed local FASTA access | PENDING | |
| 033 | Create exhaustive coordinate-convention tests | PENDING | |
| 034 | Run reference-allele validation over candidate temporal variants | PENDING | |
| 035 | Finalize duplicate-resolution policy and audit | PENDING | |
| 036 | Build the primary temporal cohort from raw public archives | PENDING | |
| 037 | Validate primary cohort counts and hashes against the research checkpoint | PENDING | |
| 038 | Build the disjoint definitive-at-t0 calibration cohort | PENDING | |
| 039 | Enforce zero normalized-ID overlap and define gene-group splits | PENDING | |
| 040 | Freeze cohort outputs and data-only QC package | PENDING | |
| 041 | Freeze the exact 8,192-base sequence-window convention | PENDING | |
| 042 | Implement exact reference-window generation | PENDING | |
| 043 | Define and test chromosome-edge behavior | PENDING | |
| 044 | Implement alternate-sequence mutation with strong invariants | PENDING | |
| 045 | Implement reverse-complement variant transformation correctly | PENDING | |
| 046 | Create deterministic sequence cache and provenance records | PENDING | |
| 047 | Define the model-agnostic scorer interface | PENDING | |
| 048 | Build a deterministic fake scorer for software tests only | PENDING | |
| 049 | Define official Evo 2 parity requirements before GPU integration | PENDING | |
| 050 | Run end-to-end scoring orchestration with fake scorer only | PENDING | |
| 051 | Re-verify current official Evo 2 installation requirements and pin a clean environment | PENDING | |
| 052 | Set up Modal for the NEW project without reusing old deployment identity | PENDING | |
| 053 | Build a clean Modal image for Evo 2 | PENDING | |
| 054 | Create persistent model-cache storage on Modal | PENDING | |
| 055 | Run the first isolated Evo 2 model-load smoke test | PENDING | |
| 056 | Run the official Evo 2 generation/inference self-test | PENDING | |
| 057 | Validate official sequence-score semantics on tiny sequences | PENDING | |
| 058 | Validate one real reference/alternate SNV pair end to end | PENDING | |
| 059 | Validate reverse-complement scoring and orientation record | PENDING | |
| 060 | Run a small registered multi-gene throughput and parity pilot | PENDING | |
| 061 | Design the full scoring record and shard format | PENDING | |
| 062 | Implement deterministic sharding | PENDING | |
| 063 | Implement idempotent resume and retry semantics | PENDING | |
| 064 | Implement explicit failure taxonomy and observability | PENDING | |
| 065 | Implement the persistent Modal scoring service | PENDING | |
| 066 | Implement asynchronous/background batch submission | PENDING | |
| 067 | Run a 25-variant resumability and failure-recovery pilot | PENDING | |
| 068 | Run a 100-variant performance-engineering pilot and finalize cost model | PENDING | |
| 069 | Enforce the explicit full-run approval gate | PENDING | |
| 070 | Run and freeze full primary Evo 2 scoring | PENDING | |
| 071 | Create a common comparator adapter contract | PENDING | |
| 072 | Integrate and validate PhyloP conservation baseline | PENDING | |
| 073 | Integrate and validate CADD baseline | PENDING | |
| 074 | Evaluate GPN-Star/GPN-MSA feasibility under a strict provenance gate | PENDING | |
| 075 | Integrate AlphaMissense only on its valid missense subset | PENDING | |
| 076 | Score the calibration cohort with frozen predictors or define a justified sampling plan | PENDING | |
| 077 | Fit gene-grouped Platt calibration | PENDING | |
| 078 | Run guarded isotonic calibration sensitivity | PENDING | |
| 079 | Implement the full metrics and gene-clustered uncertainty engine | PENDING | |
| 080 | Run the frozen primary and paired comparator analysis | PENDING | |
| 081 | Analyze forward versus reverse-complement disagreement | PENDING | |
| 082 | Run predeclared context-length robustness analysis | PENDING | |
| 083 | Run small center-shift robustness analysis | PENDING | |
| 084 | Run review-status sensitivity analyses | PENDING | |
| 085 | Perform gene-held-out transport analysis | PENDING | |
| 086 | Annotate and analyze consequence/coding subgroups | PENDING | |
| 087 | Analyze predictor coverage and structured missingness | PENDING | |
| 088 | Implement risk-coverage and abstention analysis | PENDING | |
| 089 | Run structured error analysis | PENDING | |
| 090 | Complete bias, validity, and limitation audits | PENDING | |
| 091 | Build the research FastAPI service around validated core modules | PENDING | |
| 092 | Implement asynchronous batch-job API and result registry views | PENDING | |
| 093 | Redesign the Next.js application as a research workbench | PENDING | |
| 094 | Implement safe single-variant research analysis UI | PENDING | |
| 095 | Implement batch and benchmark dashboard | PENDING | |
| 096 | Implement Methods and Provenance mode | PENDING | |
| 097 | Complete security, accessibility, E2E, and failure-mode validation | PENDING | |
| 098 | Perform a clean-room reproduction from a fresh clone of the NEW repository | PENDING | |
| 099 | Generate paper/report figures and tables exclusively from registered outputs | PENDING | |
| 100 | Execute final scientific/engineering release gate and create the new-repository release | PENDING | |

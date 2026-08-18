# TARGET ARCHITECTURE — EvoVariant-TR monorepo (Milestone 008)

Date: 2026-08-18
Status: design frozen for migration; directories created as empty skeleton.

This is the target layout (master prompt §15). It is a destination, not a reason to
do a giant rewrite in one commit — migration is incremental (see
`docs/architecture/backend_refactor_candidates.md` §3).

## 1. Directory layout

```text
EvoVariant-TR/
├── README.md                     # new-project README (rewritten at identity/migration)
├── pyproject.toml                # Python package + tooling config (M16)
├── Makefile                      # single control surface (M20)
├── .gitignore
├── .env.example                  # names only, never values (M19)
├── MIGRATION_PLAN.md             # frozen migration plan (M10)
├── apps/
│   └── web/                      # Next.js research workbench (moved at M18)
├── src/
│   └── evovariant_tr/            # core Python package (typed, CPU-testable)
│       ├── api/                  # research FastAPI service (M91-92)
│       ├── calibration/          # Platt/isotonic calibrators (M77-78)
│       ├── clinvar/              # discovery/parser/classification/review/eligibility/temporal (M22-30)
│       ├── comparators/          # CADD/PhyloP/GPN/AlphaMissense adapters (M71-75)
│       ├── evaluation/           # metrics engine (M79)
│       ├── scoring/              # scorer interface/fake/pipeline/shards/resume/failures (M47-64)
│       ├── sequence/             # window/mutate/orientation/cache (M41-46)
│       ├── statistics/           # gene-clustered bootstrap (M79)
│       ├── config.py             # validated scientific vs deployment config (M12)
│       ├── evidence.py           # evidence-stage types + claim guards (M13)
│       ├── manifest.py           # deterministic file manifests + hashing (M15)
│       ├── reference.py          # indexed local FASTA access (M32)
│       ├── registry.py           # immutable experiment registry (M14)
│       ├── variants.py           # canonical variant identity (M28)
│       └── cli.py                # CLI entrypoint (M16)
├── services/
│   └── modal/                    # ALL Modal/cloud-specific code (M51-66)
│       ├── image.py              # pinned, patch-free GPU image
│       ├── evo2_constraints.txt  # exact dependency pins
│       ├── model_service.py      # model lifecycle + scoring service
│       ├── cache_model.py        # weight warmup to dedicated volume
│       ├── batch_submit.py       # detached/sharded batch submission
│       └── ...                   # parity/pilot/robustness entrypoints
├── research/
│   ├── protocol/                 # frozen scientific specification (M11)
│   │   ├── PROTOCOL.md
│   │   ├── protocol.yaml
│   │   ├── DEVIATION_LOG.md
│   │   ├── CLASSIFICATION_MAP.csv
│   │   ├── REVIEW_STATUS_MAP.csv
│   │   └── EXCLUSION_REASONS.csv
│   ├── schemas/                  # JSON schemas for runs/results/comparators
│   ├── model/                    # Evo 2 parity spec + model config (M49)
│   └── literature/               # citations/notes
├── tests/
│   ├── unit/                     # pure logic, no network/GPU
│   ├── contract/                 # external schema contracts
│   ├── integration/              # tiny local fixtures across subsystems
│   ├── modal/                    # behind explicit marker; may cost money
│   ├── scientific/               # slow/scientific gates behind markers
│   └── e2e/                      # browser E2E (M97)
├── data/
│   ├── raw/          # gitignored — downloaded archives (ClinVar, reference)
│   ├── reference/    # gitignored — GRCh38 FASTA + index
│   ├── interim/      # gitignored — intermediate tables
│   ├── processed/    # usually gitignored — cohort/calibration parquet
│   ├── manifests/    # TRACKED — JSON manifests (source, hash, dates)
│   └── fixtures/     # TRACKED — tiny fixtures only
├── experiments/
│   └── registry/                 # append-only run records (M14)
├── artifacts/
│   ├── qc/                       # cohort/reference/leakage QC reports
│   ├── pilots/                   # engineering pilot outputs
│   ├── analysis/                 # primary + sensitivity analysis outputs
│   ├── compute/                  # Modal image/model manifests
│   ├── parity/                   # official-parity evidence
│   ├── calibration/              # fitted calibrator artifacts
│   ├── gates/                    # approval-gate documents
│   ├── runs/<RUN_ID>/            # registered run outputs
│   ├── release/                  # release manifests
│   └── baseline/                 # legacy baseline smoke-test log (M6)
├── docs/                         # bootstrap/audit/architecture/project/terminology/...
├── scripts/                      # validate_local.sh, verify_manifest.py, check_*.sh
└── paper/                        # figures/tables generated from registered outputs (M99)
```

## 2. Layering principle

Three layers with strictly one-directional dependencies:

1. **Core science** (`src/evovariant_tr/**`, excluding `api/`): pure, deterministic,
   typed. Importable and testable on macOS/CPU with **no Modal, no torch, no
   network**. This is where cohort building, windows, mutation, orientation,
   calibration, metrics, and statistics live.
2. **Adapters/transport** (`services/modal/**`, `src/evovariant_tr/api/**`): cloud
   and HTTP transport. May import the core package and Modal/FastAPI. Scientific
   orchestration stays OUT of request handlers.
3. **UI** (`apps/web`): talks to the research API only. Never imports Python, never
   talks to Modal directly for scientific scoring.

## 3. What stays out of Git

Raw ClinVar archives, GRCh38 FASTA/index, model checkpoints, Hugging Face cache,
`node_modules`, virtualenvs, build outputs, and large processed tables are all
gitignored. Only manifests, tiny fixtures, schemas, scripts, and small reports are
tracked (enforced at M21).

## 4. Migration stance

Legacy `evo2-backend/`, `evo2-frontend/`, and `evaluation/` remain in-tree as the
migration baseline until their replacements pass the relevant gates. They are moved
(e.g. frontend → `apps/web` at M18) or removed incrementally with attribution —
never in a single big-bang rewrite, and never before the replacement is validated.
